#!/usr/bin/env python3
"""Build a trivia flashcard quiz: quiz.json -> one self-contained HTML file.

The page is model-free and network-free, so it behaves the same as a Claude
artifact, on Vercel, or double-clicked from Downloads. The one exception is
--live-photos, for a tool whose builder cannot download photos: the page then
loads each photo from its Wikipedia article when opened online, and hides it offline.

This script is where the checks live. It REFUSES to build when:
  - a question has no right answer, two right answers, or a duplicate option
  - a hint gives the answer away
  - a fact carries neither a source URL nor an explicit "check": true
  - a picture question has no picture
  - a chosen difficulty cannot fill the requested number of questions
  - a source link is dead (a 401/403/429 is a site refusing robots, not a dead link)
  - --source is given and any of the parent's questions or answers drifted by one letter

    python3 build_quiz.py quiz.json --out quiz.html [--photos DIR] [--source own.json] [--no-net] [--live-photos] [--explain]
"""
import argparse, base64, html, json, os, re, subprocess, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
LIVE = os.path.join(HERE, "..", "assets", "live-photos.js")   # --live-photos only
BOOT = "useQuiz(0);\nif(LIB.length > 1) picker(); else home();\n"
HDR_OLD = """/* Trivia flashcard engine. One file, no network, no model. The quiz lives in
   QUIZ below; photographs live in the .ph-* classes. Do not edit per quiz. */"""
HDR_LIVE = """/* Trivia flashcard engine. One file, no model. The quiz lives in QUIZ below;
   photographs live in the .ph-* classes. The only network use: photos named by
   Wikipedia article ("wiki") are fetched when online. Do not edit per quiz. */"""
UA = {"User-Agent": "QuizMakerSkill/1.0 (trivia builder; contact: the quiz owner)"}
FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
TYPES = {"mc", "tf", "pic"}
POOL = {1: (1, 2), 2: (1, 2, 3), 3: (2, 3)}        # must match pool() in engine.html


class Refused(Exception):
    pass


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


# ---------------------------------------------------------------- validation
def validate(quiz):
    errs, warns = [], []
    for k in ("id", "title", "sections", "questions"):
        if not quiz.get(k):
            errs.append(f"missing top-level field '{k}'")
    if errs:
        raise Refused("\n".join(errs))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", quiz["id"]):
        errs.append("id must be lowercase letters, digits and '-' (it keeps this quiz's scores separate)")
    look = quiz.get("look", {})
    if look.get("font", "rounded") not in FONTS:
        errs.append(f"look.font must be one of {sorted(FONTS)}")
    if look.get("bg", "auto") not in COLOURS:
        errs.append(f"look.bg must be one of {sorted(COLOURS)}")
    if quiz.get("level", 2) not in (1, 2, 3):
        errs.append("level must be 1 (easy), 2 (medium) or 3 (hard)")

    photo_keys = {p["key"] for p in quiz.get("photos", [])}
    for k in (quiz.get("cover"), look.get("photo")):
        if k and k not in photo_keys:
            errs.append(f"cover/background photo '{k}' is not in photos")

    seen, longest_right, mc_n = set(), 0, 0
    for i, c in enumerate(quiz["questions"]):
        where = f"question {i+1} ({c.get('id', '?')})"
        cid = c.get("id")
        if not cid or not re.fullmatch(r"[a-z0-9-]{1,30}", str(cid)):
            errs.append(f"{where}: id must be short lowercase letters/digits/'-'")
        elif cid in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(cid)
        t = c.get("t")
        if t not in TYPES:
            errs.append(f"{where}: t must be one of {sorted(TYPES)}"); continue
        if c.get("lvl") not in (1, 2, 3):
            errs.append(f"{where}: lvl must be 1, 2 or 3")
        if c.get("section") not in quiz["sections"]:
            errs.append(f"{where}: section '{c.get('section')}' is not one of the quiz's sections")
        if not str(c.get("q", "")).strip():
            errs.append(f"{where}: no question text")

        if t == "tf":
            if not isinstance(c.get("a"), bool):
                errs.append(f"{where}: a true/false question needs \"a\": true or false")
            right = "true" if c.get("a") else "false"
        else:
            opts = c.get("opts") or []
            if not (3 <= len(opts) <= 4):
                errs.append(f"{where}: needs 3 or 4 options, has {len(opts)}"); continue
            if len({norm(o) for o in opts}) != len(opts):
                errs.append(f"{where}: two options are the same")
            a = c.get("a")
            if not isinstance(a, int) or isinstance(a, bool) or not (0 <= a < len(opts)):
                errs.append(f"{where}: \"a\" must be the index (0-{len(opts)-1}) of the right option"); continue
            right = opts[a]
            mc_n += 1
            rival = max(len(o) for j, o in enumerate(opts) if j != a)
            if len(right) > rival + 3:
                longest_right += 1
            if len(right) > rival * 1.25 + 2:
                warns.append(f"{where}: the right answer is much the longest option ({len(right)} vs {rival} chars) - "
                             f"a child can guess it from length alone")
            for o in opts:
                if len(o) > 48:
                    warns.append(f"{where}: option is long for a child ({len(o)} chars): {o[:40]}...")
        if t == "pic":
            if not c.get("photo"):
                errs.append(f"{where}: a picture question needs \"photo\"")
        if c.get("photo") and c["photo"] not in photo_keys:
            errs.append(f"{where}: photo '{c['photo']}' is not in photos")

        h = c.get("h", "")
        if not h:
            warns.append(f"{where}: no hint")
        elif t != "tf" and len(norm(right)) >= 3 and norm(right) in norm(h):
            errs.append(f"{where}: the hint contains the answer ('{right}')")
        if not c.get("f"):
            warns.append(f"{where}: no 'Did you know?' fact")
        if not (c.get("src") or c.get("check") is True):
            errs.append(f"{where}: no source. Give \"src\" (a URL) or mark \"check\": true so it lands on the check-these list")
        if c.get("src") and not re.match(r"https?://", c["src"]):
            errs.append(f"{where}: src must be a URL")
        age = quiz.get("age", 10)
        if age <= 10 and len(c.get("q", "")) > 130:
            warns.append(f"{where}: question is long for age {age} ({len(c['q'])} chars)")

    if mc_n and longest_right / mc_n > 0.4:
        warns.append(f"the right answer is clearly the longest option in {longest_right} of {mc_n} questions - "
                     f"children learn to pick the longest one. Even out the option lengths.")

    n = quiz.get("count", 10)
    qs = quiz["questions"]
    for lvl, allowed in POOL.items():
        have = sum(1 for c in qs if c.get("lvl") in allowed)
        if have < min(n, len(qs)):
            errs.append(f"level {lvl} can draw on only {have} questions but a game asks for {n}. "
                        f"Write more at levels {allowed}, or lower count.")
    for s in quiz["sections"]:
        if not any(c.get("section") == s for c in qs):
            warns.append(f"section '{s}' has no questions")

    if errs:
        raise Refused("\n".join("  - " + e for e in errs))
    return warns


def check_source(quiz, source):
    """The parent's own questions are the answer key: every letter must survive."""
    rights = {}
    for c in quiz["questions"]:
        r = ("True" if c["a"] else "False") if c["t"] == "tf" else c["opts"][c["a"]]
        rights[c["q"]] = r
    bad = []
    for item in source:
        q, a = item["q"], item["a"]
        if q not in rights:
            bad.append(f"question changed or missing: {q!r}")
        elif rights[q] != a:
            bad.append(f"answer changed for {q!r}: list says {a!r}, quiz says {rights[q]!r}")
    if bad:
        raise Refused("the quiz no longer matches the parent's list:\n" + "\n".join("  - " + b for b in bad))


# ---------------------------------------------------------------- links
def check_links(urls, explain=False):
    dead, blocked = [], []
    for u in sorted(urls):
        try:
            req = urllib.request.Request(u, headers=UA, method="GET")
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            code = 0
        if 200 <= code < 400:
            state = "ok"
        elif code in (401, 403, 405, 406, 429):
            state = "blocked"; blocked.append(u)
        else:
            state = "DEAD"; dead.append(f"{code or 'no response'}  {u}")
        if explain:
            print(f"  {code or '---':>3}  {state:<7}  {u}", file=sys.stderr)
        time.sleep(0.3)
    if dead:
        raise Refused("these sources do not resolve:\n" + "\n".join("  - " + d for d in dead))
    return blocked


# ---------------------------------------------------------------- photographs
# Same guards as the trip-planner skill's fetcher: prefer a Wikipedia article's
# lead image, and filter Commons search with must/ban lists - a bare search once
# returned a photograph of a grave in another country.
def _get(url, timeout=30, tries=4):
    last = None
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            time.sleep((6, 12, 20, 30)[min(n, 3)] if e.code == 429 else 2 * (n + 1))
        except Exception as e:
            last = e
            time.sleep(2 * (n + 1))
    raise last


def _api(host, params):
    return json.loads(_get(f"https://{host}/w/api.php?" + urllib.parse.urlencode(params), timeout=25))


def _licence(fname):
    try:
        d = _api("commons.wikimedia.org", {"action": "query", "titles": "File:" + fname,
                                           "prop": "imageinfo", "iiprop": "extmetadata", "format": "json"})
        em = list(d["query"]["pages"].values())[0]["imageinfo"][0]["extmetadata"]
        who = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()[:70]
        return who or "unknown", em.get("LicenseShortName", {}).get("value", "").strip()
    except Exception:
        return "unknown", ""


def fetch_photo(spec, outdir, explain=False):
    key = spec["key"]
    must = [m.lower() for m in spec.get("must", [])]
    ban = [b.lower() for b in spec.get("ban", [])] + ["grab ", "friedhof", "cemetery", "grave", "plaque"]
    if spec.get("wiki"):
        try:
            d = _api("en.wikipedia.org", {"action": "query", "titles": spec["wiki"], "prop": "pageimages",
                                          "piprop": "thumbnail|name", "pithumbsize": 1100, "format": "json",
                                          "redirects": 1})
            pg = list(d["query"]["pages"].values())[0]
            thumb, fname = pg.get("thumbnail", {}).get("source"), pg.get("pageimage")
            if thumb and fname:
                blob = _get(thumb)
                if len(blob) > 12000:
                    path = os.path.join(outdir, f"raw-{key}")
                    open(path, "wb").write(blob)
                    a, l = _licence(fname)
                    if explain:
                        print(f"  photo {key:12} <- wiki:{spec['wiki']} ({l})", file=sys.stderr)
                    return path, a, l
        except Exception as e:
            if explain:
                print(f"  photo {key:12} wiki lookup failed: {type(e).__name__}: {e}", file=sys.stderr)
    for q in ([spec["search"]] if isinstance(spec.get("search"), str) else spec.get("search", [])):
        try:
            d = _api("commons.wikimedia.org", {"action": "query", "generator": "search", "gsrsearch": q,
                                               "gsrnamespace": 6, "gsrlimit": 12, "prop": "imageinfo",
                                               "iiprop": "url|extmetadata", "iiurlwidth": 1100, "format": "json"})
            for pg in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
                t = pg["title"]; tl = t.lower()
                ii = pg.get("imageinfo", [{}])[0]
                if not ii.get("thumburl") or not re.search(r"\.(jpg|jpeg|png)$", t, re.I):
                    continue
                if any(b in tl for b in ban) or (must and not any(m in tl for m in must)):
                    continue
                blob = _get(ii["thumburl"])
                if len(blob) < 12000:
                    continue
                path = os.path.join(outdir, f"raw-{key}")
                open(path, "wb").write(blob)
                em = ii.get("extmetadata", {})
                a = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()[:70] or "unknown"
                if explain:
                    print(f"  photo {key:12} <- {t[:52]}", file=sys.stderr)
                return path, a, em.get("LicenseShortName", {}).get("value", "").strip()
        except Exception as e:
            if explain:
                print(f"  photo {key:12} search {q!r} failed: {type(e).__name__}: {e}", file=sys.stderr)
    return None


def shrink(src, dst, width, quality):
    """sips on a Mac; Pillow elsewhere (the claude.ai sandbox has it); else keep the original."""
    try:
        r = subprocess.run(["sips", "-Z", str(width), "-s", "format", "jpeg", "-s", "formatOptions",
                            str(quality), src, "--out", dst], capture_output=True)
        if r.returncode == 0 and os.path.exists(dst):
            return True
    except FileNotFoundError:
        pass
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB")
        im.thumbnail((width, width))
        im.save(dst, "JPEG", quality=quality)
        return True
    except Exception:
        return False


def load_photos(quiz, photo_dir, no_net, explain, live=False):
    """Returns css, credits{key: text}, labels{key: label}, wiki{key: article}. Local files
    win over fetching. With live, nothing is fetched: a photo with a "wiki" article is left
    for the page to load from Wikipedia when it is opened online."""
    manifest = {}
    if photo_dir and os.path.exists(os.path.join(photo_dir, "manifest.json")):
        manifest = json.load(open(os.path.join(photo_dir, "manifest.json"), encoding="utf-8"))
    css, credits, labels, wiki = [], {}, {}, {}
    with tempfile.TemporaryDirectory() as td:
        fetched = 0
        for spec in quiz.get("photos", []):
            key = spec["key"]
            labels[key] = spec.get("label", key)
            src, author, lic = None, spec.get("author"), spec.get("license")
            for name in (spec.get("file"), f"sm-{key}.jpg", f"{key}.jpg"):
                if name and photo_dir and os.path.exists(os.path.join(photo_dir, name)):
                    src = os.path.join(photo_dir, name)
                    m = manifest.get(key, {})
                    author, lic = author or m.get("author"), lic or m.get("license")
                    break
            if not src and live:
                if spec.get("wiki"):
                    wiki[key] = spec["wiki"]
                continue
            if not src and not no_net:
                if fetched:
                    time.sleep(1.2)      # Wikimedia rate-limits bursts with a 429
                got = fetch_photo(spec, td, explain)
                fetched += 1
                if got:
                    raw, author, lic = got
                    # keep what was fetched, so a rebuild reuses it instead of re-downloading
                    keep = photo_dir if photo_dir and os.path.isdir(photo_dir) else td
                    src = os.path.join(keep, f"sm-{key}.jpg")
                    if not shrink(raw, src, 760, 62):
                        src = raw
                    if keep == photo_dir:
                        manifest[key] = {"author": author, "license": lic, "label": spec.get("label", key)}
                        json.dump(manifest, open(os.path.join(photo_dir, "manifest.json"), "w", encoding="utf-8"),
                                  ensure_ascii=False, indent=1)
            if not src:
                continue
            b = open(src, "rb").read()
            css.append(f'.ph-{key}{{background-image:url("data:image/jpeg;base64,{base64.b64encode(b).decode()}")}}')
            credits[key] = f"{author or 'unknown'}, {lic or 'licence unknown'} · Wikimedia Commons"
    return "\n".join(css), credits, labels, wiki


# ---------------------------------------------------------------- build
PH_RULE = re.compile(r'\.ph-([A-Za-z0-9_-]+)\{background-image:url\("data:image/[^"]+"\)\}')


def read_existing(path):
    """Pull the quizzes and their photos back out of a page this skill built,
    so the newest file can carry every earlier quiz without their quiz.json."""
    src = open(path, encoding="utf-8").read()
    m = re.search(r"^var QUIZZES = (\[.*\]);$", src, re.M)
    if m:
        quizzes = json.loads(m.group(1).replace("<\\/", "</"))
    else:
        m = re.search(r"^var QUIZ = (\{.*\});$", src, re.M)
        if not m:
            raise Refused(f"  {os.path.basename(path)} holds no quiz this skill recognises")
        quizzes = [json.loads(m.group(1).replace("<\\/", "</"))]
    css = {k: mm.group(0) for mm in PH_RULE.finditer(src) for k in [mm.group(1)]}
    for q in quizzes:
        if not q.get("id") or not q.get("questions"):
            raise Refused(f"  a quiz in {os.path.basename(path)} has no id or no questions")
    return quizzes, css


def prepare(path, a):
    """Everything that is true of ONE quiz. Raises Refused; never writes."""
    quiz = json.load(open(path, encoding="utf-8"))
    warns = validate(quiz)
    if a.source:
        check_source(quiz, json.load(open(a.source, encoding="utf-8")))
    links = sorted({c["src"] for c in quiz["questions"] if c.get("src")})
    blocked = [] if a.no_net else check_links(links, a.explain)

    css, credits, labels, wiki = load_photos(quiz, a.photos, a.no_net, a.explain, a.live_photos)
    have = set(credits) | set(wiki)
    need_q = {c["photo"] for c in quiz["questions"] if c["t"] == "pic"}
    live_pic = sorted(c["id"] for c in quiz["questions"] if c["t"] == "pic" and c.get("photo") in wiki)
    if live_pic:
        # offline a live photo is hidden, and a picture question without its picture can't be answered
        raise Refused("  picture questions can't use a live photo - offline it is hidden and the card "
                      "can't be answered: " + ", ".join(live_pic) +
                      "\n  make them ordinary questions with the photo on the answer side")
    if need_q - have:
        raise Refused("  picture questions have no picture: " + ", ".join(sorted(need_q - have))
                      + ("\n  with --live-photos every photo needs a \"wiki\" article title" if a.live_photos else ""))

    data = {k: v for k, v in quiz.items() if k not in ("photos",)}
    for c in data["questions"]:
        c.pop("src", None)                     # sources stay in the build, not on the child's card
    data["photoKeys"] = [p["key"] for p in quiz.get("photos", []) if p["key"] in have]
    data["credits"], data["labels"] = credits, labels
    if wiki:
        data["wiki"] = wiki

    return {"quiz": quiz, "data": data, "css": css, "warns": warns, "links": links,
            "blocked": blocked, "have": have, "path": path,
            "unused": have - {c.get("photo") for c in quiz["questions"]} - {quiz.get("cover")},
            "missing_back": {c["photo"] for c in quiz["questions"] if c.get("photo")} - have}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz", nargs="+", help="one quiz.json, or several to put in ONE file with an index")
    ap.add_argument("--out", default="quiz.html")
    ap.add_argument("--title", help="title for a file holding several quizzes (default: 'All quizzes')")
    ap.add_argument("--photos", help="photo folder (sm-<key>.jpg + manifest.json): read first, and fetched photos are saved here")
    ap.add_argument("--source", help="the parent's own questions as JSON [{q, a}] - checked letter by letter")
    ap.add_argument("--from-existing", dest="existing", metavar="OLD.html",
                    help="carry every quiz already in a page this skill built, so you need only the new quiz.json")
    ap.add_argument("--no-net", action="store_true", help="skip link checks and photo fetching")
    ap.add_argument("--live-photos", dest="live_photos", action="store_true",
                    help="for a tool whose builder cannot download (e.g. Copilot Cowork): store no photos; "
                         "the page loads each photo's Wikipedia article image when opened online")
    ap.add_argument("--explain", action="store_true")
    a = ap.parse_args()

    if a.source and len(a.quiz) > 1:
        print("--source checks one quiz against one list; build that quiz on its own first.", file=sys.stderr)
        sys.exit(2)

    carried, carried_css = [], {}
    if a.existing:
        try:
            carried, carried_css = read_existing(a.existing)
        except Refused as e:
            print("REFUSED TO BUILD\n" + str(e), file=sys.stderr); sys.exit(2)
        except Exception as e:
            print(f"REFUSED TO BUILD\n  could not read {a.existing}: {e}", file=sys.stderr); sys.exit(2)

    built = []
    for path in a.quiz:
        try:
            built.append(prepare(path, a))
        except Refused as e:
            print(f"REFUSED TO BUILD ({os.path.basename(path)})\n" + str(e), file=sys.stderr)
            print("\nFix the quiz, not the check. --explain shows more.", file=sys.stderr)
            sys.exit(2)

    ids = [b["data"]["id"] for b in built]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print("REFUSED TO BUILD\n  two quizzes share an id, so they would share scores: " +
              ", ".join(dup), file=sys.stderr)
        sys.exit(2)

    # a rebuilt quiz replaces its older self; everything else is carried forward
    fresh = set(ids)
    replaced = [q["title"] for q in carried if q["id"] in fresh]
    carried = [q for q in carried if q["id"] not in fresh]

    # photo keys are global to the file; the same key twice would show one quiz another's picture
    owner, css_parts = {}, []
    for b in built:
        for k in b["have"]:
            if k in owner and owner[k] != b["path"]:
                print(f"REFUSED TO BUILD\n  photo key {k!r} is used by both "
                      f"{os.path.basename(owner[k])} and {os.path.basename(b['path'])} - "
                      f"rename one, or they share a picture", file=sys.stderr)
                sys.exit(2)
            owner[k] = b["path"]
        css_parts.append(b["css"])

    # carried photos only for keys the new build does not already define
    keep_css = [r for k, r in carried_css.items() if k not in owner]
    datas = carried + [b["data"] for b in built]

    engine = open(ENGINE, encoding="utf-8").read()
    title = a.title or (datas[0]["title"] if len(datas) == 1 else "All quizzes")
    page = engine.replace("__TITLE__", html.escape(title)).replace(
        "/*__PHOTO_CSS__*/", "\n".join(keep_css + css_parts))
    if len(datas) == 1:
        page = page.replace("/*__QUIZ__*/null",
                            json.dumps(datas[0], ensure_ascii=False).replace("</", "<\\/"))
    else:
        page = page.replace("/*__QUIZZES__*/null",
                            json.dumps(datas, ensure_ascii=False).replace("</", "<\\/"))
    live_js = ""
    if any(q.get("wiki") for q in datas):
        # the one sanctioned network use: photos named by Wikipedia article, loaded when online
        live_js = open(LIVE, encoding="utf-8").read()
        if page.count(BOOT) != 1:
            print("REFUSED TO BUILD\n  engine.html boot lines not found exactly once - update build_quiz.py",
                  file=sys.stderr)
            sys.exit(2)
        page = page.replace(BOOT, live_js + BOOT + "livePhotos();\n").replace(HDR_OLD, HDR_LIVE)
    if re.search(r"\bfetch\(|XMLHttpRequest|https?://[^\s\"')]+\.(js|css)\b", page.replace(live_js, "") if live_js else page):
        print("REFUSED TO BUILD\n  the page would reach the network", file=sys.stderr)
        sys.exit(2)
    open(a.out, "w", encoding="utf-8").write(page)

    total_q = sum(len(q["questions"]) for q in datas)
    print(f"built {a.out}  {os.path.getsize(a.out)/1048576:.2f} MB  "
          f"{len(datas)} quiz{'' if len(datas)==1 else 'zes'}  {total_q} questions  "
          f"{len(owner) + len(keep_css)} photos"
          + ("  (index shown first)" if len(datas) > 1 else ""))
    n_live = sum(len(q.get("wiki") or {}) for q in datas)
    if n_live:
        print(f"  {n_live} photos are not stored: the page loads them from Wikipedia when opened "
              f"online, and hides them offline")
    if carried:
        print(f"  carried from {os.path.basename(a.existing)}: " +
              ", ".join(q["title"] for q in carried))
    if replaced:
        print(f"  replaced with the newly built version: " + ", ".join(replaced))

    for b in built:
        qs = b["quiz"]["questions"]
        by = {l: sum(1 for c in qs if c["lvl"] == l) for l in (1, 2, 3)}
        if len(datas) > 1:
            print(f"  {b['quiz']['title']}: {len(qs)} questions "
                  f"(easy {by[1]} · medium {by[2]} · hard {by[3]}), {len(b['have'])} photos, "
                  + (f"{len(b['links'])} sources NOT checked" if a.no_net else f"{len(b['links'])} sources checked"))
        else:
            print(f"  {len(qs)} questions (easy {by[1]} · medium {by[2]} · hard {by[3]})  "
                  + (f"{len(b['links'])} sources NOT checked (--no-net)" if a.no_net
                     else f"{len(b['links'])} sources checked"))
        for w in b["warns"]:
            print("  WARN " + w, file=sys.stderr)
        if b["missing_back"]:
            print("  WARN no photo found for " + ", ".join(sorted(b["missing_back"])) +
                  " - those answers show without one", file=sys.stderr)
        if b["unused"]:
            print("  note: photos only offered as backgrounds: " + ", ".join(sorted(b["unused"])), file=sys.stderr)
        if b["blocked"]:
            print(f"  {len(b['blocked'])} source(s) refused a robot - open them in a browser to be sure:", file=sys.stderr)
            for u in b["blocked"]:
                print("    " + u, file=sys.stderr)

    checks = [(b, c) for b in built for c in b["quiz"]["questions"] if c.get("check")]
    if checks:
        print("\nCHECK THESE before a child sees them:")
        for b, c in checks:
            where = (b["quiz"]["title"] + " — ") if len(datas) > 1 else ""
            print("  " + where + c["q"] + "  →  " + str(c.get("note") or c["opts"][c["a"]]))


if __name__ == "__main__":
    main()
