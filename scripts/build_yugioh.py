import json
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'data'
OUT_FILE = OUT_DIR / 'yugioh.json'
JA_CDB = ROOT / 'source' / 'yugioh-ja' / 'cards.cdb'
API_EN = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes'
API_PT = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes'


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'SertaoTCG/5.0'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def normalize_en(raw, localized=None, artwork=None, artwork_index=0):
    localized = localized or {}
    misc = (raw.get('misc_info') or [{}])[0] or {}
    sets = raw.get('card_sets') or []
    first = sets[0] if sets else {}
    artwork = artwork or ((raw.get('card_images') or [{}])[0] or {})
    base_id = raw.get('id')
    image_id = artwork.get('id') or base_id
    nsets = [
        {
            'name': s.get('set_name', ''),
            'code': s.get('set_code', ''),
            'rarity': s.get('set_rarity', ''),
            'rarityCode': s.get('set_rarity_code', ''),
            'price': s.get('set_price', ''),
        }
        for s in sets if isinstance(s, dict)
    ]
    return {
        'id': image_id,
        'originalId': base_id,
        'baseId': base_id,
        'language': 'en',
        'languages': ['en'],
        'variantId': f'{base_id}:{image_id}:{artwork_index}',
        'artworkIndex': artwork_index,
        'isAltArt': artwork_index > 0 or str(image_id) != str(base_id),
        'konamiId': misc.get('konami_id'),
        'name': localized.get('name') or raw.get('name', ''),
        'nameEn': raw.get('name', ''),
        'nameJa': '',
        'type': raw.get('type', ''),
        'frameType': raw.get('frameType', ''),
        'race': raw.get('race', ''),
        'attribute': raw.get('attribute', ''),
        'level': raw.get('level'),
        'rank': raw.get('level') if 'XYZ' in str(raw.get('type', '')).upper() else None,
        'linkval': raw.get('linkval'),
        'linkmarkers': raw.get('linkmarkers') or [],
        'scale': raw.get('scale'),
        'atk': raw.get('atk'),
        'def': raw.get('def'),
        'desc': localized.get('desc') or raw.get('desc', ''),
        'descEn': raw.get('desc', ''),
        'descJa': '',
        'pendDesc': localized.get('pend_desc') or raw.get('pend_desc', ''),
        'monsterDesc': localized.get('monster_desc') or raw.get('monster_desc', ''),
        'archetype': raw.get('archetype', ''),
        'set': first.get('set_name', ''),
        'setCode': first.get('set_code', ''),
        'rarity': first.get('set_rarity', ''),
        'sets': nsets,
        'image': artwork.get('image_url', ''),
        'imageSmall': artwork.get('image_url_small', ''),
        'imageCropped': artwork.get('image_url_cropped', ''),
        'tcgDate': misc.get('tcg_date', ''),
        'ocgDate': misc.get('ocg_date', ''),
        'formats': misc.get('formats') or [],
        'source': 'YGOPRODeck',
    }


def read_japanese_cards():
    if not JA_CDB.exists():
        print('Japanese CDB missing')
        return []
    con = sqlite3.connect(str(JA_CDB))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        'SELECT t.id,t.name,t.desc,d.type,d.atk,d.def,d.level,d.race,d.attribute,d.ot,d.alias '
        'FROM texts t LEFT JOIN datas d ON d.id=t.id'
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        cid = r['id']
        if cid is None or not str(r['name'] or '').strip():
            continue
        raw_level = r['level'] or 0
        level = (raw_level & 0xff) if isinstance(raw_level, int) else None
        out.append({
            'id': cid,
            'originalId': cid,
            'baseId': cid,
            'language': 'ja',
            'languages': ['ja'],
            'variantId': f'JP:{cid}:0',
            'artworkIndex': 0,
            'isAltArt': False,
            'konamiId': None,
            'name': str(r['name'] or '').strip(),
            'nameEn': '',
            'nameJa': str(r['name'] or '').strip(),
            'type': '',
            'frameType': '',
            'race': '',
            'attribute': '',
            'level': level,
            'rank': None,
            'linkval': None,
            'linkmarkers': [],
            'scale': None,
            'atk': r['atk'],
            'def': r['def'],
            'desc': str(r['desc'] or '').strip(),
            'descEn': '',
            'descJa': str(r['desc'] or '').strip(),
            'pendDesc': '',
            'monsterDesc': '',
            'archetype': '',
            'set': '',
            'setCode': '',
            'rarity': '',
            'sets': [],
            'image': f'https://images.ygoprodeck.com/images/cards/{cid}.jpg',
            'imageSmall': f'https://images.ygoprodeck.com/images/cards_small/{cid}.jpg',
            'imageCropped': f'https://images.ygoprodeck.com/images/cards_cropped/{cid}.jpg',
            'tcgDate': '',
            'ocgDate': '',
            'formats': ['OCG'],
            'source': 'mycard/ygopro-database ja-JP',
            'rawType': r['type'],
            'rawRace': r['race'],
            'rawAttribute': r['attribute'],
            'ot': r['ot'],
            'alias': r['alias'],
        })
    return out


def overlay_japanese(en_record, jp):
    merged = dict(en_record)
    langs = list(merged.get('languages') or ['en'])
    if 'ja' not in langs:
        langs.append('ja')
    merged['languages'] = langs
    merged['nameJa'] = jp.get('nameJa') or jp.get('name', '')
    merged['descJa'] = jp.get('descJa') or jp.get('desc', '')
    sources = []
    for s in str(merged.get('source', '')).split(' + ') + str(jp.get('source', '')).split(' + '):
        if s and s not in sources:
            sources.append(s)
    merged['source'] = ' + '.join(sources)
    return merged


def enrich_japanese_only(jp, en_by_id):
    # Alias can point to the canonical card ID in some OCG databases.
    alias = jp.get('alias')
    src = en_by_id.get(str(alias)) if alias not in (None, 0, '0') else None
    if not src:
        return jp
    for k in ('nameEn', 'type', 'frameType', 'race', 'attribute', 'rank', 'linkval', 'linkmarkers', 'scale', 'archetype', 'set', 'setCode', 'rarity', 'sets', 'tcgDate', 'ocgDate'):
        if not jp.get(k) and src.get(k):
            jp[k] = src[k]
    if jp.get('level') in (None, 0) and src.get('level') is not None:
        jp['level'] = src['level']
    if jp.get('atk') is None:
        jp['atk'] = src.get('atk')
    if jp.get('def') is None:
        jp['def'] = src.get('def')
    return jp


def main():
    en_cards = get_json(API_EN).get('data') or []
    if not en_cards:
        raise SystemExit('YGOPRODeck English database returned no cards')

    pt = {}
    try:
        for c in get_json(API_PT).get('data') or []:
            if c.get('id') is not None:
                pt[str(c.get('id'))] = c
    except Exception as exc:
        print(f'Portuguese overlay unavailable: {exc}')

    cards = []
    alt = 0
    en_by_id = {}
    indexes_by_base = {}

    for raw in en_cards:
        loc = pt.get(str(raw.get('id')), {})
        images = raw.get('card_images') or [{}]
        base_norm = normalize_en(raw, loc, images[0], 0)
        base_key = str(raw.get('id'))
        en_by_id[base_key] = base_norm
        indexes_by_base[base_key] = []
        for idx, img in enumerate(images):
            c = normalize_en(raw, loc, img, idx)
            if c['name']:
                indexes_by_base[base_key].append(len(cards))
                cards.append(c)
                if c['isAltArt']:
                    alt += 1

    jp_all = read_japanese_cards()
    jp_only = []
    merged_language = 0

    for jp in jp_all:
        base_key = str(jp.get('baseId'))
        if base_key in indexes_by_base:
            # Same Konami card: keep one searchable printing per artwork, add JA metadata.
            for index in indexes_by_base[base_key]:
                cards[index] = overlay_japanese(cards[index], jp)
            merged_language += 1
        else:
            jp_only.append(enrich_japanese_only(jp, en_by_id))

    # Only genuinely OCG-only cards are appended as separate searchable records.
    cards.extend(jp_only)
    cards.sort(key=lambda c: (str(c.get('name', '')).casefold(), str(c.get('baseId', '')), c.get('artworkIndex', 0)))

    coverage = {
        'englishCards': len(en_cards),
        'portugueseOverlay': len(pt),
        'englishArtworkRecords': len(cards) - len(jp_only),
        'japaneseCdbRecords': len(jp_all),
        'japaneseDuplicatesMerged': merged_language,
        'japaneseOnlyUniqueCards': len(jp_only),
        'artworkVariants': alt,
        'totalSearchableRecords': len(cards),
    }
    payload = {
        'source': 'YGOPRODeck EN artworks + PT overlay + mycard/ygopro-database ja-JP (language-deduplicated)',
        'language': 'en preferred with ja metadata / OCG-only unique records',
        'count': len(cards),
        'uniqueEnglishCards': len(en_cards),
        'japaneseRecords': len(jp_all),
        'artworkVariants': alt,
        'coverage': coverage,
        'cards': cards,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(
        f"Wrote {len(cards)} Yu-Gi-Oh unique searchable records: "
        f"EN artworks={len(cards)-len(jp_only)}, JP-only={len(jp_only)}, "
        f"JP merged={merged_language}, alt={alt}"
    )
    print(coverage)


if __name__ == '__main__':
    main()
