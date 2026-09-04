#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

TYPE_LINK = 0x4000000
MASK64 = (1 << 64) - 1


def split_setcodes(raw):
    raw = int(raw or 0) & MASK64
    out = []
    for _ in range(4):
        sc = raw & 0xFFFF
        if sc:
            out.append(sc)
        raw >>= 16
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: build-duellab-core.py /path/to/BabelCDB')
    root = Path(sys.argv[1])
    canonical = root / 'cards.cdb'
    files = [canonical] if canonical.exists() else []
    for p in sorted(root.glob('*.cdb')):
        n = p.name.lower()
        if p == canonical or 'rush' in n or 'skill' in n or 'goat' in n:
            continue
        files.append(p)

    cards = {}
    for db in files:
        try:
            con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
            cols = {x[1] for x in con.execute('pragma table_info(datas)')}
            need = {'id','alias','setcode','type','atk','def','level','race','attribute'}
            if not need.issubset(cols):
                con.close()
                continue
            for row in con.execute('select id,alias,setcode,type,atk,def,level,race,attribute from datas'):
                cid, alias, setcode, ctype, atk, defense, levelraw, race, attribute = row
                cid = int(cid)
                ctype = int(ctype or 0)
                levelraw = int(levelraw or 0) & 0xFFFFFFFF
                defense = int(defense or 0)
                marker = 0
                if ctype & TYPE_LINK:
                    marker = defense & 0xFFFFFFFF
                    defense = 0
                cards[cid] = {
                    'id': cid,
                    'alias': int(alias or 0),
                    'setcode': split_setcodes(setcode),
                    'type': ctype,
                    'level': levelraw & 0xFF,
                    'attribute': int(attribute or 0) & 0xFFFFFFFF,
                    'race': int(race or 0) & MASK64,
                    'atk': int(atk or 0),
                    'def': defense,
                    'lscale': (levelraw >> 24) & 0xFF,
                    'rscale': (levelraw >> 16) & 0xFF,
                    'link_marker': marker,
                }
            con.close()
        except sqlite3.DatabaseError as exc:
            print('skip', db.name, exc)

    ordered = [cards[k] for k in sorted(cards)]
    if len(ordered) < 10000:
        raise SystemExit(f'core database unexpectedly small: {len(ordered)}')

    payload = json.dumps(ordered, separators=(',', ':'), ensure_ascii=False)
    for out in (Path('duellab/web/core/cards_core.json'), Path('assets/duellab/core/cards_core.json')):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding='utf-8')

    upstream = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip()
    manifest = {
        'source': 'ProjectIgnis/BabelCDB',
        'upstream': upstream,
        'cardCount': len(ordered),
        'databases': [p.name for p in files],
    }
    Path('duellab/web/core/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'generated {len(ordered)} cards from {len(files)} databases @ {upstream}')


if __name__ == '__main__':
    main()
