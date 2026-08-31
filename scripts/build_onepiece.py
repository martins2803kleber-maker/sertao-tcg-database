import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / 'source' / 'optcg'
SECONDARY = ROOT / 'source' / 'apitcg'
SECONDARY_CARDS = SECONDARY / 'cards' / 'en'
OUT_DIR = ROOT / 'data'
OUT_FILE = OUT_DIR / 'onepiece.json'


def as_list(v):
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if v is None:
        return []
    t = str(v).strip()
    return [t] if t else []


def to_int(v):
    if v in (None, '', '-'):
        return None
    try:
        return int(str(v).replace('+', '').strip())
    except Exception:
        return v


def pack_titles(lang):
    file = PRIMARY / lang / 'packs.json'
    out = {}
    if not file.exists():
        return out
    try:
        packs = json.loads(file.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'Could not parse {file}: {exc}')
        return out
    it = packs.values() if isinstance(packs, dict) else packs if isinstance(packs, list) else []
    for p in it:
        if not isinstance(p, dict):
            continue
        pid = str(p.get('id', '')).strip()
        tp = p.get('title_parts') or {}
        out[pid] = tp.get('title') or tp.get('label') or p.get('raw_title') or pid
    return out


def canonical_id(value):
    """Language is metadata, never part of a physical printing's identity."""
    value = str(value or '').strip()
    value = re.sub(r'^(?:JP|JA|EN):', '', value, flags=re.I)
    return value


def base_id(value):
    return canonical_id(value).split('_', 1)[0].strip()


def normalize_primary(raw, lang, titles):
    original_id = canonical_id(raw.get('id', ''))
    pack_id = str(raw.get('pack_id', '')).strip()
    image = raw.get('img_full_url') or raw.get('img_url') or ''
    if image and image.startswith('/'):
        image = ('https://www.onepiece-cardgame.com' if lang == 'japanese' else 'https://en.onepiece-cardgame.com') + image
    is_ja = lang == 'japanese'
    return {
        'id': original_id,
        'originalId': original_id,
        'baseId': base_id(original_id),
        'language': 'ja' if is_ja else 'en',
        'languages': ['ja' if is_ja else 'en'],
        'name': str(raw.get('name', '') or '').strip(),
        'nameJa': str(raw.get('name', '') or '').strip() if is_ja else '',
        'packId': pack_id,
        'pack': titles.get(pack_id, pack_id),
        'packLabel': titles.get(pack_id, pack_id),
        'rarity': str(raw.get('rarity', '') or '').strip(),
        'category': str(raw.get('category', '') or '').strip(),
        'colors': as_list(raw.get('colors')),
        'cost': to_int(raw.get('cost')),
        'power': to_int(raw.get('power')),
        'counter': to_int(raw.get('counter')),
        'attributes': as_list(raw.get('attributes')),
        'types': as_list(raw.get('types')),
        'effect': str(raw.get('effect', '') or '').strip(),
        'effectJa': str(raw.get('effect', '') or '').strip() if is_ja else '',
        'trigger': str(raw.get('trigger', '') or '').strip(),
        'triggerJa': str(raw.get('trigger', '') or '').strip() if is_ja else '',
        'image': str(image or '').strip(),
        'imageJa': str(image or '').strip() if is_ja else '',
        'source': f'Kuroro1990/OPTCG {lang}',
    }


def normalize_secondary(raw, source_file):
    images = raw.get('images') or {}
    attribute = raw.get('attribute') or {}
    set_info = raw.get('set') or {}
    card_id = canonical_id(raw.get('id') or raw.get('code') or '')
    bid = canonical_id(raw.get('code') or base_id(card_id))
    category = str(raw.get('type', '') or '').strip().title()
    color = str(raw.get('color', '') or '').strip()
    family = str(raw.get('family', '') or '').strip()
    attr_name = str(attribute.get('name', '') or '').strip() if isinstance(attribute, dict) else str(attribute or '').strip()
    pack_name = str(set_info.get('name', '') or '').strip() if isinstance(set_info, dict) else str(set_info or '').strip()
    pack_id = source_file.stem.upper()
    return {
        'id': card_id,
        'originalId': card_id,
        'baseId': bid,
        'language': 'en',
        'languages': ['en'],
        'name': str(raw.get('name', '') or '').strip(),
        'nameJa': '',
        'packId': pack_id,
        'pack': pack_name or pack_id,
        'packLabel': pack_name or pack_id,
        'rarity': str(raw.get('rarity', '') or '').strip(),
        'category': 'DON!!' if category.upper() == 'DON!!' else category,
        'colors': [color] if color else [],
        'cost': to_int(raw.get('cost')),
        'power': to_int(raw.get('power')),
        'counter': to_int(raw.get('counter')),
        'attributes': [attr_name] if attr_name else [],
        'types': [x.strip() for x in family.replace('/', '|').split('|') if x.strip()],
        'effect': str(raw.get('ability', '') or '').replace('<br>', '\n').strip(),
        'effectJa': '',
        'trigger': str(raw.get('trigger', '') or '').replace('<br>', '\n').strip(),
        'triggerJa': '',
        'image': str(images.get('large') or images.get('small') or '').strip(),
        'imageJa': '',
        'source': 'apitcg/one-piece-tcg-data',
    }


def quality(c):
    return sum(bool(c.get(k)) for k in ('image', 'effect', 'pack', 'types', 'attributes', 'rarity'))


def merge_same_print(a, b):
    if not a:
        return b

    a_is_en = 'en' in (a.get('languages') or [a.get('language')])
    b_is_en = 'en' in (b.get('languages') or [b.get('language')])

    # Prefer English as public display text whenever available; Japanese stays as metadata.
    if b_is_en and not a_is_en:
        primary, other = b, a
    elif a_is_en and not b_is_en:
        primary, other = a, b
    else:
        primary, other = (a, b) if quality(a) >= quality(b) else (b, a)

    m = dict(primary)
    langs = []
    for card in (a, b):
        for lang in card.get('languages') or [card.get('language', '')]:
            if lang and lang not in langs:
                langs.append(lang)
    m['languages'] = langs
    m['language'] = 'en' if 'en' in langs else 'ja'

    ja = a if 'ja' in (a.get('languages') or [a.get('language')]) else b if 'ja' in (b.get('languages') or [b.get('language')]) else None
    if ja:
        m['nameJa'] = ja.get('nameJa') or ja.get('name') or m.get('nameJa', '')
        m['effectJa'] = ja.get('effectJa') or ja.get('effect') or m.get('effectJa', '')
        m['triggerJa'] = ja.get('triggerJa') or ja.get('trigger') or m.get('triggerJa', '')
        m['imageJa'] = ja.get('imageJa') or ja.get('image') or m.get('imageJa', '')

    for k in ('name', 'packId', 'pack', 'packLabel', 'rarity', 'category', 'effect', 'trigger', 'image', 'baseId', 'originalId'):
        if not m.get(k) and other.get(k):
            m[k] = other[k]
    for k in ('cost', 'power', 'counter'):
        if m.get(k) is None and other.get(k) is not None:
            m[k] = other[k]
    for k in ('colors', 'attributes', 'types'):
        vals = []
        for x in as_list(m.get(k)) + as_list(other.get(k)):
            if x not in vals:
                vals.append(x)
        m[k] = vals

    src = []
    for card in (a, b):
        for s in str(card.get('source', '')).split(' + '):
            if s and s not in src:
                src.append(s)
    m['source'] = ' + '.join(src)
    return m


def add(store, card):
    key = canonical_id(card.get('id'))
    if not key or not card.get('name'):
        return False
    card['id'] = key
    card['originalId'] = key
    card['baseId'] = base_id(card.get('baseId') or key)
    existed = key in store
    store[key] = merge_same_print(store.get(key), card)
    return existed


def set_code(card):
    candidates = [card.get('id', ''), card.get('baseId', ''), card.get('pack', ''), card.get('packLabel', '')]
    text = ' '.join(str(x) for x in candidates)
    m = re.search(r'\b(OP|EB|ST|PRB)[-_ ]?0?(\d{1,2})\b', text, flags=re.I)
    if not m:
        return ''
    return f'{m.group(1).upper()}-{int(m.group(2)):02d}'


def main():
    store = {}
    counts = {}
    language_merges = 0

    # English first so it becomes the preferred display layer.
    for lang in ('english', 'japanese'):
        cards_dir = PRIMARY / lang / 'cards'
        titles = pack_titles(lang)
        n = 0
        if not cards_dir.exists():
            print(f'Missing {cards_dir}')
            continue
        for file in sorted(cards_dir.rglob('*.json')):
            try:
                parsed = json.loads(file.read_text(encoding='utf-8'))
            except Exception as exc:
                print(f'Skipping {file}: {exc}')
                continue
            rows = [parsed] if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else []
            for raw in rows:
                if not isinstance(raw, dict):
                    continue
                card = normalize_primary(raw, lang, titles)
                if card.get('id') and card.get('name'):
                    n += 1
                    if add(store, card) and lang == 'japanese':
                        language_merges += 1
        counts[lang] = n

    sec = 0
    if SECONDARY_CARDS.exists():
        for file in sorted(SECONDARY_CARDS.glob('*.json')):
            try:
                parsed = json.loads(file.read_text(encoding='utf-8'))
            except Exception as exc:
                print(f'Skipping {file}: {exc}')
                continue
            rows = [parsed] if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else []
            for raw in rows:
                if not isinstance(raw, dict):
                    continue
                card = normalize_secondary(raw, file)
                if card.get('id') and card.get('name'):
                    sec += 1
                    add(store, card)
    counts['secondaryEnglish'] = sec
    counts['languageDuplicatesMerged'] = language_merges

    cards = list(store.values())
    cards.sort(key=lambda c: (c['name'].casefold(), c.get('baseId', ''), c.get('id', '')))

    # Coverage diagnostics specifically guard the newest Japanese sets.
    by_set = {}
    for c in cards:
        sc = set_code(c)
        if sc:
            by_set[sc] = by_set.get(sc, 0) + 1
    counts['setCoverage'] = dict(sorted(by_set.items()))
    counts['OP14Records'] = by_set.get('OP-14', 0)
    counts['OP15Records'] = by_set.get('OP-15', 0)
    op_numbers = [int(code.split('-')[1]) for code in by_set if code.startswith('OP-')]
    counts['highestOPSetDetected'] = max(op_numbers) if op_numbers else None
    counts['japaneseOnlyUnique'] = sum(1 for c in cards if (c.get('languages') or []) == ['ja'])
    counts['multilingualMerged'] = sum(1 for c in cards if 'ja' in (c.get('languages') or []) and 'en' in (c.get('languages') or []))
    counts['mergedSearchableRecords'] = len(cards)

    def uniq(vals):
        return sorted({str(v).strip() for v in vals if str(v).strip()}, key=str.casefold)

    meta = {
        'languages': uniq(lang for c in cards for lang in (c.get('languages') or [c.get('language', '')])),
        'colors': uniq(x for c in cards for x in c['colors']),
        'categories': uniq(c['category'] for c in cards),
        'rarities': uniq(c['rarity'] for c in cards),
        'attributes': uniq(x for c in cards for x in c['attributes']),
        'types': uniq(x for c in cards for x in c['types']),
        'packs': uniq(c['pack'] for c in cards),
    }
    payload = {
        'source': 'Kuroro1990/OPTCG English+Japanese + apitcg English (language-deduplicated)',
        'language': 'en preferred, ja metadata / ja-only unique printings',
        'count': len(cards),
        'coverage': counts,
        'meta': meta,
        'cards': cards,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Wrote {len(cards)} One Piece unique searchable records')
    print(counts)


if __name__ == '__main__':
    main()
