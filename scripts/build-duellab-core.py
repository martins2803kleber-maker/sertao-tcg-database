#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

TYPE_LINK = 0x4000000
MASK64 = (1 << 64) - 1


def u64_string(value):
    """Serialize 64-bit CDB integers exactly as the current Rust/WASM bridge expects."""
    return str(int(value or 0) & MASK64)


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

                # IMPORTANT: this JSON is consumed by CardRecordInput in duellab/engine.
                # The bridge currently expects setcode/race as strings and level as the
                # packed CDB value (level + pendulum scales). For Link monsters, CDB
                # stores link markers in the DEF column and the bridge derives them.
                cards[cid] = {
                    'id': cid,
                    'alias': int(alias or 0),
                    'setcode': u64_string(setcode),
                    'type': ctype,
                    'atk': int(atk or 0),
                    'def': defense,
                    'level': levelraw,
                    'race': u64_string(race),
                    'attribute': int(attribute or 0) & 0xFFFFFFFF,
                }
            con.close()
        except sqlite3.DatabaseError as exc:
            print('skip', db.name, exc)

    ordered = [cards[k] for k in sorted(cards)]
    if len(ordered) < 10000:
        raise SystemExit(f'core database unexpectedly small: {len(ordered)}')

    # Validate the exact Rust bridge contract before publishing anything.
    required = {'id','alias','setcode','type','atk','def','level','race','attribute'}
    for card in ordered:
        if set(card) != required:
            raise SystemExit(f'invalid card schema for {card.get("id")}: {sorted(card)}')
        if not isinstance(card['setcode'], str) or not isinstance(card['race'], str):
            raise SystemExit(f'bridge string fields invalid for {card["id"]}')
        if not all(isinstance(card[k], int) for k in ('id','alias','type','atk','def','level','attribute')):
            raise SystemExit(f'bridge numeric fields invalid for {card["id"]}')

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
        'bridgeSchema': 'CardRecordInput-v1',
    }
    Path('duellab/web/core/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'generated {len(ordered)} cards from {len(files)} databases @ {upstream}')


if __name__ == '__main__':
    main()
