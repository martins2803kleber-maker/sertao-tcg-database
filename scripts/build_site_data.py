#!/usr/bin/env python3
# Builds the browser-optimized mirrors used by search, filters, decklists and Deck Builder.
# Pokemon Standard hotfix: dedicated, prevalidated Standard dataset.
from __future__ import annotations
import hashlib, json, re, shutil
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'site'
DETAIL = OUT / 'detail'

KEEP = {
'yugioh': {
'id','baseId','originalId','name','namePt','nameEn','nameJa','type','frameType','race','attribute','level','rank','linkval','scale','atk','def','archetype','desc','description','effect','text','pend_desc','monster_desc','rarity','image','imageSmall','imageLarge','imageCropped','imageUrl','image_url','images','banlist_info','cardType','typeline','setcode','genesysPoints','genesys_points'
},
'pokemon': {
'id','name','namePt','nameEn','nameJa','number','set','setCode','setId','series','supertype','subtypes','types','rarity','hp','stage','evolvesFrom','artist','regulationMark','releaseDate','legalities','convertedRetreatCost','retreatCost','abilities','attacks','rules','weaknesses','resistances','ancientTrait','description','desc','effectText','text','image','imageSmall','imageLarge','imageHiRes','imageHires','imageUrl','image_url','images','category'
},
'onepiece': {
'id','code','baseId','originalId','cardId','card_id','number','name','namePt','nameEn','nameJa','category','colors','color','rarity','pack','packLabel','attributes','attribute','types','type','cost','power','counter','effect','trigger','text','image','imageSmall','imageLarge','imageHiRes','imageHires','imageUrl','image_url','imageEn','imageJa','images','set','setCode'
}}

def read_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

def compact_value(v):
    if isinstance(v, str):
        return v.strip()
    return v

def compact_card(game: str, card: dict) -> dict:
    allowed = KEEP[game]
    out = {}
    for k in allowed:
        if k not in card:
            continue
        v = card[k]
        if v is None or v == '' or v == [] or v == {}:
            continue
        out[k] = compact_value(v)
    if game == 'yugioh':
        if 'id' in out:
            out.setdefault('baseId', out['id'])
        if 'desc' not in out:
            for k in ('description','effect','text','monster_desc'):
                if out.get(k): out['desc'] = out[k]; break
    elif game == 'onepiece':
        if out.get('id') and not out.get('code'): out['code'] = out['id']
        if out.get('code') and not out.get('id'): out['id'] = out['code']
    elif game == 'pokemon':
        if out.get('name') and not out.get('nameEn'): out['nameEn'] = out['name']
        s = out.get('set') if isinstance(out.get('set'), dict) else card.get('set')
        if isinstance(s, dict):
            if not out.get('releaseDate'):
                release = s.get('releaseDate') or s.get('release_date')
                if release: out['releaseDate'] = release
            if not out.get('series') and s.get('series'):
                out['series'] = s.get('series')
            if not out.get('setCode'):
                code = s.get('ptcgoCode') or s.get('id')
                if code: out['setCode'] = code
        if not out.get('legalities') and isinstance(card.get('legality'), dict):
            out['legalities'] = card['legality']
    return out

def cards_from(payload):
    if isinstance(payload, list): return payload
    if isinstance(payload, dict) and isinstance(payload.get('cards'), list): return payload['cards']
    raise ValueError('JSON sem lista cards')

def clean_set(v):
    return re.sub(r'[^A-Za-z0-9_-]+','',str(v or '').upper()) or 'UNKNOWN'

def detail_bucket(game: str, c: dict) -> str:
    if game == 'yugioh':
        sid = re.sub(r'\D','',str(c.get('id') or c.get('baseId') or '0')).zfill(8)
        return sid[:2]
    if game == 'pokemon':
        s = c.get('setCode') or c.get('set') or c.get('setId') or 'UNKNOWN'
        if isinstance(s, dict): s = s.get('id') or s.get('ptcgoCode') or s.get('name') or 'UNKNOWN'
        return clean_set(s)
    code = str(c.get('code') or c.get('id') or 'UNKNOWN').upper()
    return clean_set(code.split('-')[0])

def norm(v):
    return re.sub(r'\s+', ' ', str(v or '').strip().lower())

def pokemon_release_date(c: dict):
    v = c.get('releaseDate')
    if not v and isinstance(c.get('set'), dict):
        v = c['set'].get('releaseDate') or c['set'].get('release_date')
    if not v:
        return None
    s = str(v).strip().replace('/', '-')
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except ValueError:
        return None

def pokemon_standard_status(c: dict) -> str:
    leg = c.get('legalities') if isinstance(c.get('legalities'), dict) else {}
    if not leg and isinstance(c.get('legality'), dict):
        leg = c.get('legality')
    return norm(leg.get('standard'))

def pokemon_direct_standard_legal(c: dict, cutoff: date) -> bool:
    status = pokemon_standard_status(c)
    if status == 'legal':
        return True
    if status in {'not legal','illegal','banned'}:
        return False
    mark = str(c.get('regulationMark') or '').strip().upper()
    if mark not in {'H','I','J'}:
        return False
    released = pokemon_release_date(c)
    return released is None or released <= cutoff

def pokemon_standard_cards(compact_cards: list[dict]) -> tuple[list[dict], int, int]:
    cutoff = date.today() - timedelta(days=14)
    legal_names = set()
    direct_keys = set()
    direct_count = 0
    for c in compact_cards:
        if pokemon_direct_standard_legal(c, cutoff):
            direct_count += 1
            name = norm(c.get('nameEn') or c.get('name'))
            if name:
                legal_names.add(name)
            direct_keys.add(str(c.get('id') or '') + '|' + str(c.get('setId') or c.get('setCode') or c.get('set') or '') + '|' + str(c.get('number') or ''))

    # Keep older printings in the pool when a current printing with the same name is legal.
    # They are useful for alternate-art/import compatibility, but are NOT counted as
    # distinct Standard cards in the manifest.
    out = []
    seen = set()
    for c in compact_cards:
        name = norm(c.get('nameEn') or c.get('name'))
        key = str(c.get('id') or '') + '|' + str(c.get('setId') or c.get('setCode') or c.get('set') or '') + '|' + str(c.get('number') or '')
        if key in direct_keys or (name and name in legal_names):
            if key not in seen:
                seen.add(key)
                out.append(c)
    return out, len(legal_names), direct_count

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if DETAIL.exists(): shutil.rmtree(DETAIL)
    DETAIL.mkdir(parents=True, exist_ok=True)
    manifest = {'schema':4,'games':{}}

    for game in ('yugioh','pokemon','onepiece'):
        src_path = DATA / f'{game}.json'
        payload = read_json(src_path)
        source_cards = cards_from(payload)
        compact_cards = [compact_card(game,c) for c in source_cards if isinstance(c,dict)]
        compact_payload = {'cards': compact_cards}
        if isinstance(payload, dict):
            for k in ('meta','updatedAt','updated_at','source','version'):
                if k in payload: compact_payload[k] = payload[k]
        compact_payload['siteSchema'] = 4
        dest = OUT / f'{game}.json'
        write_json(dest, compact_payload)

        standard = []
        standard_unique = 0
        standard_direct = 0
        if game == 'pokemon':
            standard, standard_unique, standard_direct = pokemon_standard_cards(compact_cards)
            std_path = OUT / 'pokemon_standard.json'
            write_json(std_path, {
                'cards': standard,
                'siteSchema': 4,
                'format': 'standard-2026',
                'regulationMarks': ['H','I','J'],
                'uniqueLegalCardNames': standard_unique,
                'directLegalPrintings': standard_direct,
                'allCompatiblePrintings': len(standard),
                'generatedAt': date.today().isoformat()
            })

        buckets = {}
        for c in compact_cards:
            buckets.setdefault(detail_bucket(game,c), []).append(c)
        game_dir = DETAIL / game
        for bucket, items in buckets.items():
            write_json(game_dir / f'{bucket}.json', {'cards':items,'siteSchema':4})

        raw_size = src_path.stat().st_size
        compact_size = dest.stat().st_size
        sha = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
        manifest['games'][game] = {
            'cards':len(compact_cards), 'bytes':compact_size, 'sourceBytes':raw_size,
            'savedPct': round((1 - compact_size/raw_size)*100, 1) if raw_size else 0,
            'sha256':sha, 'detailBuckets':len(buckets),
            'url':f'data/site/{game}.json'
        }
        if game == 'pokemon':
            manifest['games'][game]['standardUniqueCards'] = standard_unique
            manifest['games'][game]['standardDirectPrintings'] = standard_direct
            manifest['games'][game]['standardCompatiblePrintings'] = len(standard)
            manifest['games'][game]['standardUrl'] = 'data/site/pokemon_standard.json'
            manifest['games'][game]['standardBytes'] = (OUT / 'pokemon_standard.json').stat().st_size
    write_json(OUT / 'manifest.json', manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
