import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "yugioh.json"

API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes"


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SertaoTCG/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def main():
    api_payload = get_json(API_URL)
    cards_raw = api_payload.get("data") or []

    cards = []

    for raw in cards_raw:
        misc = (raw.get("misc_info") or [{}])[0] or {}
        sets = raw.get("card_sets") or []
        first_set = sets[0] if sets else {}
        images = raw.get("card_images") or []
        first_image = images[0] if images else {}

        card = {
            "id": raw.get("id"),
            "konamiId": misc.get("konami_id"),
            "name": raw.get("name", ""),
            "type": raw.get("type", ""),
            "frameType": raw.get("frameType", ""),
            "race": raw.get("race", ""),
            "attribute": raw.get("attribute", ""),
            "level": raw.get("level"),
            "rank": raw.get("level") if "XYZ" in str(raw.get("type", "")).upper() else None,
            "linkval": raw.get("linkval"),
            "linkmarkers": raw.get("linkmarkers") or [],
            "scale": raw.get("scale"),
            "atk": raw.get("atk"),
            "def": raw.get("def"),
            "desc": raw.get("desc", ""),
            "pendDesc": raw.get("pend_desc", ""),
            "monsterDesc": raw.get("monster_desc", ""),
            "archetype": raw.get("archetype", ""),
            "set": first_set.get("set_name", ""),
            "setCode": first_set.get("set_code", ""),
            "rarity": first_set.get("set_rarity", ""),
            "image": first_image.get("image_url", ""),
            "imageSmall": first_image.get("image_url_small", ""),
            "imageCropped": first_image.get("image_url_cropped", ""),
        }

        if card["name"]:
            cards.append(card)

    cards.sort(key=lambda c: c["name"].casefold())

    payload = {
        "source": "YGOPRODeck",
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
