#!/usr/bin/env python3
"""Build a self-contained trip page from a trip.json.

Renders the page, fetches a real photograph for every named place from Wikimedia
Commons, embeds every image as a data URI, checks that every link resolves, and
refuses to build on unsourced prices or dead links.

--no-net, for a builder with no internet: nothing is fetched and no link is
checked, and the page says so in place of "checked". --live-photos (which implies
--no-net) adds the one sanctioned network use to the page: each photo named by a
Wikipedia article is loaded when the page is opened online, and hidden offline.

    python3 build_page.py trip.json --out trip-brief.html [--explain] [--no-net] [--live-photos]
"""
import argparse, base64, html, io, json, os, re, subprocess, sys, tempfile, time
import urllib.parse, urllib.request

UA = {"User-Agent": "TripPlannerSkill/1.0 (itinerary builder; contact: the trip owner)"}
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
LIVE = os.path.join(ASSETS, "live-photos.js")      # --live-photos only; same file as gemini-gem/live-photos.js
# The trip Gem's wording, so the two versions of this page say the same thing.
PHOTO_LINE = ("Photographs come from Wikipedia and Wikimedia Commons, under their stated licences, "
              "and load only when this page is opened with internet. ")
NOT_CHECKED = ("The links on this page were not machine-checked when it was built, so open its source "
               "links and confirm everything marked with the check dot before you book.")
# ---------------------------------------------------------------- network guard
# The page must not reach the network when opened, except: Google Fonts (degrades to
# system fonts offline) and, with --live-photos, the one live-photo script block.
# Raw-HTML fields (*_html) go into the page as written, so the guard reads the FINISHED
# page with an HTML parser (which decodes entities the way a browser does) and allows
# only the tags and attributes this builder itself writes, plus plain inline formatting.
ALLOWED_TAGS = {
    # what build_page.py writes
    "title", "link", "style", "script", "nav", "div", "header", "p", "h1", "h2", "h3", "dl", "dt", "dd",
    "span", "small", "section", "ol", "ul", "li", "a", "article", "table", "thead", "tbody", "tr", "th",
    "td", "label", "input", "button", "svg", "g", "rect", "text", "line", "b", "strong", "em",
    # inline formatting a *_html field may reasonably use
    "i", "br", "sup", "sub", "code", "abbr", "mark", "s", "u", "q", "wbr",
}
ALLOWED_ATTRS = {
    "class", "id", "role", "aria-label", "aria-hidden", "aria-current", "title", "lang", "dir", "style",
    "href", "rel", "crossorigin", "target", "type", "for",
    "viewbox", "font-size", "font-family", "font-weight", "text-anchor", "fill", "fill-opacity",
    "stroke", "stroke-width", "stroke-dasharray", "x", "y", "x1", "x2", "y1", "y2", "rx", "width", "height",
}
FONT_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
_WS = re.compile(r"[\x00-\x20\x7f]+")


def _css_plain(css):
    """CSS as a browser reads it: escapes decoded, comments and whitespace dropped, lower case."""
    css = re.sub(r"\\([0-9a-fA-F]{1,6})[ \t\r\n\f]?", lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) < 0x110000 else "", css)
    css = re.sub(r"\\(.)", r"\1", css)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return _WS.sub("", css).lower()


def _css_problem(css):
    c = _css_plain(css)
    for bad in ("@import", "image-set(", "image(", "cross-fade(", "element(", "src(", "expression("):
        if bad in c:
            return f"CSS uses {bad}"
    for m in re.finditer(r"url\(", c):
        target = c[m.end():m.end() + 8].lstrip("'\"")
        if not target.startswith("data:"):
            return "CSS url() points outside the page: url(" + c[m.end():m.end() + 40]
    return None


def network_problem(page):
    """None if the page stays offline (fonts aside), else the reason in words."""
    from html.parser import HTMLParser
    found = []
    scripts = []

    class G(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.raw = None

        def handle_starttag(self, tag, attrs):
            self.check(tag, attrs)
            if tag in ("script", "style"):
                self.raw = [tag, ""]

        def handle_startendtag(self, tag, attrs):
            self.check(tag, attrs)

        def handle_data(self, data):
            if self.raw:
                self.raw[1] += data

        def handle_endtag(self, tag):
            if self.raw and tag == self.raw[0]:
                kind, body = self.raw
                self.raw = None
                if kind == "script":
                    scripts.append(body)
                elif _css_problem(body):
                    found.append("<style>: " + _css_problem(body))

        def check(self, tag, attrs):
            if found:
                return
            if tag not in ALLOWED_TAGS:
                found.append(f"<{tag}> is not a tag this page may contain"); return
            a = {}
            for k, v in attrs:
                v = v or ""
                if k not in ALLOWED_ATTRS:
                    found.append(f'attribute "{k}" on <{tag}> is not allowed'); return
                a[k] = v
                flat = _WS.sub("", v).lower()
                if k == "style" and _css_problem(v):
                    found.append(f"style on <{tag}>: " + _css_problem(v)); return
                if "url(" in _css_plain(v) and k != "style":
                    found.append(f'attribute "{k}" on <{tag}> holds a url()'); return
                if k == "href" and tag not in ("a", "link"):
                    found.append(f"href on <{tag}> (only links may have one)"); return
                if k == "href" and re.match(r"(javascript|vbscript):", flat):
                    found.append(f"<{tag}> href runs script"); return
            if tag == "link":
                host = urllib.parse.urlsplit(_WS.sub("", a.get("href", ""))).hostname or ""
                rel = a.get("rel", "").lower().split()
                if not rel or set(rel) - {"preconnect", "stylesheet"} or host not in FONT_HOSTS \
                        or not _WS.sub("", a.get("href", "")).lower().startswith("https://"):
                    found.append(f'<link rel="{a.get("rel","")}" href="{a.get("href","")[:60]}"> - '
                                 f'a <link> may only reach Google Fonts'); return
            if tag == "input" and a.get("type", "").lower() != "checkbox":
                found.append(f'<input type="{a.get("type","")}"> (only checkboxes)'); return

    g = G()
    g.feed(page)
    g.close()
    if found:
        return found[0]
    if scripts != [SCRIPT]:
        return (f"the page holds {len(scripts)} script blocks; only the builder's own may run "
                f"(and, with --live-photos, the live-photo block)")
    return None


E = lambda s: html.escape(str(s), quote=True)


# Section ids whose data lives under a different key.
DATA_KEY = {"week": "days", "before": "deadlines"}


# ---------------------------------------------------------------- validation
class Refused(Exception):
    pass


def validate(trip, explain=False):
    """Every money figure needs a source or an explicit check mark."""
    problems = []

    def money_rows():
        for p in trip.get("places", []):
            yield f"places/{p.get('name','?')}", p.get("price")
        for h in trip.get("hotels", []):
            yield f"hotels/{h.get('name','?')}", h.get("rate")
        for f in trip.get("flights", []):
            yield f"flights/{f.get('tag','?')}", f.get("fare")

    for where, cell in money_rows():
        if cell is None:
            continue
        if not isinstance(cell, dict):
            problems.append(f"{where}: price must be an object with 'text', not a bare value")
            continue
        if not cell.get("source") and not cell.get("check"):
            problems.append(f"{where}: price {cell.get('text','?')!r} has no source and is not marked check:true")

    for d in trip.get("weather", []):
        if d.get("derived") and not d.get("check"):
            problems.append(f"weather/{d.get('day','?')}: derived figure must also be check:true")

    for key in ("page_title", "eyebrow", "title_html", "subtitle", "asof", "footer",
                "facts", "sections", "toc_groups", "days", "weather"):
        if not trip.get(key):
            problems.append(f"missing required field: {key}")

    known = set(RENDER)
    for s in trip.get("sections", []):
        if s.get("id") not in known:
            problems.append(f"sections/{s.get('id','?')}: no renderer for that section id")
        if s.get("group") not in {g[0] for g in trip.get("toc_groups", [])}:
            problems.append(f"sections/{s.get('id','?')}: group {s.get('group')!r} is not in toc_groups")
        data_key = DATA_KEY.get(s.get("id"), s.get("id"))
        if not trip.get(data_key):
            problems.append(f"sections/{s.get('id','?')}: listed in sections but '{data_key}' holds no data")

    if problems:
        raise Refused("\n".join("  - " + p for p in problems))
    if explain:
        print("validation: every price carries a source or a check mark", file=sys.stderr)


# ---------------------------------------------------------------- links
def collect_links(node, found=None):
    """Walk every string in the spec. Do NOT regex over json.dumps - the quotes
    come back backslash-escaped there and href="..." silently never matches."""
    if found is None:
        found = set()
    if isinstance(node, str):
        for u in re.findall(r'href=["\'](https?://[^"\']+)["\']', node):
            found.add(html.unescape(u))
        if re.fullmatch(r'https?://\S+', node.strip()):
            found.add(html.unescape(node.strip()))
    elif isinstance(node, dict):
        for v in node.values():
            collect_links(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_links(v, found)
    return found


def check_links(urls, explain=False):
    """A 403 is a site refusing a robot, not a broken link. Only treat a link as
    dead when the server actually says it is missing, or says nothing at all."""
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
    if dead:
        raise Refused("these links do not resolve:\n" + "\n".join("  - " + d for d in dead))
    return blocked


# ---------------------------------------------------------------- photographs
def _get(url, timeout=30, tries=4):
    """Wikimedia rate-limits bursts with a 429. A bare try/except here silently
    loses photographs, so wait it out properly - a 429 needs seconds, not
    milliseconds - and only then give up."""
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
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(params)
    return json.loads(_get(url, timeout=25))


def _licence(fname):
    try:
        d = _api("commons.wikimedia.org", {"action": "query", "titles": "File:" + fname,
                                           "prop": "imageinfo", "iiprop": "extmetadata", "format": "json"})
        em = list(d["query"]["pages"].values())[0]["imageinfo"][0]["extmetadata"]
        who = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()[:70]
        lic = em.get("LicenseShortName", {}).get("value", "").strip()
        return who or "unknown", lic
    except Exception:
        return "unknown", ""


def fetch_photo(spec, outdir, explain=False):
    """spec: {key, wiki?, search?, must?, ban?}. Returns (path, author, licence) or None.

    The relevance guard matters: a bare Commons search for a hotel name once
    returned a photograph of a grave in a different country.
    """
    key = spec["key"]
    must = [m.lower() for m in spec.get("must", [])]
    ban = [b.lower() for b in spec.get("ban", [])] + ["grab ", "friedhof", "cemetery", "gedenktafel", "plaque"]

    # 1. the Wikipedia article's own lead image - far more reliable than search
    if spec.get("wiki"):
        try:
            d = _api("en.wikipedia.org", {"action": "query", "titles": spec["wiki"], "prop": "pageimages",
                                          "piprop": "thumbnail|name", "pithumbsize": 1100,
                                          "format": "json", "redirects": 1})
            pg = list(d["query"]["pages"].values())[0]
            thumb, fname = pg.get("thumbnail", {}).get("source"), pg.get("pageimage")
            if thumb and fname:
                blob = _get(thumb)
                if len(blob) > 12000:
                    path = os.path.join(outdir, f"raw-{key}")
                    open(path, "wb").write(blob)
                    a, l = _licence(fname)
                    if explain:
                        print(f"  photo {key:14} <- wiki:{spec['wiki']}  ({l})", file=sys.stderr)
                    return path, a, l
        except Exception as e:
            if explain:
                print(f"  photo {key:14} wiki lookup failed: {type(e).__name__}: {e}", file=sys.stderr)

    # 2. Commons search, guarded
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
                if any(b in tl for b in ban):
                    continue
                if must and not any(m in tl for m in must):
                    continue
                blob = _get(ii["thumburl"])
                if len(blob) < 12000:
                    continue
                path = os.path.join(outdir, f"raw-{key}")
                open(path, "wb").write(blob)
                em = ii.get("extmetadata", {})
                a = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()[:70] or "unknown"
                l = em.get("LicenseShortName", {}).get("value", "").strip()
                if explain:
                    print(f"  photo {key:14} <- {t[:52]}  ({l})", file=sys.stderr)
                return path, a, l
        except Exception as e:
            if explain:
                print(f"  photo {key:14} search {q!r} failed: {type(e).__name__}: {e}", file=sys.stderr)
            continue
    # 3. Openverse - a different provider entirely (Flickr, museums, Commons),
    #    so a Wikimedia rate limit or a Wikimedia coverage gap does not sink us.
    got = _openverse(spec, outdir, explain)
    if got:
        return got

    if explain:
        print(f"  photo {key:14} -- NONE FOUND", file=sys.stderr)
    return None


# Commercial use AND modification must both be allowed: this builder resizes every
# image, and the pages get used in a commercial setting. NC and ND are excluded on
# purpose - Openverse returns plenty of both by default.
SAFE_LICENCES = "cc0,pdm,by,by-sa"


def _openverse(spec, outdir, explain=False):
    key = spec["key"]
    must = [m.lower() for m in spec.get("must", [])]
    ban = [b.lower() for b in spec.get("ban", [])] + ["cemetery", "grave", "plaque"]
    queries = [spec["search"]] if isinstance(spec.get("search"), str) else list(spec.get("search", []))
    queries.append(spec.get("label") or spec.get("wiki") or key)

    for q in queries:
        url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
            {"q": q, "license": SAFE_LICENCES, "page_size": 8})
        try:
            data = json.loads(_get(url, timeout=20, tries=2))
        except Exception as e:
            if explain:
                print(f"  photo {key:14} openverse {q!r} failed: {type(e).__name__}", file=sys.stderr)
            continue
        for r in data.get("results", []):
            title = (r.get("title") or "").lower()
            if any(b in title for b in ban):
                continue
            if must and not any(m in title for m in must):
                continue
            src = r.get("url")
            if not src:
                continue
            try:
                blob = _get(src, timeout=25, tries=2)
            except Exception:
                continue
            if len(blob) < 12000:
                continue
            path = os.path.join(outdir, f"raw-{key}")
            open(path, "wb").write(blob)
            lic = f"{r.get('license','?').upper()} {r.get('license_version','')}".strip()
            who = r.get("creator") or "unknown"
            if explain:
                print(f"  photo {key:14} <- openverse/{r.get('source')}: {str(r.get('title'))[:38]}  ({lic})",
                      file=sys.stderr)
            return path, who, lic
    return None


def shrink(src, dst, width, quality):
    r = subprocess.run(["sips", "-Z", str(width), "-s", "format", "jpeg",
                        "-s", "formatOptions", str(quality), src, "--out", dst],
                       capture_output=True)
    return r.returncode == 0 and os.path.exists(dst)


def build_photo_css(trip, explain=False, no_net=False):
    css, credits = [], []
    if no_net:
        return "", []
    with tempfile.TemporaryDirectory() as td:
        for i, spec in enumerate(trip.get("photos", [])):
            if i:
                time.sleep(1.2)          # be a polite client, not a burst
            got = fetch_photo(spec, td, explain)
            if not got:
                continue
            raw, author, lic = got
            small = os.path.join(td, f"sm-{spec['key']}.jpg")
            w, q = (1100, 64) if spec.get("hero") else (620, 58)
            if not shrink(raw, small, w, q):
                small = raw
            b = open(small, "rb").read()
            css.append(f'.ph-{spec["key"]}{{background-image:url("data:image/jpeg;base64,{base64.b64encode(b).decode()}")}}')
            credits.append(f'{E(spec.get("label", spec["key"]))} &mdash; {E(author)}, {E(lic)}')
    return "\n".join(css), credits


# ---------------------------------------------------------------- rendering
def money(cell):
    if not cell:
        return ""
    t = E(cell.get("text", ""))
    if cell.get("source"):
        t = f'<a href="{E(cell["source"])}">{t}</a>'
    if cell.get("check"):
        t += ' <span class="dot check"></span>'
    return t


def sec(sid, title, tag, note, body):
    n = f'<p class="sec-note">{note}</p>' if note else ""
    return (f'<section id="{sid}">\n<div class="sec-head"><h2>{E(title)}</h2>'
            f'<span class="sec-tag">{E(tag)}</span></div>\n{n}\n{body}\n</section>\n')


def r_masthead(t, checked=True):
    facts = "".join(
        f'<div class="fact"><dt>{E(f["label"])}</dt><dd>{E(f["value"])}'
        f'<small>{E(f.get("note",""))}</small></dd></div>' for f in t["facts"])
    hero = ""
    h = next((p for p in t.get("photos", []) if p.get("hero")), None)
    if h:
        hero = (f'<div class="ph ph-{h["key"]} hero" role="img" aria-label="{E(h.get("alt",""))}">'
                f'<div class="hero-cap">{E(h.get("caption",""))}</div></div>')
    return (f'<header class="mast"><div class="mast-top">'
            f'<p class="eyebrow">{E(t["eyebrow"])}</p><h1>{t["title_html"]}</h1>'
            f'<p class="mast-sub">{E(t["subtitle"])}</p></div>{hero}'
            f'<dl class="facts">{facts}</dl>'
            f'<div class="legend"><span class="key"><span class="dot check"></span> Check before relying on it</span>'
            f'<span class="key"><span class="dot stop"></span> No trip if missed</span>'
            + (f'<span class="asof">Facts checked {E(t["asof"])}</span></div></header>\n' if checked else
               f'<span class="asof">Facts researched {E(t["asof"])} &middot; links not machine-checked</span>'
               f'</div></header>\n'))


def r_contents(groups):
    out = []
    for i, g in enumerate(groups, 1):
        items = "".join(
            f'<li><a href="#{E(it["id"])}"><span class="toc-n">{it["n"]:02d}</span>'
            f'<span class="toc-t">{E(it["title"])}</span>'
            f'<span class="toc-kind">{E(it["kind"])}</span></a></li>' for it in g["items"])
        lo, hi = g["items"][0]["n"], g["items"][-1]["n"]
        out.append(f'<div class="phase p{i}"><div class="phase-head">'
                   f'<span class="phase-n">{lo:02d}&ndash;{hi:02d}</span>'
                   f'<span class="phase-name">{E(g["name"])}</span>'
                   f'<span class="phase-when">{E(g["when"])}</span></div>'
                   f'<ol class="toc-list">{items}</ol></div>')
    return f'<nav class="toc" aria-label="What\'s in this brief"><div class="toc-phases">{"".join(out)}</div></nav>\n'


def r_route(t):
    alert = ""
    if t.get("critical"):
        c = t["critical"]
        alert = (f'<div class="alert"><span class="dot stop"></span><div><b>{E(c["headline"])}</b>'
                 f'<span>{E(c["detail"])}</span></div></div>')
    rows = []
    for s in t["route"]:
        if s["kind"] == "leg":
            rows.append(f'<li class="jleg"><span class="jlabel">{s["label_html"]}</span></li>')
        elif s["kind"] == "base":
            trips = "".join(f'<li><span class="jt-tag">{E(x["tag"])}</span>{x["html"]}</li>'
                            for x in s.get("trips", []))
            photo = (f'<div class="ph ph-{s["photo"]} jphoto" role="img" aria-label="{E(s.get("alt",""))}"></div>'
                     if s.get("photo") else "")
            rows.append(
                f'<li class="jstop base {E(s["tone"])}"><span class="jmark"></span>'
                f'<div class="jbody jcard">{photo}<div class="jcard-text">'
                f'<div class="jname big">{E(s["name"])}</div>'
                f'<div class="jmeta"><span class="nights">{E(s["nights"])}</span> {s["meta_html"]}</div>'
                f'<ul class="jtrips">{trips}</ul></div></div></li>')
        else:
            rows.append(f'<li class="jstop"><span class="jmark{" end" if s.get("end") else ""}"></span>'
                        f'<div class="jbody"><div class="jname">{E(s["name"])}</div>'
                        f'<div class="jmeta">{E(s["meta"])}</div></div></li>')
    return alert + f'<ol class="journey">{"".join(rows)}</ol>'


def r_weather(t):
    rows = []
    for d in t["weather"]:
        cls = " class=\"wx-travel\"" if d.get("travel") else (" class=\"wx-key\"" if d.get("key") else "")
        temp = d.get("temp_html", "&mdash;")
        if d.get("check"):
            temp += ' <span class="dot check"></span>'
        rows.append(f'<tr{cls}><td class="wx-d">{E(d["day"])}</td><td>{d["where_html"]}</td>'
                    f'<td class="num">{temp}</td><td class="num">{E(d.get("light","—"))}</td>'
                    f'<td class="wx-n">{d["note_html"]}</td></tr>')
    stats = "".join(f'<div class="wx-stat"><div class="wx-stat-n">{E(s["n"])}</div>'
                    f'<div class="wx-stat-l">{E(s["label"])}</div></div>' for s in t.get("weather_stats", []))
    return (f'<div class="alert amber"><span class="dot check"></span><div>'
            f'<b>{E(t["weather_notice"]["headline"])}</b><span>{t["weather_notice"]["detail_html"]}</span></div></div>'
            f'<div class="panel scroll"><table class="wx"><thead><tr>'
            f'<th>Day</th><th>Where you are</th><th class="num">Typical high / low</th>'
            f'<th class="num">Daylight</th><th>What that means</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
            f'<div class="wx-foot">{stats}</div>'
            f'<p class="wx-src">{t.get("weather_sources_html","")}</p>')


def _leg(l):
    note = f'<span class="nx">{E(l["note"])}</span>' if l.get("note") else ""
    quiet = f'<p class="f-quiet">{E(l["quiet"])}</p>' if l.get("quiet") else ""
    return (f'<div class="f-leg"><p class="f-route">{E(l["route"])}{note}</p>'
            f'<p class="f-sub">{l["sub_html"]}</p>{quiet}</div>')


def r_flights(t):
    cards = []
    for f in t["flights"]:
        legs = "".join(_leg(l) for l in f["legs"])
        alt = f'<p class="f-alt">{f["alt_html"]}</p>' if f.get("alt_html") else ""
        cards.append(f'<article class="flight {E(f["tone"])}"><div class="flight-in">'
                     f'<div class="f-head"><span class="f-tag">{E(f["tag"])}</span>'
                     f'<span class="pill good">{E(f["pill"])}</span></div>{legs}{alt}</div></article>')
    fare = ""
    if t.get("fare_note"):
        fare = (f'<div class="fare"><span class="dot check"></span><div><b>{t["fare_note"]["headline_html"]}</b>'
                f'<span>{t["fare_note"]["detail_html"]}</span></div></div>')
    return f'<div class="flights">{"".join(cards)}</div>{fare}'


def r_hotels(t):
    cards = []
    for h in t["hotels"]:
        photo = ""
        if h.get("photo"):
            cap = f'<span class="h-img-cap">{E(h["photo_caption"])}</span>' if h.get("photo_caption") else ""
            photo = f'<div class="ph ph-{h["photo"]} h-img" role="img" aria-label="{E(h.get("alt",""))}">{cap}</div>'
        vs = "".join(f'<li><span class="vk {E(v["kind"])}">{E(v["label"])}</span><span>{E(v["text"])}</span></li>'
                     for v in h.get("verdicts", []))
        cards.append(f'<article class="hotel">{photo}<div class="h-city {E(h["tone"])}">{E(h["when"])}</div>'
                     f'<h3 class="h-name">{h["name_html"]}</h3>'
                     f'<p class="h-meta">{E(h["meta"])} &middot; {money(h.get("rate"))}</p>'
                     f'<div class="score">{E(h["score"])} <small>{E(h["score_src"])}</small></div>'
                     f'<ul class="verdicts">{vs}</ul><p class="so">{E(h["so"])}</p></article>')
    gap = f'<p class="gap-note">{t["hotels_gap_html"]}</p>' if t.get("hotels_gap_html") else ""
    return f'<div class="hotels">{"".join(cards)}</div>{gap}'


def r_before(t):
    rows = []
    for d in t["deadlines"]:
        k = d.get("kind", "")
        cls = {"crit": "is-crit", "key": "is-key", "go": "is-go", "now": "is-now"}.get(k, "")
        pill = ""
        if d.get("pill"):
            tone = "crit" if k == "crit" else "cool"
            pill = f'<span class="pill {tone}">{E(d["pill"])}</span>'
        rows.append(f'<li class="{cls}"><span class="r-date">{E(d["date"])}</span>'
                    f'<span class="r-mark"><span class="r-dot {k}"></span></span>'
                    f'<span class="r-what">{E(d["what"])}</span>{pill or "<span></span>"}</li>')
    return f'<div class="panel panel-pad"><ul class="rail">{"".join(rows)}</ul></div>'


def r_week(t):
    out = []
    for d in t["days"]:
        tone = f' {d["tone"]}' if d.get("tone") else ""
        thumb = (f'<div class="ph ph-{d["photo"]} d-thumb" role="img" aria-label="{E(d.get("alt",""))}"></div>'
                 if d.get("photo") else "")
        body = (f'<div class="d-body">{thumb}<div class="d-text">'
                f'<p class="d-main">{d["main_html"]}</p><p class="d-sub">{d["sub_html"]}</p></div></div>')
        out.append(f'<article class="day{tone}"><div class="d-when"><span class="d-day">{E(d["day"])}</span>'
                   f'<span class="d-city">{E(d["where"])}</span></div>{body}'
                   f'<span class="pill {E(d["pill_tone"])}">{E(d["pill"])}</span></article>')
    return f'<div class="days">{"".join(out)}</div>'


def r_places(t):
    out = []
    for p in t["places"]:
        img = (f'<div class="ph ph-{p["photo"]} p-img" role="img" aria-label="{E(p.get("alt",""))}"></div>'
               if p.get("photo") else "")
        out.append(f'<article class="place">{img}<div class="p-body">'
                   f'<div class="p-when {E(p["tone"])}">{E(p["when"])}</div>'
                   f'<h3 class="p-name">{p["name_html"]}</h3>'
                   f'<p class="p-fact">{money(p.get("price"))}{" &middot; " + E(p["extra"]) if p.get("extra") else ""}</p>'
                   f'<p class="p-note">{E(p["note"])}</p></div></article>')
    return f'<div class="places">{"".join(out)}</div>'


def r_reviews(t):
    out = []
    for v in t["reviews"]:
        out.append(f'<article class="verdict"><div class="v-who"><span class="v-name">{E(v["name"])}</span>'
                   f'<span class="v-src">{E(v["source"])}</span></div><div class="v-lines">'
                   f'<div>{E(v["loved"])}</div><div style="color:var(--ink-soft)">{E(v["watch"])}</div>'
                   f'<div class="so">{E(v["so"])}</div></div>'
                   f'<span class="pill {E(v["tone"])}">{E(v["verdict"])}</span></article>')
    return f'<div class="board">{"".join(out)}</div>'


def r_budget(t):
    b = t["budget"]
    cap, scale = b["cap"], b["scale"]
    X = lambda v: 200 + v / scale * 500
    hue = {"flights": "var(--salz)", "hotels": "var(--vie)", "food": "var(--ice)",
           "tickets": "var(--brass)", "transport": "var(--ink-faint)"}
    rows, y = [], 88
    for s in b["scenarios"]:
        off, segs = 0, []
        for item in s["items"]:
            x, w = X(off), X(item["usd"]) - 200
            lbl = (f'<text x="{x+w/2:.0f}" y="{y+22}" text-anchor="middle" font-size="11.5" font-weight="600" '
                   f'fill="var(--ink)" font-family="var(--mono)">${item["usd"]:,}</text>') if w > 44 else ""
            segs.append(f'<rect x="{x:.0f}" y="{y}" width="{max(w-2,2):.0f}" height="34" rx="3" '
                        f'fill="{hue.get(item["key"],"var(--ink-faint)")}" fill-opacity=".34" '
                        f'stroke="{hue.get(item["key"],"var(--ink-faint)")}"/>{lbl}')
            off += item["usd"]
        rows.append(f'<text x="24" y="{y-10}" font-size="13" font-weight="600" fill="var(--ink)" '
                    f'font-family="var(--sans)">{E(s["label"])}</text>{"".join(segs)}'
                    f'<text x="736" y="{y+22}" text-anchor="end" font-size="14" font-weight="600" '
                    f'fill="var(--ink)" font-family="var(--mono)">${s["total"]:,}</text>')
        y += 78
    legend = "".join(
        f'<rect x="{24+i*86}" y="{y+28}" width="11" height="11" rx="2" fill="{hue[k]}" fill-opacity=".34" stroke="{hue[k]}"/>'
        f'<text x="{41+i*86}" y="{y+38}" font-size="11.5" fill="var(--ink-soft)">{k.title()}</text>'
        for i, k in enumerate([x["key"] for x in b["scenarios"][0]["items"]]) if k in hue)
    capx = X(cap)
    return (f'<div class="panel scroll"><svg class="fig" viewBox="0 0 760 {y+54}" role="img" '
            f'aria-label="{E(b["alt"])}" font-size="13">'
            f'<text x="24" y="26" font-size="14" font-weight="600" fill="var(--ink)" '
            f'font-family="var(--sans)">{E(b["headline"])}</text>'
            f'<g font-family="var(--sans)">{"".join(rows)}'
            f'<line x1="{capx:.0f}" x2="{capx:.0f}" y1="72" y2="{y-10}" stroke="var(--crit)" '
            f'stroke-width="1.5" stroke-dasharray="4 4"/>'
            f'<text x="{capx:.0f}" y="64" text-anchor="middle" font-size="11.5" font-weight="600" '
            f'fill="var(--crit)" font-family="var(--mono)">${cap:,} cap</text>{legend}</g></svg></div>')


def r_planb(t):
    steps = "".join(f'<li><span class="jt-tag">{E(s["tag"])}</span>{s["html"]}</li>' for s in t["planb"]["steps"])
    swaps = "".join(
        (f'<div class="swap">' +
         (f'<div class="ph ph-{s["photo"]} sw-img" role="img" aria-label="{E(s.get("alt",""))}"></div>' if s.get("photo") else "") +
         f'<div class="sw-name">{s["name_html"]}</div><p class="sw-a">{E(s["text"])}</p></div>')
        for s in t["planb"]["swaps"])
    return (f'<div class="panel panel-pad"><ul class="jtrips" style="gap:9px">{steps}</ul></div>'
            f'<div class="swaps">{swaps}</div>')


def r_ground(t):
    out = []
    for g in t["ground"]:
        chk = ' <span class="dot check"></span>' if g.get("check") else ""
        out.append(f'<div class="tile{" danger" if g.get("danger") else ""}"><div class="tile-in">'
                   f'<div class="t-name">{E(g["name"])}{chk}</div>'
                   f'<p class="t-a">{g["a_html"]}</p><p class="t-b">{E(g["b"])}</p></div></div>')
    return f'<div class="tiles">{"".join(out)}</div>'


def r_bookings(t):
    rows = "".join(
        f'<tr><td><label class="chk"><input type="checkbox" id="bk-{E(b["id"])}">'
        f'<span>{E(b["item"])}</span></label></td><td class="num de">{E(b["date"])}</td>'
        f'<td><span class="blank"></span></td></tr>' for b in t["bookings"])
    return (f'<div class="panel scroll"><table><thead><tr><th>Item</th><th class="num">Date</th>'
            f'<th>Confirmation number</th></tr></thead><tbody>{rows}</tbody></table></div>')


def r_addresses(t):
    rows = "".join(f'<tr><td>{a["place_html"]}</td><td>{E(a["address"])}</td>'
                   f'<td class="num de">{E(a.get("phone","—"))}</td></tr>' for a in t["addresses"])
    return (f'<div class="panel scroll"><table><thead><tr><th>Place</th>'
            f'<th>Address, as written locally</th><th class="num">Phone</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


SCRIPT = """
(function(){
  var btn=document.getElementById('print');
  if(btn)btn.addEventListener('click',function(){window.print();});
  var boxes=document.querySelectorAll('input[type="checkbox"][id^="bk-"]');
  for(var i=0;i<boxes.length;i++){
    try{boxes[i].checked=localStorage.getItem('trip.'+boxes[i].id)==='1';}catch(e){}
    boxes[i].addEventListener('change',function(ev){
      try{localStorage.setItem('trip.'+ev.target.id,ev.target.checked?'1':'0');}catch(e){}
    });
  }
  /* tap a photo to see it whole, full size; tap again or Esc to close */
  var zoom=document.createElement('div');zoom.id='zoom';zoom.hidden=true;
  zoom.setAttribute('role','dialog');zoom.setAttribute('aria-label','Photo, full size. Tap to close.');
  document.body.appendChild(zoom);
  function shut(){zoom.hidden=true;zoom.innerHTML='';}
  zoom.addEventListener('click',shut);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!zoom.hidden)shut();});
  document.addEventListener('click',function(e){
    var el=e.target.closest?e.target.closest('.ph'):null;if(!el||e.target.closest('a'))return;
    var img=getComputedStyle(el).backgroundImage;if(!img||img==='none')return;
    var zi=document.createElement('div');zi.className='zi';zi.style.backgroundImage=img;zoom.appendChild(zi);
    var t=el.getAttribute('aria-label');if(t){var p=document.createElement('p');p.textContent=t;zoom.appendChild(p);}
    zoom.hidden=false;
  });
  var nav=document.getElementById('railnav'),mast=document.querySelector('.mast');
  var sections=Array.prototype.slice.call(document.querySelectorAll('section[id]'));
  if(!nav||!mast||!('IntersectionObserver' in window))return;
  var byId={};Array.prototype.forEach.call(nav.querySelectorAll('a'),function(a){
    byId[a.getAttribute('href').slice(1)]=a;});
  new IntersectionObserver(function(es){nav.classList.toggle('on',!es[0].isIntersecting);},
    {rootMargin:'-40px 0px 0px 0px'}).observe(mast);
  var vis={};
  var spy=new IntersectionObserver(function(es){
    es.forEach(function(e){vis[e.target.id]=e.isIntersecting;});
    var cur=null;
    for(var i=0;i<sections.length;i++){if(vis[sections[i].id]){cur=sections[i].id;break;}}
    Object.keys(byId).forEach(function(id){byId[id].removeAttribute('aria-current');});
    if(cur&&byId[cur])byId[cur].setAttribute('aria-current','true');
  },{rootMargin:'-64px 0px -58% 0px'});
  sections.forEach(function(s){spy.observe(s);});
})();
"""

RENDER = {"route": r_route, "weather": r_weather, "flights": r_flights, "hotels": r_hotels,
          "before": r_before, "week": r_week, "places": r_places, "reviews": r_reviews,
          "budget": r_budget, "planb": r_planb, "ground": r_ground,
          "bookings": r_bookings, "addresses": r_addresses}


def live_block(trip):
    """The one sanctioned network use: the trip Gem's live-photos.js, unchanged, plus the
    three names it expects from the Gem's engine (E, A, PHOTO_LINE) and its call."""
    js = open(LIVE, encoding="utf-8").read()
    photos = [{"key": p["key"], "wiki": p["wiki"], "label": p.get("label", p["key"])}
              for p in trip.get("photos", []) if p.get("wiki")]
    data = json.dumps({"photos": photos}, ensure_ascii=False).replace("</", "<\\/")
    return ("<script>\n/* Photos named by Wikipedia article (\"wiki\") are fetched when this page is opened\n"
            "   online, and hidden offline. This block is the page's only network use besides fonts. */\n"
            "function E(s){\n"
            "  return String(s == null ? \"\" : s).replace(/&/g, \"&amp;\").replace(/</g, \"&lt;\")\n"
            "    .replace(/>/g, \"&gt;\").replace(/\"/g, \"&quot;\").replace(/'/g, \"&#x27;\");\n}\n"
            "function A(x){ return Array.isArray(x) ? x : []; }\n"
            f"var PHOTO_LINE = {json.dumps(PHOTO_LINE)};\n"
            f"{js.rstrip()}\n"
            f"try{{ livePhotos({data}); }}catch(e){{\n"
            "  /* a fault in the loader: hide every photo box so the page stays whole, then report it */\n"
            "  var st = document.getElementById(\"photos\"); if(st) st.appendChild(document.createTextNode(\"\\n.ph{display:none}\"));\n"
            "  setTimeout(function(){ throw new Error(\"live photos: \" + (e && e.message || e)); }, 0);\n"
            "}\n</script>\n")


def render(trip, photo_css, credits, checked=True, live=False):
    css = open(os.path.join(ASSETS, "style.css"), encoding="utf-8").read()
    css = css.replace("/* photo classes are appended here by build_page.py */", photo_css)

    secs, toc_items = [], []
    for i, s in enumerate(trip["sections"], 1):
        fn = RENDER.get(s["id"])
        if not fn:
            continue
        secs.append(sec(s["id"], s["title"], s["tag"], s.get("note_html", ""), fn(trip)))
        toc_items.append({"n": i, "id": s["id"], "title": s["title"], "kind": s["kind"], "group": s["group"]})

    groups = []
    for name, when in trip["toc_groups"]:
        items = [x for x in toc_items if x["group"] == name]
        if items:
            groups.append({"name": name, "when": when, "items": items})

    rail = "".join(f'<a href="#{E(x["id"])}">{E(x.get("short", x["title"]))}</a>' for x in toc_items)

    srcs = "".join(f'<p><strong>{E(s["label"])}:</strong> {s["html"]}</p>' for s in trip.get("sources", []))
    cred = (" &middot; ".join(credits) + ".") if credits else "No photographs embedded."
    if live:
        photo_line = E(PHOTO_LINE) + "No photographs loaded."       # live-photos.js refills this
    else:
        photo_line = ("All photographs from Wikimedia Commons, reused under their stated licences and "
                      f"embedded in this file. {cred}")
    src_head = (f'Sources &middot; checked {E(trip["asof"])}' if checked else
                f'Sources &middot; researched {E(trip["asof"])} &middot; links not machine-checked')
    not_checked = "" if checked else f'<p class="not-checked" style="margin-top:12px">{E(NOT_CHECKED)}</p>'

    return (f'<title>{E(trip["page_title"])}</title>\n'
            f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            f'family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700'
            f'&family=Instrument+Serif:ital@0;1&display=swap">\n'
            f'<style>\n{css}\n</style>\n'
            + ('<style id="photos"></style>\n' if live else '') +
            f'<nav class="rail-nav" id="railnav" aria-label="Jump to section"><div class="rail-in">{rail}</div></nav>\n'
            f'<div class="wrap">\n{r_masthead(trip, checked)}{r_contents(groups)}{"".join(secs)}'
            f'<div class="src"><h3>{src_head}</h3>{srcs}'
            f'<h3 style="margin-top:16px">Photographs</h3><p class="credit">'
            f'{photo_line}</p>'
            f'<p style="margin-top:12px">Anything marked <span class="dot check" '
            f'style="display:inline-block;vertical-align:middle"></span> is perishable &mdash; prices, '
            f'opening hours, timetables and entry rules change. Nothing here is a booking.</p>{not_checked}</div>\n'
            f'<div class="foot"><span>{E(trip["footer"])}</span>'
            f'<button class="btn" id="print">Print this page</button></div>\n</div>\n'
            f'<script>{SCRIPT}</script>\n'
            + (live_block(trip) if live else ''))


# ---------------------------------------------------------------- main
def refuse_if_networked(page, trip, live):
    """The one sanctioned network use is the live-photo block, so it is taken out (once,
    exactly) before the guard reads the page."""
    if live:
        block = live_block(trip)
        if page.count(block) != 1:
            print("REFUSED TO BUILD\n  the live-photo block is not in the page exactly once - update build_page.py",
                  file=sys.stderr)
            sys.exit(2)
        page = page.replace(block, "")
    why = network_problem(page)
    if why:
        print("REFUSED TO BUILD\n  the page would reach the network: " + why +
              "\n  a *_html field may hold <a href>, <strong>, <em> and plain formatting - no images, "
              "embeds, scripts, styles that load, or other <link>s", file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default="trip-brief.html")
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--no-net", action="store_true",
                    help="skip photos and link checking; the page then says its links were not machine-checked")
    ap.add_argument("--live-photos", dest="live_photos", action="store_true",
                    help="for a tool whose builder has no internet (e.g. Copilot Cowork): implies --no-net; "
                         "stores no photos, and the page loads each photo's Wikipedia article image when opened online")
    a = ap.parse_args()
    if a.live_photos:
        a.no_net = True        # a builder that cannot download photos cannot check links either

    trip = json.load(open(a.spec, encoding="utf-8"))

    try:
        blocked = []
        validate(trip, a.explain)
        if a.live_photos:
            no_wiki = sorted(str(p.get("key", "?")) for p in trip.get("photos", []) if not p.get("wiki"))
            if no_wiki:
                # the page can only load a photo it can name by Wikipedia article; any other would never show
                raise Refused("  with --live-photos every photo needs a \"wiki\" article title: "
                              + ", ".join(no_wiki)
                              + "\n  give each one the English Wikipedia article about that exact place, or drop it")
        page_links = collect_links(trip)
        if not a.no_net:
            if a.explain:
                print(f"checking {len(page_links)} links", file=sys.stderr)
            blocked = check_links(page_links, a.explain)
    except Refused as e:
        print("REFUSED TO BUILD\n" + str(e), file=sys.stderr)
        print("\nFix the data rather than the check. Run with --explain for detail.", file=sys.stderr)
        sys.exit(2)

    # refuse a networked page before spending minutes on photographs; checked again on the final page
    refuse_if_networked(render(trip, "", [], checked=not a.no_net, live=a.live_photos), trip, a.live_photos)
    if a.explain and not a.no_net:
        print("fetching photographs", file=sys.stderr)
    photo_css, credits = build_photo_css(trip, a.explain, a.no_net)

    # a photo key referenced by the page but never fetched renders as a grey box
    have = set(re.findall(r'\.ph-([a-z0-9-]+)\{', photo_css))
    want = {s["key"] for s in trip.get("photos", [])}
    missing = want - have
    if missing and not a.live_photos:
        print(f"  WARNING: no photograph found for {', '.join(sorted(missing))} - "
              f"those slots render as empty boxes. Give them a better 'wiki' or 'search'.",
              file=sys.stderr)

    page = render(trip, photo_css, credits, checked=not a.no_net, live=a.live_photos)
    refuse_if_networked(page, trip, a.live_photos)
    open(a.out, "w", encoding="utf-8").write(page)
    mb = os.path.getsize(a.out) / 1048576
    if a.no_net:
        why = "--live-photos" if a.live_photos else "--no-net"
        print(f"built {a.out}  {mb:.2f} MB  {len(credits)} photographs  "
              f"{len(page_links)} links NOT checked ({why})")
    else:
        print(f"built {a.out}  {mb:.2f} MB  {len(credits)} photographs  {len(page_links)} links checked")
    n_live = sum(1 for p in trip.get("photos", []) if p.get("wiki")) if a.live_photos else 0
    if n_live:
        print(f"  {n_live} photos are not stored: the page loads them from Wikipedia when opened "
              f"online, and hides them offline")
    if a.no_net:
        print("  the page says its links were not machine-checked. Tell the traveller the same, in these words:\n"
              f"  \"{NOT_CHECKED}\"")
    if blocked:
        print(f"  {len(blocked)} link(s) refused a robot and could not be machine-verified "
              f"(they may still be fine in a browser):", file=sys.stderr)
        for u in blocked:
            print(f"    {u}", file=sys.stderr)
    if mb > 16:
        print("WARNING: over the 16 MB artifact limit", file=sys.stderr)


if __name__ == "__main__":
    main()
