import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "yugioh.json"

API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes"
MANIFEST_URL = "https://artworks.ygoresources.com/manifest.json"
ART_BASE = "https://artworks.ygoresources.com"


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SertaoTCG/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def resolve_artwork(manifest_cards, konami_id):
    if not konami_id:
        return ""

    card_data = manifest_cards.get(str(konami_id))
    if not isinstance(card_data, dict) or not card_data:
        return ""

    artwork_ids = sorted(card_data.keys(), key=lambda x: (not str(x).isdigit(), str(x)))
    artwork = card_data.get(artwork_ids[0]) or {}

    candidate = artwork.get("bestTCG") or artwork.get("bestArt") or artwork.get("bestOCG") or ""

    if isinstance(candidate, dict):
        candidate = candidate.get("path", "")

    if not candidate:
        idx = artwork.get("idx") or {}
        for locale in ("en", "pt", "de", "fr", "it", "es", "ja", "ko"):
            items = idx.get(locale)
            if isinstance(items, list) and items:
                candidate = items[0].get("path", "")
                if candidate:
                    break

    if not candidate:
        return ""

    if candidate.startswith("http://") or candidate.startswith("https://"):
        return candidate

    if not candidate.startswith("/"):
        candidate = "/" + candidate

    return ART_BASE + candidate


def main():
    api_payload = get_json(API_URL)
    cards_raw = api_payload.get("data") or []

    manifest = get_json(MANIFEST_URL)
    manifest_cards = manifest.get("cards") or {}

    cards = []

    for raw in cards_raw:
        misc = (raw.get("misc_info") or [{}])[0] or {}
        konami_id = misc.get("konami_id")
        image = resolve_artwork(manifest_cards, konami_id)

        sets = raw.get("card_sets") or []
        first_set = sets[0] if sets else {}

        card = {
            "id": raw.get("id"),
            "konamiId": konami_id,
            "name": raw.get("name", ""),
            "type": raw.get("type", ""),
            "race": raw.get("race", ""),
            "attribute": raw.get("attribute", ""),
            "level": raw.get("level"),
            "atk": raw.get("atk"),
            "def": raw.get("def"),
            "desc": raw.get("desc", ""),
            "archetype": raw.get("archetype", ""),
            "set": first_set.get("set_name", ""),
            "setCode": first_set.get("set_code", ""),
            "rarity": first_set.get("set_rarity", ""),
            "image": image,
        }

        if card["name"]:
            cards.append(card)

    cards.sort(key=lambda c: c["name"].casefold())

    payload = {
        "source": "YGOPRODeck + YGOResources artworks",
        "language": "pt",
        "count": len(cards),
        "cards": cards,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"Wrote {len(cards)} Yu-Gi-Oh cards to {OUT_FILE}")


if __name__ == "__main__":
    main()
