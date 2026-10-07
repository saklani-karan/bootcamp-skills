#!/usr/bin/env python3
"""Build recipe cards: recipe.json -> one self-contained HTML page of cards.

The model reads the recipe and writes each ingredient and step exactly as the
source gives it. This script does everything that must not be left to judgement:
it checks that what the model parsed out of each line still matches that line,
does all the scaling and any unit conversion, and fills the fixed page in
assets/engine.html. The page is model-free and network-free.

It REFUSES to build when:
  - the file or a card has no title, or a card has no ingredients
  - an ingredient or a step has empty text, or an id is used twice
  - an ingredient's parsed amount or unit does not match its own text
    (text "2 cups flour" with qty "3" is the model improving the recipe)
  - an amount cannot be read as a number, a fraction or a range
  - scaling is asked for on a card with no stated servings and no base count
  - unit conversion is asked for and a unit is one it does not know
  - the finished page would reach the network

    python3 build_card.py recipe.json --out cards.html [--explain]
"""
import argparse, html, json, os, re, sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
BASE_FACTORS = [F(1, 2), F(1), F(3, 2), F(2), F(3)]


class Refused(Exception):
    pass


# ---------------------------------------------------------------- numbers
GLYPH = {"½": F(1, 2), "⅓": F(1, 3), "⅔": F(2, 3), "¼": F(1, 4), "¾": F(3, 4), "⅕": F(1, 5),
         "⅛": F(1, 8), "⅜": F(3, 8), "⅝": F(5, 8), "⅞": F(7, 8), "⅙": F(1, 6), "⅚": F(5, 6)}
G = "".join(GLYPH)
NUM = rf"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?\s?[{G}]?|[{G}])"
RANGE = rf"{NUM}(?:\s*(?:–|—|-|to)\s*{NUM})?"


def parse_num(s):
    s = s.strip().replace(",", ".")
    m = re.fullmatch(rf"(\d+(?:\.\d+)?)?\s?([{G}])?", s)
    if m and (m.group(1) or m.group(2)):
        return (F(m.group(1)) if m.group(1) else F(0)) + (GLYPH[m.group(2)] if m.group(2) else 0)
    m = re.fullmatch(r"(?:(\d+)\s+)?(\d+)/(\d+)", s)
    if m and int(m.group(3)):
        return F(int(m.group(1) or 0)) + F(int(m.group(2)), int(m.group(3)))
    raise ValueError(s)


def parse_qty(s):
    """'1½' -> (3/2, None);  '2–3' -> (2, 3).  Raises ValueError if unreadable."""
    s = str(s).strip()
    parts = re.split(r"\s*(?:–|—|to|(?<=\d)-(?=\d|\s*\d))\s*", s)
    if len(parts) == 1:
        return parse_num(parts[0]), None
    if len(parts) == 2:
        return parse_num(parts[0]), parse_num(parts[1])
    raise ValueError(s)


def nice(x, metric=False):
    """A number as a cook writes it. 1.5 -> 1½, 0.333 -> ⅓; metric grams -> whole numbers."""
    x = F(x)
    if metric == "dec":
        v = round(float(x), 2)
        return f"{v:.2f}".rstrip("0").rstrip(".")
    if metric:
        v = float(x)
        if v >= 100:
            v = round(v / 5) * 5
        elif v >= 10:
            v = round(v)
        else:
            v = round(v * 2) / 2
        return (f"{v:.1f}".rstrip("0").rstrip(".")) if v != int(v) else str(int(v))
    whole = int(x)
    rest = x - whole
    best, best_d = F(0), None
    for f in [F(0), F(1, 8), F(1, 4), F(1, 3), F(3, 8), F(1, 2), F(5, 8), F(2, 3), F(3, 4), F(7, 8), F(1)]:
        d = abs(rest - f)
        if best_d is None or d < best_d:
            best, best_d = f, d
    if best == 1:
        whole, best = whole + 1, F(0)
    glyph = {v: k for k, v in GLYPH.items()}.get(best, "")
    if whole and glyph:
        return f"{whole}{glyph}"
    if glyph:
        return glyph
    return str(whole)


def fmt_range(lo, hi, metric=False):
    return nice(lo, metric) if hi is None else f"{nice(lo, metric)}–{nice(hi, metric)}"


# ---------------------------------------------------------------- units
UNITS = {  # spelling -> (key, kind, size in base unit: g or ml)
    "g": ("g", "mass", 1), "gram": ("g", "mass", 1), "grams": ("g", "mass", 1), "gr": ("g", "mass", 1),
    "kg": ("kg", "mass", 1000), "kilo": ("kg", "mass", 1000), "kilos": ("kg", "mass", 1000),
    "oz": ("oz", "mass", 28.3495), "ounce": ("oz", "mass", 28.3495), "ounces": ("oz", "mass", 28.3495),
    "lb": ("lb", "mass", 453.592), "lbs": ("lb", "mass", 453.592), "pound": ("lb", "mass", 453.592),
    "pounds": ("lb", "mass", 453.592),
    "ml": ("ml", "vol", 1), "millilitre": ("ml", "vol", 1), "milliliter": ("ml", "vol", 1),
    "millilitres": ("ml", "vol", 1), "milliliters": ("ml", "vol", 1),
    "l": ("l", "vol", 1000), "litre": ("l", "vol", 1000), "liter": ("l", "vol", 1000),
    "litres": ("l", "vol", 1000), "liters": ("l", "vol", 1000),
    "cup": ("cup", "vol", 236.588), "cups": ("cup", "vol", 236.588), "c": ("cup", "vol", 236.588),
    "fl oz": ("fl oz", "vol", 29.5735), "pint": ("pint", "vol", 473.176), "pints": ("pint", "vol", 473.176),
    "quart": ("quart", "vol", 946.353), "quarts": ("quart", "vol", 946.353),
    "tbsp": ("tbsp", "spoon", 1), "tablespoon": ("tbsp", "spoon", 1), "tablespoons": ("tbsp", "spoon", 1),
    "tbs": ("tbsp", "spoon", 1), "tsp": ("tsp", "spoon", 1), "teaspoon": ("tsp", "spoon", 1),
    "teaspoons": ("tsp", "spoon", 1),
}
# units that mean the same thing everywhere: scaled, never converted
SAME_EVERYWHERE = {"", "clove", "cloves", "can", "cans", "tin", "tins", "pinch", "pinches", "dash", "dashes",
                   "handful", "handfuls", "slice", "slices", "piece", "pieces", "bunch", "bunches", "sprig",
                   "sprigs", "stick", "sticks", "egg", "eggs", "large", "medium", "small", "packet",
                   "packets", "pack", "jar", "jars", "head", "heads", "leaf", "leaves", "drop", "drops",
                   "sheet", "sheets", "knob", "splash"}


def unit_key(u):
    return UNITS.get(u.strip().lower().rstrip("."))


def convert(lo, hi, unit, to):
    """Return (lo, hi, unit_label, metric_rounding) in the target system, or the input unchanged."""
    k = unit_key(unit)
    if not k or k[1] == "spoon":
        return lo, hi, unit, False
    key, kind, size = k
    base_lo = float(lo) * size
    base_hi = float(hi) * size if hi is not None else None
    if to == "metric" and key in ("oz", "lb", "cup", "fl oz", "pint", "quart"):
        big = base_lo >= 1000
        lab = ("kg" if big else "g") if kind == "mass" else ("l" if big else "ml")
        div = 1000 if big else 1
        return (F(base_lo / div), None if base_hi is None else F(base_hi / div), lab, "dec" if big else True)
    if to == "us" and key in ("g", "kg", "ml", "l"):
        if kind == "mass":
            lab, div = ("lb", 453.592) if base_lo >= 453.592 else ("oz", 28.3495)
        else:
            lab, div = ("cup", 236.588) if base_lo >= 59 else (("tbsp", 14.787) if base_lo >= 14.787 else ("tsp", 4.929))
        lo2 = F(base_lo / div).limit_denominator(64)
        hi2 = None if base_hi is None else F(base_hi / div).limit_denominator(64)
        if lab == "cup" and (hi2 or lo2) > 1:
            lab = "cups"
        return lo2, hi2, lab, False
    return lo, hi, unit, rounding_for(unit)


def rounding_for(unit):
    k = unit_key(unit)
    if not k:
        return False
    return True if k[0] in ("g", "ml") else ("dec" if k[0] in ("kg", "l") else False)


WORD_UNITS = {"cup": "cups", "tablespoon": "tablespoons", "teaspoon": "teaspoons", "ounce": "ounces",
              "pound": "pounds", "clove": "cloves", "can": "cans", "tin": "tins", "slice": "slices",
              "piece": "pieces", "pinch": "pinches", "stick": "sticks", "handful": "handfuls", "sprig": "sprigs",
              "litre": "litres", "liter": "liters", "gram": "grams", "kilo": "kilos", "pint": "pints",
              "quart": "quarts", "bunch": "bunches", "packet": "packets", "jar": "jars", "head": "heads"}
SINGULAR = {v: k for k, v in WORD_UNITS.items()}


def agree_unit(unit, many):
    """'cup' / 'cups' to match the amount. Abbreviations (tbsp, g, oz) never change."""
    low = unit.lower()
    if many and low in WORD_UNITS:
        return unit[:0] + WORD_UNITS[low]
    if not many and low in SINGULAR:
        return SINGULAR[low]
    return unit


def agree_item(item, many):
    """Only for a counted thing with no unit: '1 eggs' -> '1 egg', '2 egg' -> '2 eggs'.
    Changes the last word before any comma or bracket, and nothing else."""
    m = re.match(r"^([^,(]*?)([A-Za-z]+)(\s*(?:[,(].*)?)$", item)
    if not m:
        return item
    head, word, tail = m.groups()
    low = word.lower()
    if many and not low.endswith("s"):
        word = word + ("es" if low.endswith(("o", "ch", "sh", "x")) else "s")
    elif not many and low.endswith("s") and not low.endswith("ss"):
        word = word[:-2] if low.endswith(("oes", "ches", "shes", "xes")) else word[:-1]
    return head + word + tail


# ---------------------------------------------------------------- validation
def first_amount(text):
    """The amount a line of ingredient text starts with, or None."""
    m = re.match(rf"\s*(?:about\s+|approx\.?\s+|~\s*)?({RANGE})", text, re.I)
    return m.group(1) if m else None


def check_ingredient(it, where, errs):
    text = str(it.get("text", "")).strip()
    if not text:
        errs.append(f"{where}: empty ingredient text"); return
    qty, unit = str(it.get("qty", "")).strip(), str(it.get("unit", "")).strip()
    said = first_amount(text)
    if qty:
        try:
            q = parse_qty(qty)
        except ValueError:
            errs.append(f"{where}: qty {qty!r} is not a number, a fraction or a range"); return
        try:
            s = parse_qty(said) if said else None
        except ValueError:
            s = None
        if s != q:
            errs.append(f"{where}: qty {qty!r} does not match its own text {text!r} - copy the amount exactly as written")
    elif said and re.match(r"\s*\d", text):
        errs.append(f"{where}: the text starts with an amount ({said.strip()!r}) but qty is empty")
    if unit and not re.search(r"(?<![a-z])" + re.escape(unit.lower()), text.lower()):
        errs.append(f"{where}: unit {unit!r} does not appear in its own text {text!r}")


def validate(spec):
    errs, warns = [], []
    for k in ("id", "title", "cards"):
        if not spec.get(k):
            errs.append(f"missing top-level field '{k}'")
    if errs:
        raise Refused("\n".join(errs))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", str(spec["id"])):
        errs.append("id must be lowercase letters, digits and '-' (it keeps this file's ticks separate)")
    look = spec.get("look", {})
    if look.get("font", "rounded") not in FONTS:
        errs.append(f"look.font must be one of {sorted(FONTS)}")
    if look.get("bg", "auto") not in COLOURS:
        errs.append(f"look.bg must be one of {sorted(COLOURS)}")
    units = spec.get("units", "source")
    if units not in ("source", "us", "metric"):
        errs.append("units must be 'source', 'us' or 'metric'")

    seen = set()
    for ci, card in enumerate(spec["cards"]):
        cw = f"card {ci+1} ({card.get('title', '?')!r})"
        cid = card.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,60}", str(cid)):
            errs.append(f"{cw}: id must be lowercase letters, digits and '-'")
        elif cid in seen:
            errs.append(f"{cw}: duplicate card id {cid!r}")
        seen.add(cid)
        if not str(card.get("title", "")).strip():
            errs.append(f"card {ci+1}: no title")
        groups = card.get("ingredients", [])
        if not any(g.get("items") for g in groups):
            errs.append(f"{cw}: no ingredients")
        for gi, g in enumerate(groups):
            for ii, it in enumerate(g.get("items", [])):
                where = f"{cw}, ingredient {ii+1} of group {gi+1}"
                check_ingredient(it, where, errs)
                if units != "source" and str(it.get("qty", "")).strip():
                    u = str(it.get("unit", "")).strip()
                    if u.lower().rstrip(".") not in SAME_EVERYWHERE and not unit_key(u):
                        errs.append(f"{where}: cannot convert unknown unit {u!r} - leave units as 'source' or tell the person")
                if it.get("flag"):
                    warns.append(f"{cw}: flagged on the card - {it['text']!r}: {it['flag']}")
                if "[unreadable]" in str(it.get("text", "")):
                    warns.append(f"{cw}: an unreadable part is marked - {it['text']!r}")
        for si, sg in enumerate(card.get("method", [])):
            for sti, st in enumerate(sg.get("steps", [])):
                if not str(st).strip():
                    errs.append(f"{cw}: step {sti+1} of method group {si+1} is empty")
                if "[unreadable]" in str(st):
                    warns.append(f"{cw}: an unreadable part is marked in step {sti+1}")
        serves = card.get("serves")
        base = card.get("base_count")
        if card.get("scale_to") is not None:
            if not serves and not (base and base.get("n")):
                errs.append(f"{cw}: scaling asked for, but the source states no servings and no base count - "
                            "do not guess one; ask the person or leave it unscaled")
            elif float(card["scale_to"]) <= 0:
                errs.append(f"{cw}: scale_to must be more than 0")
        if serves is not None and (not isinstance(serves, (int, float)) or serves <= 0):
            errs.append(f"{cw}: serves must be a number (as the source states it) or left out")
    if errs:
        raise Refused("\n".join(errs))
    return warns


# ---------------------------------------------------------------- scaling
def line_at(it, factor, units):
    """One ingredient line at a given factor and unit system."""
    text = str(it["text"]).strip()
    qty = str(it.get("qty", "")).strip()
    if not qty:
        return {"t": text, "fixed": factor != 1}
    if factor == 1 and units == "source":
        return {"t": text}
    lo, hi = parse_qty(qty)
    lo, hi = lo * factor, (hi * factor if hi is not None else None)
    unit = str(it.get("unit", "")).strip()
    metric = bool(unit_key(unit)) and unit_key(unit)[0] in ("g", "ml")
    if units != "source":
        lo, hi, unit, metric = convert(lo, hi, unit, units)
    amount = fmt_range(lo, hi, metric)
    # singular or plural follows the amount as PRINTED: 1.06 cups prints as "1", so "1 cup"
    many = not re.fullmatch(rf"(?:0|1|0?\.\d+|[{G}])", amount)
    unit_was = unit
    unit = agree_unit(unit, many) if unit else unit
    item = str(it.get("item", "")).strip() or text
    if not unit_was:
        item = agree_item(item, many)
    out = {"t": " ".join(x for x in (amount, unit, item) if x)}
    if units != "source" and unit != str(it.get("unit", "")).strip():
        out["was"] = text
    return out


def card_data(card, units):
    serves, base = card.get("serves"), card.get("base_count")
    scalable = bool(serves) or bool(base and base.get("n"))
    n0 = serves or (base or {}).get("n")
    factors = list(BASE_FACTORS) if scalable else [F(1)]
    start = F(1)
    if scalable and card.get("scale_to") is not None:
        start = F(str(card["scale_to"])) / F(str(n0))
        if start not in factors:
            factors.append(start); factors.sort()
    what = "" if serves else " " + str((base or {}).get("what", "")).strip()
    opts = []
    for f in factors:
        lab = "×" + nice(f)
        n = F(str(n0)) * f if scalable else None
        opts.append({"label": lab, "n": (nice(n) + what) if n is not None else "", "f": float(f)})
    groups = []
    for g in card.get("ingredients", []):
        items = []
        for it in g.get("items", []):
            items.append({"v": [line_at(it, f, units) for f in factors], "flag": it.get("flag", "")})
        groups.append({"name": g.get("name", ""), "items": items})
    method = [{"name": m.get("name", ""), "steps": [str(s).strip() for s in m.get("steps", [])]}
              for m in card.get("method", [])]
    steps_have_numbers = any(re.search(r"\d", s) for m in method for s in m["steps"])
    return {
        "id": card["id"], "title": card["title"], "source": card.get("source", ""),
        "servesText": card.get("serves_text", ""), "times": card.get("times", []),
        "opts": opts, "start": factors.index(start), "groups": groups, "method": method,
        "howTo": card.get("how_to_use", ""), "notes": card.get("notes", []),
        "stepsHaveNumbers": steps_have_numbers,
    }


def render(spec):
    units = spec.get("units", "source")
    data = {"id": spec["id"], "title": spec["title"], "subtitle": spec.get("subtitle", ""),
            "look": {"font": spec.get("look", {}).get("font", "rounded"), "bg": spec.get("look", {}).get("bg", "auto")},
            "units": units, "cards": [card_data(c, units) for c in spec["cards"]]}
    page = open(ENGINE, encoding="utf-8").read()
    for slot in ("/*__RECIPES__*/null", "__TITLE__"):
        if page.count(slot) != 1:
            raise Refused(f"engine.html must contain {slot} exactly once")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("/*__RECIPES__*/null", blob).replace("__TITLE__", html.escape(spec["title"]))
    if re.search(r"fetch\(|XMLHttpRequest|<script[^>]+src=|<link[^>]+href=\"?https?:|<img[^>]+src=\"?https?:", page):
        raise Refused("the page would reach the network")
    return page, data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recipe"); ap.add_argument("--out", required=True)
    ap.add_argument("--explain", action="store_true", help="print every ingredient line at every size")
    a = ap.parse_args()
    try:
        spec = json.load(open(a.recipe, encoding="utf-8"))
        warns = validate(spec)
        page, data = render(spec)
    except Refused as e:
        print("REFUSED TO BUILD\n  " + str(e).replace("\n", "\n  "), file=sys.stderr); sys.exit(2)
    except (OSError, json.JSONDecodeError) as e:
        print(f"REFUSED TO BUILD\n  could not read {a.recipe}: {e}", file=sys.stderr); sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    for w in warns:
        print("WARN  " + w)
    if a.explain:
        for c in data["cards"]:
            print(f"\n{c['title']}  sizes: {[o['label'] for o in c['opts']]}  starts at {c['opts'][c['start']]['label']}")
            for g in c["groups"]:
                for it in g["items"]:
                    print("   " + "  |  ".join(v["t"] for v in it["v"]))
    print(f"built {os.path.basename(a.out)}  {len(data['cards'])} card(s)  units={data['units']}  {len(page)//1024} KB")


if __name__ == "__main__":
    main()
