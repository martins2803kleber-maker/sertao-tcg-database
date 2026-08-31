import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / 'data' / 'pokemon.json'

SOURCES = [
    ('delta', 'https://tcgscreener.com/guide/delta-reign-card-list'),
    ('30c', 'https://tcgscreener.com/guide/30th-celebration-card-list'),
]


class ImgParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'img':
            return
        d = dict(attrs)
        alt = (d.get('alt') or '').strip()
        src = (d.get('src') or d.get('data-src') or '').strip()
        srcset = (d.get('srcset') or '').strip()
        if not src and srcset:
            src = srcset.split(',')[-1].strip().split(' ')[0]
        self.images.append((alt, src))


def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'SertaoTCG/7.1 (+card catalog updater)'})
    with urllib.request.urlopen(req, timeout=180) as response:
        return response.read().decode('utf-8', errors='replace')


def image_works(url):
    if not url:
        return False
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 SertaoTCG/7.1', 'Range': 'bytes=0-1023'})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            ctype = str(response.headers.get('Content-Type', '')).lower()
            return response.status in (200, 206) and ('image' in ctype or 'octet-stream' in ctype)
    except Exception:
        return False


def unwrap_next_image(src, base):
    src = urllib.parse.urljoin(base, src)
    parsed = urllib.parse.urlparse(src)
    if parsed.path.endswith('/_next/image') or parsed.path == '/_next/image':
        q = urllib.parse.parse_qs(parsed.query)
        target = (q.get('url') or [''])[0]
        if target:
            return urllib.parse.urljoin(base, target)
    return src


def blank_card(cid, name, number, set_id, set_name, rarity, image, language, source, fallbacks=None):
    return {
        'id': cid,
        'originalId': cid,
        'language': language,
        'languages': [language],
        'name': name,
        'nameJa': name if language == 'ja' else '',
        'number': number,
        'setId': set_id,
        'set': set_name,
        'series': 'Mega Evolution',
        'releaseDate': '2026',
        'rarity': rarity,
        'supertype': '',
        'subtypes': [],
        'hp': '',
        'types': [],
        'evolvesFrom': '',
        'evolvesTo': [],
        'rules': [],
        'ancientTrait': None,
        'abilities': [],
        'attacks': [],
        'weaknesses': [],
        'resistances': [],
        'retreatCost': [],
        'convertedRetreatCost': None,
        'artist': '',
        'regulationMark': '',
        'legalities': {'standard': '', 'expanded': '', 'unlimited': ''},
        'image': image,
        'imageLarge': image,
        '_fallbackImages': fallbacks or [],
        'source': source,
    }


def parse_delta(html):
    parser = ImgParser(); parser.feed(html)
    out = {}
    for alt, src in parser.images:
        if 'storm emeralda' not in alt.casefold() and 'delta reign' not in alt.casefold():
            continue
        m = re.search(r'(.+?)\s+(\d{3})/076(?:\b|,)', alt)
        if not m:
            continue
        name = m.group(1).strip()
        number = m.group(2)
        if not name or len(name) > 80:
            continue
        page_image = unwrap_next_image(src, 'https://tcgscreener.com') if src else ''
        scrydex = f'https://images.scrydex.com/pokemon/m6_ja-{int(number)}/medium'
        rarity_match = re.search(r'\b(C|U|R|RR|AR|SR|SAR|MUR)\b', alt)
        rarity = rarity_match.group(1) if rarity_match else ''
        cid = f'M6-{number}'
        out[cid] = blank_card(
            cid, name, number, 'M6', 'Delta Reign / Storm Emeralda', rarity,
            scrydex, 'ja', 'TCGscreener + Scrydex Storm Emeralda public catalog',
            [page_image] if page_image and page_image != scrydex else []
        )
    return list(out.values())


def parse_30c(html):
    parser = ImgParser(); parser.feed(html)
    out = {}
    for alt, src in parser.images:
        if '30th celebration' not in alt.casefold():
            continue
        m = re.search(r'(.+?)\s+(\d{3})/128(?:\b|,)', alt)
        if m:
            name = m.group(1).strip()
            number = m.group(2)
            if name and len(name) <= 80:
                page_image = unwrap_next_image(src, 'https://tcgscreener.com') if src else ''
                fallback = f'https://tcgscreener.com/guides/30th-celebration/cards/30c-{number}.webp'
                image = page_image or fallback
                cid = f'30C-{number}'
                out[cid] = blank_card(
                    cid, name, number, '30C', '30th Celebration', '', image, 'en',
                    'TCGscreener revealed-card catalog using official revealed imagery',
                    [fallback] if fallback != image else []
                )
            continue
        pm = re.search(r'(.+?)\s+MEP\s+(\d{3})\s+promo', alt, flags=re.I)
        if pm:
            name = pm.group(1).strip()
            number = pm.group(2)
            image = unwrap_next_image(src, 'https://tcgscreener.com') if src else ''
            if image:
                cid = f'MEP-{number}'
                out[cid] = blank_card(
                    cid, name, number, 'MEP', '30th Celebration Promos', 'Promo', image, 'en',
                    'TCGscreener 30th Celebration promo catalog'
                )
    return list(out.values())


def verify_cards(cards):
    def check(card):
        candidates = []
        for u in [card.get('image'), card.get('imageLarge')] + list(card.get('_fallbackImages') or []):
            if u and u not in candidates:
                candidates.append(u)
        for u in candidates:
            if image_works(u):
                fixed = dict(card)
                fixed['image'] = u
                fixed['imageLarge'] = u
                fixed.pop('_fallbackImages', None)
                return fixed
        return None

    good = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(check, c) for c in cards]
        for future in as_completed(futures):
            try:
                card = future.result()
            except Exception:
                card = None
            if card:
                good.append(card)
    return good


def add_or_repair(store, incoming):
    cid = incoming['id']
    if cid not in store:
        store[cid] = incoming
        return 'added'
    current = store[cid]
    if not current.get('image') and incoming.get('image'):
        current['image'] = incoming['image']
        current['imageLarge'] = incoming.get('imageLarge') or incoming['image']
        return 'repaired'
    return 'existing'


def main():
    payload = json.loads(DB_FILE.read_text(encoding='utf-8'))
    cards = payload.get('cards') or []
    store = {str(c.get('id')): c for c in cards if c.get('id')}
    stats = {'deltaAdded': 0, 'celebration30Added': 0, 'imagesRepaired': 0, 'upcomingBrokenImagesSkipped': 0}
    for kind, url in SOURCES:
        try:
            html = fetch_text(url)
            parsed = parse_delta(html) if kind == 'delta' else parse_30c(html)
            fresh = verify_cards(parsed)
            stats['upcomingBrokenImagesSkipped'] += len(parsed) - len(fresh)
            print(f'{kind}: parsed {len(parsed)}, verified {len(fresh)} cards with working images')
            for card in fresh:
                result = add_or_repair(store, card)
                if result == 'added':
                    stats['deltaAdded' if kind == 'delta' else 'celebration30Added'] += 1
                elif result == 'repaired':
                    stats['imagesRepaired'] += 1
        except Exception as exc:
            print(f'Upcoming supplement {kind} unavailable: {exc}')
    store = {k: v for k, v in store.items() if v.get('image') or v.get('imageLarge')}
    cards = list(store.values())
    for c in cards:
        c.pop('_fallbackImages', None)
    cards.sort(key=lambda c: (str(c.get('name', '')).casefold(), str(c.get('set', '')), str(c.get('number', '')), str(c.get('id', ''))))
    coverage = payload.setdefault('coverage', {})
    coverage.update(stats)
    coverage['deltaReignStormEmeraldaRecords'] = sum(1 for c in cards if c.get('setId', '').casefold() == 'm6' or 'delta reign' in str(c.get('set', '')).casefold())
    coverage['celebration30Records'] = sum(1 for c in cards if c.get('setId', '').casefold() == '30c' or '30th celebration' in str(c.get('set', '')).casefold())
    coverage['mergedSearchableRecords'] = len(cards)
    payload['count'] = len(cards)
    payload['cards'] = cards
    meta = payload.setdefault('meta', {})
    meta['sets'] = sorted({str(c.get('set', '')).strip() for c in cards if str(c.get('set', '')).strip()}, key=str.casefold)
    payload['source'] = str(payload.get('source', '')) + ' + verified revealed Delta Reign/30th Celebration supplement'
    DB_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Pokemon final count after verified upcoming supplement: {len(cards)}')
    print(stats)


if __name__ == '__main__':
    main()
