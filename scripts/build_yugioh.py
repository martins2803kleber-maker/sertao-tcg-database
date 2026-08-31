import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "yugioh.json"

API_EN = "https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes"
API_PT = "https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes"


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SertaoTCG/2.0"},
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def normalize(raw, localized=None):
    localized = localized or {}
    misc = (raw.get("misc_info") or [{}])[0] or {}
    sets = raw.get("card_sets") or []
    first_set = sets[0] if sets else {}
    images = raw.get("card_images") or []
    first_image = images[0] if images else {}

    normalized_sets = []
    for s in sets:
        if not isinstance(s, dict):
            continue
        normalized_sets.append({
            "name": s.get("set_name", ""),
            "code": s.get("set_code", ""),
            "rarity": s.get("set_rarity", ""),
            "rarityCode": s.get("set_rarity_code", ""),
            "price": s.get("set_price", ""),
        })

    return {
        "id": raw.get("id"),
        "konamiId": misc.get("konami_id"),
        "name": localized.get("name") or raw.get("name", ""),
        "nameEn": raw.get("name", ""),
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
        "desc": localized.get("desc") or raw.get("desc", ""),
        "descEn": raw.get("desc", ""),
        "pendDesc": localized.get("pend_desc") or raw.get("pend_desc", ""),
        "monsterDesc": localized.get("monster_desc") or raw.get("monster_desc", ""),
        "archetype": raw.get("archetype", ""),
        "set": first_set.get("set_name", ""),
        "setCode": first_set.get("set_code", ""),
        "rarity": first_set.get("set_rarity", ""),
        "sets": normalized_sets,
        "image": first_image.get("image_url", ""),
        "imageSmall": first_image.get("image_url_small", ""),
        "imageCropped": first_image.get("image_url_cropped", ""),
        "tcgDate": misc.get("tcg_date", ""),
        "ocgDate": misc.get("ocg_date", ""),
        "formats": misc.get("formats") or [],
    }


def main():
    en_payload = get_json(API_EN)
    en_cards = en_payload.get("data") or []
    if not en_cards:
        raise SystemExit("YGOPRODeck English database returned no cards")

    pt_by_id = {}
    try:
        pt_payload = get_json(API_PT)
        for card in pt_payload.get("data") or []:
            if card.get("id") is not None:
                pt_by_id[str(card.get("id"))] = card
    except Exception as exc:
        print(f"Portuguese overlay unavailable, continuing with full English database: {exc}")

    cards = []
    for raw in en_cards:
        localized = pt_by_id.get(str(raw.get("id")), {})
        card = normalize(raw, localized)
        if card["name"]:
            cards.append(card)

    cards.sort(key=lambda c: (str(c["name"]).casefold(), int(c["id"] or 0)))

    payload = {
        "source": "YGOPRODeck EN complete + PT overlay",
        "language": "pt/en",
        "count": len(cards),
        "coverage": {
            "english": len(en_cards),
            "portugueseOverlay": len(pt_by_id),
        },
        "cards": cards,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    print(f"Wrote {len(cards)} Yu-Gi-Oh cards to {OUT_FILE}")
    print(f"Portuguese overlay available for {len(pt_by_id)} cards")


if __name__ == "__main__":
    main()
