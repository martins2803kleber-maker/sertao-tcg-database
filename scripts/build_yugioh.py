import json
import sqlite3
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT_DIR=ROOT/'data'; OUT_FILE=OUT_DIR/'yugioh.json'
JA_CDB=ROOT/'source'/'yugioh-ja'/'cards.cdb'
API_EN='https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes'
API_PT='https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes'


def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SertaoTCG/4.0'})
    with urllib.request.urlopen(req,timeout=180) as r: return json.load(r)

def normalize_en(raw,localized=None,artwork=None,artwork_index=0):
    localized=localized or {}; misc=(raw.get('misc_info') or [{}])[0] or {}; sets=raw.get('card_sets') or []; first=sets[0] if sets else {}
    artwork=artwork or ((raw.get('card_images') or [{}])[0] or {}); base_id=raw.get('id'); image_id=artwork.get('id') or base_id
    nsets=[{'name':s.get('set_name',''),'code':s.get('set_code',''),'rarity':s.get('set_rarity',''),'rarityCode':s.get('set_rarity_code',''),'price':s.get('set_price','')} for s in sets if isinstance(s,dict)]
    return {'id':image_id,'originalId':base_id,'baseId':base_id,'language':'en','variantId':f'{base_id}:{image_id}:{artwork_index}','artworkIndex':artwork_index,'isAltArt':artwork_index>0 or str(image_id)!=str(base_id),
        'konamiId':misc.get('konami_id'),'name':localized.get('name') or raw.get('name',''),'nameEn':raw.get('name',''),'type':raw.get('type',''),'frameType':raw.get('frameType',''),'race':raw.get('race',''),'attribute':raw.get('attribute',''),
        'level':raw.get('level'),'rank':raw.get('level') if 'XYZ' in str(raw.get('type','')).upper() else None,'linkval':raw.get('linkval'),'linkmarkers':raw.get('linkmarkers') or [],'scale':raw.get('scale'),'atk':raw.get('atk'),'def':raw.get('def'),
        'desc':localized.get('desc') or raw.get('desc',''),'descEn':raw.get('desc',''),'pendDesc':localized.get('pend_desc') or raw.get('pend_desc',''),'monsterDesc':localized.get('monster_desc') or raw.get('monster_desc',''),'archetype':raw.get('archetype',''),
        'set':first.get('set_name',''),'setCode':first.get('set_code',''),'rarity':first.get('set_rarity',''),'sets':nsets,'image':artwork.get('image_url',''),'imageSmall':artwork.get('image_url_small',''),'imageCropped':artwork.get('image_url_cropped',''),
        'tcgDate':misc.get('tcg_date',''),'ocgDate':misc.get('ocg_date',''),'formats':misc.get('formats') or [],'source':'YGOPRODeck'}

def read_japanese_cards():
    if not JA_CDB.exists():
        print('Japanese CDB missing'); return []
    con=sqlite3.connect(str(JA_CDB)); con.row_factory=sqlite3.Row
    rows=con.execute('SELECT t.id,t.name,t.desc,d.type,d.atk,d.def,d.level,d.race,d.attribute,d.ot,d.alias FROM texts t LEFT JOIN datas d ON d.id=t.id').fetchall(); con.close()
    out=[]
    for r in rows:
        cid=r['id']
        if cid is None or not str(r['name'] or '').strip(): continue
        raw_level=r['level'] or 0
        level=(raw_level & 0xff) if isinstance(raw_level,int) else None
        out.append({'id':f'JP:{cid}','originalId':cid,'baseId':cid,'language':'ja','variantId':f'JP:{cid}:0','artworkIndex':0,'isAltArt':False,'konamiId':None,
            'name':str(r['name'] or '').strip(),'nameEn':'','type':'','frameType':'','race':'','attribute':'','level':level,'rank':None,'linkval':None,'linkmarkers':[],'scale':None,'atk':r['atk'],'def':r['def'],
            'desc':str(r['desc'] or '').strip(),'descEn':'','pendDesc':'','monsterDesc':'','archetype':'','set':'','setCode':'','rarity':'','sets':[],
            'image':f'https://images.ygoprodeck.com/images/cards/{cid}.jpg','imageSmall':f'https://images.ygoprodeck.com/images/cards_small/{cid}.jpg','imageCropped':f'https://images.ygoprodeck.com/images/cards_cropped/{cid}.jpg',
            'tcgDate':'','ocgDate':'','formats':['OCG'],'source':'mycard/ygopro-database ja-JP','rawType':r['type'],'rawRace':r['race'],'rawAttribute':r['attribute'],'ot':r['ot'],'alias':r['alias']})
    return out

def enrich_japanese(jp,en_by_id):
    src=en_by_id.get(str(jp.get('originalId')))
    if not src: return jp
    for k in ('nameEn','type','frameType','race','attribute','rank','linkval','linkmarkers','scale','archetype','set','setCode','rarity','sets','tcgDate','ocgDate'):
        if not jp.get(k) and src.get(k): jp[k]=src[k]
    if jp.get('level') in (None,0) and src.get('level') is not None: jp['level']=src['level']
    if jp.get('atk') is None: jp['atk']=src.get('atk')
    if jp.get('def') is None: jp['def']=src.get('def')
    return jp

def main():
    en_cards=get_json(API_EN).get('data') or []
    if not en_cards: raise SystemExit('YGOPRODeck English database returned no cards')
    pt={}
    try:
        for c in get_json(API_PT).get('data') or []:
            if c.get('id') is not None: pt[str(c.get('id'))]=c
    except Exception as exc: print(f'Portuguese overlay unavailable: {exc}')
    cards=[]; alt=0; en_by_id={}
    for raw in en_cards:
        loc=pt.get(str(raw.get('id')),{})
        images=raw.get('card_images') or [{}]
        base_norm=normalize_en(raw,loc,images[0],0); en_by_id[str(raw.get('id'))]=base_norm
        for idx,img in enumerate(images):
            c=normalize_en(raw,loc,img,idx)
            if c['name']:
                cards.append(c)
                if c['isAltArt']: alt+=1
    jp_cards=[enrich_japanese(c,en_by_id) for c in read_japanese_cards()]
    cards.extend(jp_cards)
    cards.sort(key=lambda c:(c.get('language',''),str(c.get('name','')).casefold(),str(c.get('baseId','')),c.get('artworkIndex',0)))
    payload={'source':'YGOPRODeck EN artworks + PT overlay + mycard/ygopro-database ja-JP','language':'en/ja/pt-overlay','count':len(cards),'uniqueEnglishCards':len(en_cards),'japaneseRecords':len(jp_cards),'artworkVariants':alt,
        'coverage':{'englishCards':len(en_cards),'portugueseOverlay':len(pt),'englishArtworkRecords':len(cards)-len(jp_cards),'japaneseCdbRecords':len(jp_cards),'totalSearchableRecords':len(cards)},'cards':cards}
    OUT_DIR.mkdir(parents=True,exist_ok=True); OUT_FILE.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Wrote {len(cards)} Yu-Gi-Oh searchable records: EN artworks={len(cards)-len(jp_cards)}, JP={len(jp_cards)}, alt={alt}')

if __name__=='__main__': main()
