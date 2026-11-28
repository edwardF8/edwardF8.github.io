"""Build civs.js: civilizations + leaders + uniques (Civ wiki) + photos (Wikipedia/Commons).

usage: python3 -I civ_build.py <civs.json> <cache_dir> <out civs.js>
civs.json is the hand-researched list (name, civPage, leaders[], wiki, lat/lng, history, wonders...).
"""
import json, sys, os, re, time, html, hashlib, urllib.parse, urllib.request

civs_p, cache_dir, out_p = sys.argv[1:4]
os.makedirs(cache_dir, exist_ok=True)
UA = {"User-Agent": "civ6map-local/1.0 (personal fan map)"}
FAPI = "https://civilization.fandom.com/api.php?"
WAPI = "https://en.wikipedia.org/w/api.php?"


def get(url):
    key = os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".json")
    if os.path.exists(key):
        return json.load(open(key))
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                data = json.loads(r.read().decode())
            json.dump(data, open(key, "w"))
            time.sleep(0.2)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                json.dump({"_404": True}, open(key, "w"))
                return {"_404": True}
            time.sleep(4 * (attempt + 1))
        except Exception:
            time.sleep(4 * (attempt + 1))
    print("!! request failed:", url[:140])
    return {}


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


ICON = {
    'Faith6': '{Faith}', 'Science6': '{Science}', 'Culture6': '{Culture}', 'Gold6': '{Gold}', 'Production6': '{Production}',
    'Food6': '{Food}', 'Amenities6': '{Amenity}', 'Amenity6': '{Amenity}', 'Housing6': '{Housing}', 'Tourism6': '{Tourism}',
    'TourismIcon6': '{Tourism}', 'Citizen6': '{Citizen}', 'CitizenIcon6': '{Citizen}', 'Envoys6': '{Envoy}', 'Envoy6': '{Envoy}',
    'TradeRoute6': '{TradeRoute}', 'Power6': '{Power}', 'Movement6': '{Movement}', 'Moves6': '{Movement}', 'DiplomaticFavor6': '{Favor}',
    'Strength6': '{Strength}', 'StrengthIcon6': '{Strength}', 'ProductionIcon6': '{Production}', 'GoldIcon6': '{Gold}',
    'FaithIcon6': '{Faith}', 'ScienceIcon6': '{Science}', 'CultureIcon6': '{Culture}', 'FoodIcon6': '{Food}',
    'GS': '[GS]', 'R&F': '[R&F]', 'District6': 'district', 'Capital6': 'Capital',
    'Scientist6': 'Great Scientist', 'Writer6': 'Great Writer', 'Musician6': 'Great Musician', 'Merchant6': 'Great Merchant',
    'Admiral6': 'Great Admiral', 'General6': 'Great General', 'Prophet6': 'Great Prophet', 'Engineer6': 'Great Engineer',
    'Artist6': 'Great Artist', 'GreatPeople6': 'Great People', 'MilitaryPolicy6': '', 'EconomicPolicy6': '',
    'DiplomaticPolicy6': '', 'WildcardSlot6': '', 'BuildChargesIcon6': '', 'Promotion6': 'promotion',
    'Loyalty6': 'Loyalty', 'Era6': 'Era Score', 'Appeal6': 'Appeal',
}

ICON_LC = {k.lower(): v for k, v in ICON.items()}


def clean(s):
    s = s or ""
    s = re.sub(r'<ref[^>]*/>', '', s)
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)

    def tpl(m):
        parts = m.group(1).split('|')
        name = parts[0].strip()
        if name in ICON:
            return ICON[name]
        if name.lower() in ICON_LC:
            return ICON_LC[name.lower()]
        if name.startswith('Req6') and len(parts) > 1:
            return f"(requires {parts[1]})"
        if len(parts) > 1:
            return parts[-1]
        return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', re.sub(r'(Icon)?6$', '', name))
    for _ in range(4):
        s = re.sub(r'\{\{([^{}]*)\}\}', tpl, s)
    s = re.sub(r"'''?", '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n', s)
    return s.strip()


def infobox(text, names):
    """Return {field: raw value} for the first {{<name> ...}} template found."""
    start = -1
    for n in names:
        start = text.find("{{" + n)
        if start >= 0:
            break
    if start < 0:
        return {}
    i, depth = start, 0
    while i < len(text):
        if text.startswith("{{", i) or text.startswith("[[", i):
            depth += 1; i += 2; continue
        if text.startswith("}}", i) or text.startswith("]]", i):
            depth -= 1; i += 2
            if depth == 0:
                break
            continue
        i += 1
    body = text[start + 2:i - 2]
    fields, cur, d, j = [], "", 0, 0
    while j < len(body):
        two = body[j:j + 2]
        if two in ("{{", "[["):
            d += 1; cur += two; j += 2; continue
        if two in ("}}", "]]"):
            d -= 1; cur += two; j += 2; continue
        if body[j] == "|" and d == 0:
            fields.append(cur); cur = ""; j += 1; continue
        cur += body[j]; j += 1
    fields.append(cur)
    out = {}
    for f in fields[1:]:
        if "=" in f:
            k, v = f.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def fetch_pages(titles):
    """title -> dict(text, image, url, title) via the Civ wiki API (follows redirects)."""
    res = {}
    for batch in chunks(sorted(set(titles)), 40):
        q = FAPI + urllib.parse.urlencode(dict(action="query", format="json", redirects=1, prop="revisions|pageimages|info",
                                               rvprop="content", rvslots="main", piprop="original", inprop="url",
                                               titles="|".join(batch)))
        d = get(q).get("query", {})
        norm = {x["from"]: x["to"] for x in d.get("normalized", [])}
        red = {x["from"]: x["to"] for x in d.get("redirects", [])}
        pages = {p["title"]: p for p in d.get("pages", {}).values()}
        for t in batch:
            t2 = norm.get(t, t)
            p = pages.get(red.get(t2, t2))
            if not p or "revisions" not in p:
                res[t] = None
                continue
            res[t] = dict(text=p["revisions"][0]["slots"]["main"]["*"], image=(p.get("original") or {}).get("source"),
                          url=p.get("fullurl"), title=p["title"])
    return res


def strip_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


BAD = re.compile(r"(\.svg$|\.gif$|\.tif|map|karte|locator|location|relief|flag|coat_of_arms|logo|icon|plan\b|plan_|diagram|seal_of|signature|chart|graph|stamp|banknote|\.webm|\.ogv|territor|extent|expansion|empire_|_empire\.|borders)", re.I)


def photos_for(title):
    ml = get("https://en.wikipedia.org/api/rest_v1/page/media-list/" + urllib.parse.quote(title.replace(" ", "_"), safe=""))
    cands = []
    for it in ml.get("items", []):
        t = it.get("title", "")
        if it.get("type") != "image" or BAD.search(t):
            continue
        cands.append((t, strip_html((it.get("caption") or {}).get("html", ""))))
        if len(cands) >= 14:
            break
    if not cands:
        return []
    q = WAPI + urllib.parse.urlencode(dict(action="query", format="json", prop="imageinfo", iiprop="url|size|mime|extmetadata",
                                           iiurlwidth=960, iiextmetadatafilter="Artist|LicenseShortName|ImageDescription",
                                           titles="|".join(t for t, _ in cands)))
    infos = {p["title"]: p["imageinfo"][0] for p in get(q).get("query", {}).get("pages", {}).values() if p.get("imageinfo")}
    out = []
    for t, cap in cands:
        ii = infos.get(t) or infos.get(t.replace("_", " "))
        if not ii or ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
            continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < 640 or h < 400 or not (0.55 <= w / max(h, 1) <= 2.6):
            continue
        if ii.get("mime") == "image/png" and w * h < 600_000:
            continue
        md = ii.get("extmetadata", {})
        src = ii.get("thumburl") or ii["url"]
        out.append(dict(src=src, small=src.replace("/960px-", "/330px-") if "/960px-" in src else src, page=ii.get("descriptionurl", ""),
                        caption=(cap or strip_html(md.get("ImageDescription", {}).get("value", "")))[:180],
                        credit=strip_html(md.get("Artist", {}).get("value", ""))[:80],
                        license=strip_html(md.get("LicenseShortName", {}).get("value", ""))))
        if len(out) >= 7:
            break
    return out


civs = json.load(open(civs_p))

# 1. civ + leader pages
civ_pages = fetch_pages([c["civPage"] for c in civs])
leader_titles = [l["page"] for c in civs for l in c.get("leaders", [])]
leader_pages = fetch_pages(leader_titles)

UNIQUE_KEYS = re.compile(r"^(unit|building|district|improvement|infrastructure)\d*$")
unique_names = set()
for c in civs:
    p = civ_pages.get(c["civPage"])
    if not p:
        print("!! civ page missing:", c["civPage"]); continue
    ib = infobox(p["text"], ["Civ (Civ6)"])
    c["_ib"] = ib
    c["_uniques"] = []
    for k, v in ib.items():
        if UNIQUE_KEYS.match(k):
            for name in [x.strip() for x in clean(v).split(",") if x.strip()]:
                c["_uniques"].append(name); unique_names.add(name)
    for l in c.get("leaders", []):
        lp = leader_pages.get(l["page"])
        if not lp:
            print("!! leader page missing:", l["page"]); continue
        lib = infobox(lp["text"], ["Leader (Civ6)"])
        l["_ib"], l["_img"], l["_url"] = lib, lp["image"], lp["url"]
        l["_uniques"] = []
        for k, v in lib.items():
            if UNIQUE_KEYS.match(k):
                for name in [x.strip() for x in clean(v).split(",") if x.strip()]:
                    l["_uniques"].append(name); unique_names.add(name)

# 2. unique units / buildings / improvements
uniq_pages = fetch_pages([n + " (Civ6)" for n in unique_names])
TYPES = {"Unit (Civ6)": "Unit", "Building (Civ6)": "Building", "District (Civ6)": "District", "Improvement (Civ6)": "Improvement"}
uniques = {}
for n in unique_names:
    p = uniq_pages.get(n + " (Civ6)")
    if not p:
        print("   unique page missing:", n); uniques[n] = dict(name=n); continue
    kind, ib = "Unique", {}
    for tname, label in TYPES.items():
        variants = [tname, tname.replace(" ", "_")]
        if any("{{" + v in p["text"] for v in variants):
            kind, ib = label, infobox(p["text"], variants); break
    desc = ib.get("notes") or ib.get("effect") or ib.get("effects") or ib.get("description") or ib.get("great_person_points") or ""
    desc = clean(desc)
    if kind == "Unit":
        stats = [f"{lbl} {clean(ib[k]).split(chr(10))[0]}" for k, lbl in (("strength", "Strength"), ("rangedstrength", "Ranged"), ("moves", "Moves")) if ib.get(k)]
        if stats:
            desc = (desc + "\n" if desc else "") + " · ".join(stats)
    uniques[n] = dict(name=n, kind=kind, replaces=clean(ib.get("replaces", "")), era=clean(ib.get("era", "")),
                      desc=desc[:600], icon=p["image"], url=p["url"])

# 3. wikipedia link + photos
wiki_titles = {}
for batch in chunks([c["wiki"] for c in civs], 40):
    d = get(WAPI + urllib.parse.urlencode(dict(action="query", format="json", redirects=1, prop="info", inprop="url", titles="|".join(batch)))).get("query", {})
    norm = {x["from"]: x["to"] for x in d.get("normalized", [])}
    red = {x["from"]: x["to"] for x in d.get("redirects", [])}
    pages = {p["title"]: p for p in d.get("pages", {}).values()}
    for t in batch:
        t2 = norm.get(t, t)
        p = pages.get(red.get(t2, t2))
        wiki_titles[t] = p if p and "missing" not in p else None

out = []
for c in civs:
    ib = c.get("_ib", {})
    cp = civ_pages.get(c["civPage"]) or {}
    wp = wiki_titles.get(c["wiki"])
    if not wp:
        print("!! wikipedia title missing:", c["wiki"])
    photos = photos_for(wp["title"]) if wp else []
    if len(photos) < 3:
        print(f"   only {len(photos)} photos: {c['name']} ({c['wiki']})")
    leaders = []
    for l in c.get("leaders", []):
        lib = l.get("_ib", {})
        leaders.append(dict(
            name=l["name"], persona=l.get("persona", ""), dlc=l.get("dlc", ""),
            portrait=l.get("_img"), url=l.get("_url"),
            ability=clean(lib.get("bonus-name", "")), abilityDesc=clean(lib.get("bonus-description", "")),
            agenda=clean(lib.get("agenda-name", "")), agendaDesc=clean(lib.get("agenda-description", "")),
            quote=clean(lib.get("quote", "")),
            uniques=[uniques[u] for u in l.get("_uniques", []) if u in uniques],
        ))
    slug = re.sub(r"[^a-z0-9]+", "-", c["name"].lower().encode("ascii", "ignore").decode()).strip("-")
    out.append(dict(
        id="civ-" + slug, kind="civ", name=c["name"], adjective=c.get("adjective", ""), dlc=c.get("dlc", ""),
        real=c.get("real", ""), capital=c.get("capital", ""), place=c.get("place", ""), lat=c["lat"], lng=c["lng"],
        when=c.get("when", ""), history=c.get("history", ""), wonders=c.get("wonders", []),
        icon=cp.get("image"), civUrl=cp.get("url"),
        ability=clean(ib.get("ability-name", "")), abilityDesc=clean(ib.get("ability-description", "")),
        uniques=[uniques[u] for u in c.get("_uniques", []) if u in uniques],
        leaders=leaders,
        wikiTitle=wp["title"] if wp else "", wikiUrl=(wp or {}).get("fullurl", ""), photos=photos,
    ))

out.sort(key=lambda x: x["name"])
js = "/* Generated by civ_build.py: civilization data from the Civilization Wiki, photos from Wikimedia Commons. */\n"
js += "window.CIV6_CIVS = " + json.dumps(out, ensure_ascii=False, indent=0) + ";\n"
open(out_p, "w").write(js)
print(f"wrote {out_p}: {len(out)} civs, {sum(len(c['leaders']) for c in out)} leaders, {len(uniques)} uniques, "
      f"{sum(len(c['photos']) for c in out)} photos, {os.path.getsize(out_p)//1024} KB")
