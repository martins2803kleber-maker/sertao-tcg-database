import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / 'data' / 'pokemon.json'


def candidates(card):
    urls = []

    def add(value):
        value = str(value or '').strip()
        if value and value not in urls:
            urls.append(value)

    add(card.get('imageLarge'))
    add(card.get('image'))

    images = card.get('images') or {}
    if isinstance(images, dict):
        add(images.get('large'))
        add(images.get('small'))

    for url in list(urls):
        low = url.lower()
        if low.endswith('/high.webp'):
            add(url[:-10] + '/low.webp')
        elif low.endswith('/low.webp'):
            add(url[:-9] + '/high.webp')

        if 'images.pokemontcg.io' in low and low.endswith('_hires.png'):
            add(url[:-10] + '.png')
        elif 'images.pokemontcg.io' in low and low.endswith('.png'):
            add(url[:-4] + '_hires.png')

    return urls


def url_works(url):
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 SertaoTCG/8.1 image-audit',
            'Range': 'bytes=0-255',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            ctype = str(response.headers.get('Content-Type', '')).lower()
            return response.status in (200, 206) and ('image' in ctype or 'octet-stream' in ctype)
    except Exception:
        return False


def risky(card):
    source = str(card.get('source', '')).casefold()
    url = ' '.join(candidates(card)).casefold()
    return (
        'tcgdex' in source
        or 'tcgscreener' in source
        or 'scrydex' in source
        or 'tcgdex' in url
        or 'scrydex' in url
    )


def check(card):
    urls = candidates(card)
    for url in urls:
        if url_works(url):
            fixed = dict(card)
            fixed['image'] = url
            fixed['imageLarge'] = url if not fixed.get('imageLarge') or not url_works(fixed.get('imageLarge')) else fixed.get('imageLarge')
            return fixed, 'ok'
    return None, 'broken'


def main():
    payload = json.loads(DB_FILE.read_text(encoding='utf-8'))
    cards = payload.get('cards') or []

    targets = [c for c in cards if risky(c)]
    target_ids = {id(c) for c in targets}

    results = {}
    with ThreadPoolExecutor(max_workers=48) as pool:
        futures = {pool.submit(check, card): id(card) for card in targets}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception:
                results[key] = (None, 'broken')

    out = []
    repaired = 0
    removed = 0

    for card in cards:
        key = id(card)
        if key not in target_ids:
            out.append(card)
            continue
        fixed, status = results.get(key, (None, 'broken'))
        if status == 'broken' or not fixed:
            removed += 1
            continue
        if fixed.get('image') != card.get('image') or fixed.get('imageLarge') != card.get('imageLarge'):
            repaired += 1
        out.append(fixed)

    payload['cards'] = out
    payload['count'] = len(out)
    coverage = payload.setdefault('coverage', {})
    coverage['imageAuditRiskyChecked'] = len(targets)
    coverage['brokenImageRecordsRemoved'] = removed
    coverage['imageFallbacksRepaired'] = repaired
    coverage['mergedSearchableRecords'] = len(out)

    DB_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Pokemon image audit: checked={len(targets)}, repaired={repaired}, removed={removed}, final={len(out)}')


if __name__ == '__main__':
    main()
