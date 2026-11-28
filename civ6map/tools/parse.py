import re, json, sys
src_w, src_n, out = sys.argv[1], sys.argv[2], sys.argv[3]

ICON = {
 'Faith6':'{Faith}','Science6':'{Science}','Culture6':'{Culture}','Gold6':'{Gold}','Production6':'{Production}',
 'Food6':'{Food}','Amenities6':'{Amenity}','Amenity6':'{Amenity}','Housing6':'{Housing}','Tourism6':'{Tourism}',
 'TourismIcon6':'{Tourism}','Citizen6':'{Citizen}','CitizenIcon6':'{Citizen}','Envoys6':'{Envoy}','Capital6':'Capital',
 'Scientist6':'Great Scientist','Writer6':'Great Writer','Musician6':'Great Musician','Merchant6':'Great Merchant',
 'Admiral6':'Great Admiral','General6':'Great General','Prophet6':'Great Prophet','Engineer6':'Great Engineer','Artist6':'Great Artist',
 'GreatWorkWriting6':'Great Work of Writing','Music6':'Great Work of Music','Writing6':'Writing','Relic6':'Relic','RelicIcon6':'Relic',
 'TradeRoute6':'{TradeRoute}','Power6':'{Power}','Movement6':'{Movement}','Iron6':'Iron','Stone6':'Stone','Cattle6':'Cattle',
 'MilitaryPolicy6':'','EconomicPolicy6':'','DiplomaticPolicy6':'','WildcardSlot6':'','DiplomaticFavor6':'{Favor}',
 'ReligiousStrengthIcon6':'Religious Strength','Promotion6':'promotion','Lifespan6':'','Landscape6':'','BuildChargesIcon6':'',
 'Strength6':'{Strength}','StrengthIcon6':'{Strength}','District6':'district','ProductionIcon6':'{Production}',
 'GS':'[GS]','R&F':'[R&F]','RiseandFall':'Rise and Fall','GatheringStorm':'Gathering Storm','Civ6':'Civilization VI',
}
def clean(s):
    s = re.sub(r'<ref[^>]*/>', '', s)
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    def tpl(m):
        body = m.group(1)
        parts = body.split('|')
        name = parts[0].strip()
        if name in ICON: return ICON[name]
        if name.startswith('SurePageIcon'): return parts[1]
        if len(parts) > 1: return parts[-1]
        return name
    for _ in range(3):
        s = re.sub(r'\{\{([^{}]*)\}\}', tpl, s)
    s = re.sub(r"'''?", '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def bullets(s):
    s = clean(s)
    items = [re.sub(r'^\*+\s*', '', l).strip() for l in s.split('\n')]
    return [i for i in items if i]

def expansion(cell):
    if '{{GS}}' in cell.split('|',1)[-1][:200] and 'SurePage' in cell: pass
    m = re.search(r'<ref[^>]*>(.*?)</ref>', cell, re.S)
    if m:
        t = clean(m.group(1)); t = re.sub(r'^(Added in|Available with the|Available in the)\s*', '', t); t = re.sub(r'\s*DLC$','',t)
        return t
    head = cell
    if '{{GS}}' in head: return 'Gathering Storm'
    if '{{R&F}}' in head: return 'Rise and Fall'
    return 'Base game'

def split_rows(txt):
    body = txt.split('{|',1)[1].split('\n|}',1)[0]
    rows = re.split(r'\n\|-[^\n]*\n', body)
    return rows[1:]

def cells(row):
    out = []; cur = None
    for line in row.split('\n'):
        if line.startswith('|') and not line.startswith('|}') and not line.startswith('|+'):
            if cur is not None: out.append(cur)
            cur = line[1:]
        elif line.startswith('!'):
            return None
        else:
            if cur is not None: cur += '\n' + line
    if cur is not None: out.append(cur)
    # strip style attrs: 'style=... | content'
    res = []
    for c in out:
        m = re.match(r'\s*(?:style|data-sort-value|class)[^|]*?\|(?!\|)(.*)', c, re.S)
        if m and not c.strip().startswith('{{'): c = m.group(1)
        res.append(c)
    return res

named_refs = {}
def collect_refs(txt):
    for m in re.finditer(r'<ref name="?([^">/]+)"?\s*>(.*?)</ref>', txt, re.S):
        named_refs[m.group(1).strip()] = m.group(2)

def exp_from(cell):
    m = re.search(r'<ref name="?([^">/]+)"?\s*/>', cell)
    if m and m.group(1).strip() in named_refs:
        t = clean(named_refs[m.group(1).strip()])
    else:
        m = re.search(r'<ref[^>]*>(.*?)</ref>', cell, re.S)
        t = clean(m.group(1)) if m else None
    if t:
        t = re.sub(r'^(Added in( the)?|Available with the|Available in the|Available with)\s*', '', t); t = re.sub(r'\s*DLC\.?$','',t)
        return t
    if '{{GS}}' in cell: return 'Gathering Storm'
    if '{{R&F}}' in cell: return 'Rise and Fall'
    return 'Base game'

W = open(src_w).read(); N = open(src_n).read()
collect_refs(W); collect_refs(N)
wonders = []
for r in split_rows(W):
    c = cells(r)
    if not c or len(c) < 6: continue
    name = clean(re.sub(r'\{\{(GS|R&F)\}\}','',c[0])).strip()
    wonders.append(dict(name=name, expansion=exp_from(c[0]), era=clean(c[1]), req=clean(c[2]).replace('\n',' / '), cost=clean(c[3]), effects=bullets(c[4]), placement=clean(c[5])))
naturals = []
for r in split_rows(N):
    c = cells(r)
    if not c or len(c) < 4: continue
    name = clean(re.sub(r'\{\{(GS|R&F)\}\}','',c[0])).strip()
    naturals.append(dict(name=name, expansion=exp_from(c[0]), effects=[x for x in clean(c[1]).split('\n') if x.strip()], notes=clean(c[2]), size=clean(c[3]).replace('\n',' ')))
json.dump(dict(wonders=wonders, naturals=naturals), open(out,'w'), indent=1, ensure_ascii=False)
print(len(wonders), 'wonders;', len(naturals), 'natural')
for w in wonders: print('W', w['era'], '|', w['name'], '|', w['expansion'], '|', w['req'], '|', w['cost'])
for n in naturals: print('N', n['name'], '|', n['expansion'], '|', n['size'])
