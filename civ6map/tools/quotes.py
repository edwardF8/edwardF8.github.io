import json, sys, re, urllib.parse, urllib.request, time
parsed = json.load(open(sys.argv[1])); natural = json.load(open(sys.argv[2])); out = sys.argv[3]
names = [w["name"] for w in parsed["wonders"]] + [n["name"] for n in natural]
res = {}
for i in range(0, len(names), 45):
    batch = names[i:i+45]
    titles = [n + " (Civ6)" for n in batch]
    url = "https://civilization.fandom.com/api.php?" + urllib.parse.urlencode(dict(action="query", format="json", redirects=1, prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles)))
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "civ6map-local/1.0"}), timeout=60).read())
    q = d["query"]; norm = {x["from"]: x["to"] for x in q.get("normalized", [])}; red = {x["from"]: x["to"] for x in q.get("redirects", [])}
    pages = {p["title"]: p for p in q["pages"].values()}
    for n, t in zip(batch, titles):
        t2 = norm.get(t, t); p = pages.get(red.get(t2, t2))
        if not p or "revisions" not in p: res[n] = None; continue
        txt = p["revisions"][0]["slots"]["main"]["*"]
        fields = dict(re.findall(r"^\|\s*(quote\d?|quoted\d?)\s*=\s*(.*?)\s*$", txt, re.M))
        res[n] = fields
    time.sleep(1)
def clean(s):
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s or ""); s = re.sub(r"<br\s*/?>", "\n", s); s = re.sub(r"'''?", "", s); s = re.sub(r"<[^>]+>", "", s)
    return s.strip()
final = {}
for n, f in res.items():
    if not f: print("no page/fields:", n); continue
    qs = []
    for k in ["", "2", "3"]:
        if f.get("quote"+k): qs.append(dict(text=clean(f["quote"+k]), by=clean(f.get("quoted"+k, ""))))
    final[n] = qs
    print(f"{n:32} {len(qs)} | " + " || ".join(f"{q['text'][:70]} — {q['by']}" for q in qs))
json.dump(final, open(out, "w"), ensure_ascii=False, indent=1)
