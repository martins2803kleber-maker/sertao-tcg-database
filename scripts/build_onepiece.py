import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PRIMARY=ROOT/'source'/'optcg'
SECONDARY=ROOT/'source'/'apitcg'
SECONDARY_CARDS=SECONDARY/'cards'/'en'
OUT_DIR=ROOT/'data'; OUT_FILE=OUT_DIR/'onepiece.json'


def as_list(v):
    if isinstance(v,list): return [str(x).strip() for x in v if str(x).strip()]
    if v is None: return []
    t=str(v).strip(); return [t] if t else []

def to_int(v):
    if v in (None,'','-'): return None
    try: return int(str(v).replace('+','').strip())
    except Exception: return v

def pack_titles(lang):
    file=PRIMARY/lang/'packs.json'; out={}
    if not file.exists(): return out
    try: packs=json.loads(file.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'Could not parse {file}: {exc}'); return out
    it=packs.values() if isinstance(packs,dict) else packs if isinstance(packs,list) else []
    for p in it:
        if not isinstance(p,dict): continue
        pid=str(p.get('id','')).strip(); tp=p.get('title_parts') or {}
        out[pid]=tp.get('title') or tp.get('label') or p.get('raw_title') or pid
    return out

def normalize_primary(raw, lang, titles):
    original_id=str(raw.get('id','')).strip(); pack_id=str(raw.get('pack_id','')).strip()
    image=raw.get('img_full_url') or raw.get('img_url') or ''
    if image and image.startswith('/'):
        image=('https://www.onepiece-cardgame.com' if lang=='japanese' else 'https://en.onepiece-cardgame.com')+image
    code=original_id if lang=='english' else f'JP:{original_id}'
    return {
        'id':code,'originalId':original_id,'baseId':original_id.split('_',1)[0].strip(),'language':'en' if lang=='english' else 'ja',
        'name':str(raw.get('name','')).strip(),'packId':pack_id,'pack':titles.get(pack_id,pack_id),'packLabel':titles.get(pack_id,pack_id),
        'rarity':str(raw.get('rarity','') or '').strip(),'category':str(raw.get('category','') or '').strip(),'colors':as_list(raw.get('colors')),
        'cost':to_int(raw.get('cost')),'power':to_int(raw.get('power')),'counter':to_int(raw.get('counter')),'attributes':as_list(raw.get('attributes')),'types':as_list(raw.get('types')),
        'effect':str(raw.get('effect','') or '').strip(),'trigger':str(raw.get('trigger','') or '').strip(),'image':str(image or '').strip(),
        'source':f'Kuroro1990/OPTCG {lang}'
    }

def normalize_secondary(raw, source_file):
    images=raw.get('images') or {}; attribute=raw.get('attribute') or {}; set_info=raw.get('set') or {}
    card_id=str(raw.get('id') or raw.get('code') or '').strip(); base_id=str(raw.get('code') or card_id.split('_',1)[0]).strip()
    category=str(raw.get('type','') or '').strip().title(); color=str(raw.get('color','') or '').strip(); family=str(raw.get('family','') or '').strip()
    attr_name=str(attribute.get('name','') or '').strip() if isinstance(attribute,dict) else str(attribute or '').strip()
    pack_name=str(set_info.get('name','') or '').strip() if isinstance(set_info,dict) else str(set_info or '').strip(); pack_id=source_file.stem.upper()
    return {'id':card_id,'originalId':card_id,'baseId':base_id,'language':'en','name':str(raw.get('name','') or '').strip(),'packId':pack_id,'pack':pack_name or pack_id,'packLabel':pack_name or pack_id,
        'rarity':str(raw.get('rarity','') or '').strip(),'category':'DON!!' if category.upper()=='DON!!' else category,'colors':[color] if color else [],'cost':to_int(raw.get('cost')),'power':to_int(raw.get('power')),'counter':to_int(raw.get('counter')),
        'attributes':[attr_name] if attr_name else [],'types':[x.strip() for x in family.replace('/','|').split('|') if x.strip()],'effect':str(raw.get('ability','') or '').replace('<br>','\n').strip(),'trigger':str(raw.get('trigger','') or '').replace('<br>','\n').strip(),
        'image':str(images.get('large') or images.get('small') or '').strip(),'source':'apitcg/one-piece-tcg-data'}

def quality(c): return sum(bool(c.get(k)) for k in ('image','effect','pack','types','attributes'))
def merge(a,b):
    if not a: return b
    p,o=(a,b) if quality(a)>=quality(b) else (b,a); m=dict(p)
    for k in ('name','packId','pack','packLabel','rarity','category','effect','trigger','image','baseId','originalId'):
        if not m.get(k) and o.get(k): m[k]=o[k]
    for k in ('cost','power','counter'):
        if m.get(k) is None and o.get(k) is not None: m[k]=o[k]
    for k in ('colors','attributes','types'):
        vals=[]
        for x in as_list(m.get(k))+as_list(o.get(k)):
            if x not in vals: vals.append(x)
        m[k]=vals
    src=[]
    for s in (a.get('source'),b.get('source')):
        if s and s not in src: src.append(s)
    m['source']=' + '.join(src); return m

def add(store,card):
    if not card.get('id') or not card.get('name'): return
    store[card['id']]=merge(store.get(card['id']),card)

def main():
    store={}; counts={}
    for lang in ('english','japanese'):
        cards_dir=PRIMARY/lang/'cards'; titles=pack_titles(lang); n=0
        if not cards_dir.exists():
            print(f'Missing {cards_dir}'); continue
        for file in sorted(cards_dir.rglob('*.json')):
            try: parsed=json.loads(file.read_text(encoding='utf-8'))
            except Exception as exc:
                print(f'Skipping {file}: {exc}'); continue
            rows=[parsed] if isinstance(parsed,dict) else parsed if isinstance(parsed,list) else []
            for raw in rows:
                if not isinstance(raw,dict): continue
                card=normalize_primary(raw,lang,titles)
                if card.get('id') and card.get('name'): n+=1; add(store,card)
        counts[lang]=n
    sec=0
    if SECONDARY_CARDS.exists():
        for file in sorted(SECONDARY_CARDS.glob('*.json')):
            try: parsed=json.loads(file.read_text(encoding='utf-8'))
            except Exception as exc:
                print(f'Skipping {file}: {exc}'); continue
            rows=[parsed] if isinstance(parsed,dict) else parsed if isinstance(parsed,list) else []
            for raw in rows:
                if not isinstance(raw,dict): continue
                card=normalize_secondary(raw,file)
                if card.get('id') and card.get('name'): sec+=1; add(store,card)
    counts['secondaryEnglish']=sec
    cards=list(store.values()); cards.sort(key=lambda c:(c.get('language',''),c['name'].casefold(),c.get('baseId',''),c.get('id','')))
    def uniq(vals): return sorted({str(v).strip() for v in vals if str(v).strip()},key=str.casefold)
    meta={'languages':uniq(c.get('language','') for c in cards),'colors':uniq(x for c in cards for x in c['colors']),'categories':uniq(c['category'] for c in cards),'rarities':uniq(c['rarity'] for c in cards),'attributes':uniq(x for c in cards for x in c['attributes']),'types':uniq(x for c in cards for x in c['types']),'packs':uniq(c['pack'] for c in cards)}
    counts['mergedSearchableRecords']=len(cards)
    payload={'source':'Kuroro1990/OPTCG English+Japanese + apitcg English','language':'en/ja','count':len(cards),'coverage':counts,'meta':meta,'cards':cards}
    OUT_DIR.mkdir(parents=True,exist_ok=True); OUT_FILE.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Wrote {len(cards)} One Piece searchable records'); print(counts)

if __name__=='__main__': main()
