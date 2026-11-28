"""Merge Civ 6 game data + hand-written real-world data + Civ wiki art + Wikipedia photos into data.js.

usage: python3 -I build.py <parsed.json> <world.json> <natural.json> <cache_dir> <out data.js>
"""
import json, sys, os, re, math, hashlib, time, html, urllib.parse, urllib.request

parsed_p, world_p, natural_p, cache_dir, out_p = sys.argv[1:6]
os.makedirs(cache_dir, exist_ok=True)
UA = {"User-Agent": "civ6map-local/1.0 (personal fan map)"}

def get(url):
    key = os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            json.dump(data, open(key, "w"))
            time.sleep(0.15)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                json.dump({"_404": True}, open(key, "w"))
                return {"_404": True}
            time.sleep(4 * (attempt + 1))
        except Exception:
            time.sleep(4 * (attempt + 1))
    return {}

def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]

def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

ERAS = ["Ancient", "Classical", "Medieval", "Renaissance", "Industrial", "Modern", "Atomic", "Information"]
parsed = json.load(open(parsed_p))
civ_w = {w["name"]: w for w in parsed["wonders"]}
civ_n = {n["name"]: n for n in parsed["naturals"]}
SCENARIO = {
    "Kakadu": dict(expansion="Australia Civilization & Scenario Pack", scenario="Outback Tycoon scenario only",
                   effects=["Scenario-only natural wonder from Outback Tycoon."], size="", notes=""),
    "Pinnacles": dict(expansion="Australia Civilization & Scenario Pack", scenario="Outback Tycoon scenario only",
                      effects=["Scenario-only natural wonder from Outback Tycoon."], size="", notes=""),
    "Vinland": dict(expansion="Vikings, Traders, and Raiders! (game mode scenario)", scenario="Vikings, Traders, and Raiders! scenario only",
                    effects=["+1 {Culture}, +1 {Gold} to adjacent tiles.", "Provides victory points for activating Great Admirals adjacent to the wonder."],
                    size="3 tiles, impassable", notes="Found in the middle of the ocean on the western edge of the map."),
}

world = json.load(open(world_p))
natural = json.load(open(natural_p)) if os.path.exists(natural_p) else []

entries = []
for w in world:
    c = civ_w.get(w["name"])
    if not c:
        print("!! no civ data for", w["name"]); continue
    e = dict(kind="world", **w)
    e.update(era=c["era"], eraIndex=ERAS.index(c["era"]) if c["era"] in ERAS else -1, expansion=c["expansion"],
             req=c["req"], cost=c["cost"], effects=c["effects"], placement=c["placement"])
    entries.append(e)
for n in natural:
    c = civ_n.get(n["name"]) or SCENARIO.get(n["name"])
    if not c:
        print("!! no civ data for natural", n["name"]); continue
    e = dict(kind="natural", **n)
    e.update(expansion=c["expansion"], effects=c["effects"], notes=c.get("notes", ""), size=c.get("size", ""),
             scenario=c.get("scenario", ""))
    entries.append(e)
missing = set(civ_w) - {e["name"] for e in entries if e["kind"] == "world"}
missing_n = set(civ_n) - {e["name"] for e in entries if e["kind"] == "natural"}
if missing: print("!! world wonders without real-world data:", missing)
if missing_n and natural: print("!! natural wonders without real-world data:", missing_n)

# ---------- Wikipedia: resolve titles + coordinates ----------
WAPI = "https://en.wikipedia.org/w/api.php?"
title_info = {}
for batch in chunks([e["wiki"] for e in entries], 40):
    q = WAPI + urllib.parse.urlencode(dict(action="query", format="json", redirects=1, prop="coordinates|description|info",
                                           inprop="url", titles="|".join(batch)))
    d = get(q).get("query", {})
    norm = {x["from"]: x["to"] for x in d.get("normalized", [])}
    redir = {x["from"]: x["to"] for x in d.get("redirects", [])}
    pages = {p["title"]: p for p in d.get("pages", {}).values()}
    for t in batch:
        t2 = norm.get(t, t); t3 = redir.get(t2, t2)
        p = pages.get(t3)
        title_info[t] = p if p and "missing" not in p else None

def km(a, b, c, d):
    R = 6371; p1, p2 = math.radians(a), math.radians(c)
    dp = p2 - p1; dl = math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

for e in entries:
    p = title_info.get(e["wiki"])
    if not p:
        print("!! wikipedia title not found:", e["name"], "->", e["wiki"]); e["wikiUrl"] = ""; continue
    e["wikiTitle"] = p["title"]
    e["wikiUrl"] = p.get("fullurl", "https://en.wikipedia.org/wiki/" + urllib.parse.quote(p["title"].replace(" ", "_")))
    e["wikiDesc"] = p.get("description", "")
    co = (p.get("coordinates") or [None])[0]
    if co:
        dist = km(e["lat"], e["lng"], co["lat"], co["lon"])
        if dist > 25:
            print(f"   coord diff {dist:7.0f} km  {e['name']}: ours {e['lat']},{e['lng']}  wiki {co['lat']},{co['lon']}")

# ---------- Wikipedia: photos ----------
BAD = re.compile(r"(\.svg$|\.gif$|\.tif|map|karte|locator|location|relief|flag|coat_of_arms|logo|icon|plan\b|plan_|diagram|seal_of|signature|chart|graph|stamp|banknote|coin|\.webm|\.ogv)", re.I)
for e in entries:
    if not e.get("wikiTitle"):
        e["photos"] = []; continue
    ml = get("https://en.wikipedia.org/api/rest_v1/page/media-list/" + urllib.parse.quote(e["wikiTitle"].replace(" ", "_"), safe=""))
    cands = []
    for it in ml.get("items", []):
        if it.get("type") != "image": continue
        t = it.get("title", "")
        if BAD.search(t): continue
        cands.append((t, strip_html((it.get("caption") or {}).get("html", "")) or (it.get("caption") or {}).get("text", "")))
        if len(cands) >= 14: break
    infos = {}
    if cands:
        q = WAPI + urllib.parse.urlencode(dict(action="query", format="json", prop="imageinfo", iiprop="url|size|mime|extmetadata",
                                               iiurlwidth=960, iiextmetadatafilter="Artist|LicenseShortName|ImageDescription",
                                               titles="|".join(t for t, _ in cands)))
        d = get(q).get("query", {})
        norm = {x["from"]: x["to"] for x in d.get("normalized", [])}
        for p in d.get("pages", {}).values():
            if p.get("imageinfo"): infos[p["title"]] = p["imageinfo"][0]
        rev = {v: k for k, v in norm.items()}
    photos = []
    for t, cap in cands:
        ii = infos.get(t) or infos.get(t.replace("_", " "))
        if not ii: continue
        if ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"): continue
        w_, h_ = ii.get("width", 0), ii.get("height", 0)
        if w_ < 640 or h_ < 400: continue
        ar = w_ / max(h_, 1)
        if ar < 0.55 or ar > 2.6: continue
        if ii.get("mime") == "image/png" and w_ * h_ < 600_000: continue
        md = ii.get("extmetadata", {})
        thumb = ii.get("thumburl") or ii["url"]
        small = re.sub(r"/960px-", "/330px-", thumb) if "/960px-" in thumb else thumb
        desc = cap or strip_html(md.get("ImageDescription", {}).get("value", ""))
        photos.append(dict(src=thumb, small=small, page=ii.get("descriptionurl", ""), w=w_, h=h_,
                           caption=desc[:180], credit=strip_html(md.get("Artist", {}).get("value", ""))[:80],
                           license=strip_html(md.get("LicenseShortName", {}).get("value", ""))))
        if len(photos) >= 7: break
    e["photos"] = photos
    if len(photos) < 3: print(f"   only {len(photos)} photos: {e['name']} ({e['wikiTitle']})")

# ---------- Civ wiki art ----------
FAPI = "https://civilization.fandom.com/api.php?"
pages_civ = {e["name"]: e["name"] + " (Civ6)" for e in entries}
civ_pages = {}
for batch in chunks(list(pages_civ.values()), 40):
    q = FAPI + urllib.parse.urlencode(dict(action="query", format="json", redirects=1, prop="pageimages|images|info", inprop="url",
                                           piprop="original|name", imlimit=500, titles="|".join(batch)))
    # images can paginate; loop continue
    d = get(q)
    acc = {}
    while True:
        qd = d.get("query", {})
        norm = {x["from"]: x["to"] for x in qd.get("normalized", [])}
        redir = {x["from"]: x["to"] for x in qd.get("redirects", [])}
        for p in qd.get("pages", {}).values():
            a = acc.setdefault(p["title"], dict(images=[], original=None, url=None))
            a["images"] += [i["title"] for i in p.get("images", [])]
            if p.get("original"): a["original"] = p["original"]["source"]
            if p.get("fullurl"): a["url"] = p["fullurl"]
        for t in batch:
            t2 = norm.get(t, t); civ_pages.setdefault(t, redir.get(t2, t2))
        if "continue" not in d: break
        params = dict(action="query", format="json", redirects=1, prop="pageimages|images|info", inprop="url", piprop="original|name",
                      imlimit=500, titles="|".join(batch))
        params.update(d["continue"])
        d = get(FAPI + urllib.parse.urlencode(params))
    for t in batch:
        civ_pages[t] = acc.get(civ_pages.get(t, t))

want = {}
for e in entries:
    info = civ_pages.get(pages_civ[e["name"]])
    e["civ"] = dict(page=(info or {}).get("url") or "https://civilization.fandom.com/wiki/" + urllib.parse.quote(pages_civ[e["name"]].replace(" ", "_")),
                    icon=(info or {}).get("original"), render=None, splash=None)
    if not info:
        print("!! no civ wiki page:", e["name"]); continue
    base = e["name"]
    imgs = info["images"]
    splash = [i for i in imgs if re.match(r"File:Wonder ", i) and i.lower().endswith((".jpg", ".png", ".jpeg"))]
    render = [i for i in imgs if "in-game" in i.lower() or "ingame" in i.lower()]
    if splash: want[splash[0]] = (e, "splash")
    if render: want[render[0]] = (e, "render")

for batch in chunks(list(want), 40):
    q = FAPI + urllib.parse.urlencode(dict(action="query", format="json", prop="imageinfo", iiprop="url|size", titles="|".join(batch)))
    d = get(q).get("query", {})
    norm = {x["to"]: x["from"] for x in d.get("normalized", [])}
    for p in d.get("pages", {}).values():
        t = norm.get(p["title"], p["title"])
        if t in want and p.get("imageinfo"):
            e, slot = want[t]
            e["civ"][slot] = p["imageinfo"][0]["url"]

no_art = [e["name"] for e in entries if not (e["civ"].get("splash") or e["civ"].get("render"))]
if no_art: print("   no civ splash/render art:", no_art)

# ---------- output ----------
for i, e in enumerate(sorted(entries, key=lambda x: (x["kind"], x.get("eraIndex", 0), x["name"]))):
    e["id"] = re.sub(r"[^a-z0-9]+", "-", e["name"].lower().encode("ascii", "ignore").decode()).strip("-") or f"w{i}"
entries.sort(key=lambda x: (x["kind"] != "world", x.get("eraIndex", 0), x["name"]))
keep = ["id", "kind", "name", "real", "era", "eraIndex", "expansion", "scenario", "req", "cost", "effects", "placement", "notes", "size",
        "place", "lat", "lng", "approx", "when", "history", "wikiTitle", "wikiUrl", "wikiDesc", "civ", "photos"]
out = [{k: e[k] for k in keep if k in e and e[k] not in (None, "")} for e in entries]
js = "/* Generated by build.py — Civ 6 data from the Civilization Wiki (civilization.fandom.com), photos from Wikimedia Commons. */\n"
js += "window.CIV6_WONDERS = " + json.dumps(out, ensure_ascii=False, indent=0) + ";\n"
open(out_p, "w").write(js)
print(f"wrote {out_p}: {sum(e['kind']=='world' for e in out)} world, {sum(e['kind']=='natural' for e in out)} natural, "
      f"{sum(len(e.get('photos', [])) for e in out)} photos, {os.path.getsize(out_p)//1024} KB")
