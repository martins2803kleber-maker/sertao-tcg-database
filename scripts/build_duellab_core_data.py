#!/usr/bin/env python3
import argparse, json, sqlite3
from pathlib import Path


def parse_ydk(path: Path):
    main, extra, side = [], [], []
    zone = main
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#created by'):
            continue
        if line == '#main':
            zone = main; continue
        if line == '#extra':
            zone = extra; continue
        if line == '!side':
            zone = side; continue
        if line.startswith('#'):
            continue
        try: zone.append(int(line))
        except ValueError: pass
    return {'main': main, 'extra': extra, 'side': side}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cdb', required=True)
    ap.add_argument('--windbot', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(args.cdb)
    rows = db.execute('SELECT id,ot,alias,setcode,type,atk,def,level,race,attribute FROM datas').fetchall()
    cards=[]
    for r in rows:
        cards.append({'id':int(r[0]),'alias':int(r[2] or 0),'setcode':str(int(r[3] or 0)),
                      'type':int(r[4] or 0),'atk':int(r[5] or 0),'def':int(r[6] or 0),
                      'level':int(r[7] or 0),'race':str(int(r[8] or 0)),'attribute':int(r[9] or 0)})
    (out/'cards_core.json').write_text(json.dumps(cards,separators=(',',':')),encoding='utf-8')

    names={int(i):{'name':n or '', 'desc':d or ''} for i,n,d in db.execute('SELECT id,name,desc FROM texts')}
    (out/'cards_text_en.json').write_text(json.dumps(names,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    db.close()

    deck_dir=Path(args.windbot)/'Decks'
    picks=['AI_BlueEyes.ydk','AI_ABC.ydk','AI_DarkMagician.ydk','AI_SkyStriker.ydk','AI_CyberDragon.ydk','AI_Kashtira.ydk']
    decks={}
    for fn in picks:
        p=deck_dir/fn
        if p.exists(): decks[fn.replace('AI_','').replace('.ydk','')]=parse_ydk(p)
    if not decks:
        for p in list(deck_dir.glob('*.ydk'))[:12]: decks[p.stem]=parse_ydk(p)
    (out/'bot_decks.json').write_text(json.dumps(decks,separators=(',',':')),encoding='utf-8')

if __name__=='__main__': main()
