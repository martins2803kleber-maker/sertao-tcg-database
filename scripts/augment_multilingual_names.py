import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TCGDEX_BASE = 'https://api.tcgdex.net/v2'
YGO_PT = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes'


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'SertaoTCG/8.0 multilingual-name-updater'})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def fetch_tcgdex_cards(lang):
    cards = []
    page = 1
    per_page = 1000
    while page <= 100:
        query = urllib.parse.urlencode({'pagination:page': page, 'pagination:itemsPerPage': per_page})
        batch = get_json(f'{TCGDEX_BASE}/{lang}/cards?{query}')
        if not isinstance(batch, list) or not batch:
            break
        cards.extend(batch)
        print(f'TCGdex {lang} page {page}: {len(batch)} cards')
        if len(batch) < per_page:
            break
        page += 1
    return cards


def save_payload(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def augment_pokemon():
    path = ROOT / 'data' / 'pokemon.json'
    payload = json.loads(path.read_text(encoding='utf-8'))
    cards = payload.get('cards') or []

    pt_map = {}
    try:
        for raw in fetch_tcgdex_cards('pt-br'):
            if not isinstance(raw, dict):
                continue
            cid = str(raw.get('id', '') or '').strip()
            name = str(raw.get('name', '') or '').strip()
            if cid and name:
                pt_map[cid] = name
    except Exception as exc:
        print(f'Pokemon PT-BR overlay unavailable: {exc}')

    en_map = {}
    try:
        for raw in fetch_tcgdex_cards('en'):
            if not isinstance(raw, dict):
                continue
            cid = str(raw.get('id', '') or '').strip()
            name = str(raw.get('name', '') or '').strip()
            if cid and name:
                en_map[cid] = name
    except Exception as exc:
        print(f'Pokemon EN overlay unavailable: {exc}')

    pt_count = 0
    en_count = 0
    ja_count = 0
    for card in cards:
        cid = str(card.get('originalId') or card.get('id') or '').strip()
        lang = str(card.get('language', '') or '').strip()
        current = str(card.get('name', '') or '').strip()
        langs = card.get('languages') or ([lang] if lang else [])

        name_en = str(card.get('nameEn', '') or '').strip()
        if not name_en:
            if cid in en_map:
                name_en = en_map[cid]
            elif 'en' in langs or lang == 'en':
                name_en = current

        name_pt = str(card.get('namePt', '') or '').strip() or pt_map.get(cid, '')
        name_ja = str(card.get('nameJa', '') or '').strip()
        if not name_ja and (lang == 'ja' or ('ja' in langs and 'en' not in langs)):
            name_ja = current

        card['nameEn'] = name_en
        card['namePt'] = name_pt
        card['nameJa'] = name_ja
        if name_pt:
            pt_count += 1
        if name_en:
            en_count += 1
        if name_ja:
            ja_count += 1

        # Prefer Brazilian Portuguese for the visible primary name when available,
        # but keep English/Japanese alongside it so search/display can use all names.
        if name_pt:
            card['name'] = name_pt
        elif name_en:
            card['name'] = name_en
        elif name_ja:
            card['name'] = name_ja

    coverage = payload.setdefault('coverage', {})
    coverage['namePtRecords'] = pt_count
    coverage['nameEnRecords'] = en_count
    coverage['nameJaRecords'] = ja_count
    payload['nameDisplayPolicy'] = 'pt-BR preferred, then en, then ja; all names retained for search'
    save_payload(path, payload)
    print(f'Pokemon multilingual names: PT={pt_count}, EN={en_count}, JA={ja_count}, total={len(cards)}')


def augment_yugioh():
    path = ROOT / 'data' / 'yugioh.json'
    payload = json.loads(path.read_text(encoding='utf-8'))
    cards = payload.get('cards') or []

    pt_map = {}
    try:
        for raw in get_json(YGO_PT).get('data') or []:
            if not isinstance(raw, dict):
                continue
            cid = str(raw.get('id', '') or '').strip()
            name = str(raw.get('name', '') or '').strip()
            if cid and name:
                pt_map[cid] = name
    except Exception as exc:
        print(f'Yu-Gi-Oh PT overlay unavailable: {exc}')

    pt_count = 0
    en_count = 0
    ja_count = 0
    for card in cards:
        base_id = str(card.get('baseId') or card.get('originalId') or card.get('id') or '').strip()
        name_en = str(card.get('nameEn', '') or '').strip()
        if not name_en and str(card.get('language', '')) == 'en':
            name_en = str(card.get('name', '') or '').strip()
        name_pt = str(card.get('namePt', '') or '').strip() or pt_map.get(base_id, '')
        name_ja = str(card.get('nameJa', '') or '').strip()
        if not name_ja and str(card.get('language', '')) == 'ja':
            name_ja = str(card.get('name', '') or '').strip()

        card['nameEn'] = name_en
        card['namePt'] = name_pt
        card['nameJa'] = name_ja
        if name_pt:
            pt_count += 1
        if name_en:
            en_count += 1
        if name_ja:
            ja_count += 1

        if name_pt:
            card['name'] = name_pt
        elif name_en:
            card['name'] = name_en
        elif name_ja:
            card['name'] = name_ja

    coverage = payload.setdefault('coverage', {})
    coverage['namePtRecords'] = pt_count
    coverage['nameEnRecords'] = en_count
    coverage['nameJaRecords'] = ja_count
    payload['nameDisplayPolicy'] = 'pt preferred when YGOPRODeck provides it, then en, then ja; all names retained for search'
    save_payload(path, payload)
    print(f'Yu-Gi-Oh multilingual names: PT={pt_count}, EN={en_count}, JA={ja_count}, total={len(cards)}')


def augment_onepiece():
    path = ROOT / 'data' / 'onepiece.json'
    payload = json.loads(path.read_text(encoding='utf-8'))
    cards = payload.get('cards') or []

    en_count = 0
    ja_count = 0
    pt_count = 0
    for card in cards:
        langs = card.get('languages') or [card.get('language', '')]
        current = str(card.get('name', '') or '').strip()
        name_ja = str(card.get('nameJa', '') or '').strip()
        name_en = str(card.get('nameEn', '') or '').strip()
        name_pt = str(card.get('namePt', '') or '').strip()

        if not name_en and 'en' in langs:
            name_en = current
        if not name_ja and 'ja' in langs and 'en' not in langs:
            name_ja = current

        # One Piece Card Game has no official Portuguese card-name catalog.
        # Do not fabricate translations. The field stays blank until a reliable
        # Portuguese source is explicitly added later.
        card['nameEn'] = name_en
        card['namePt'] = name_pt
        card['nameJa'] = name_ja
        if name_en:
            en_count += 1
        if name_pt:
            pt_count += 1
        if name_ja:
            ja_count += 1

        if name_pt:
            card['name'] = name_pt
        elif name_en:
            card['name'] = name_en
        elif name_ja:
            card['name'] = name_ja

    coverage = payload.setdefault('coverage', {})
    coverage['namePtRecords'] = pt_count
    coverage['nameEnRecords'] = en_count
    coverage['nameJaRecords'] = ja_count
    payload['nameDisplayPolicy'] = 'en preferred; ja retained; namePt reserved for future reliable Portuguese source'
    save_payload(path, payload)
    print(f'One Piece multilingual names: PT={pt_count}, EN={en_count}, JA={ja_count}, total={len(cards)}')


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {'pokemon', 'yugioh', 'onepiece'}:
        raise SystemExit('Usage: python scripts/augment_multilingual_names.py pokemon|yugioh|onepiece')
    game = sys.argv[1]
    if game == 'pokemon':
        augment_pokemon()
    elif game == 'yugioh':
        augment_yugioh()
    else:
        augment_onepiece()


if __name__ == '__main__':
    main()
