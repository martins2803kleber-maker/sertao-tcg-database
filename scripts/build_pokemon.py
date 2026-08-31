import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "pokemon-tcg-data"
CARDS_DIR = SOURCE / "cards" / "en"
SETS_FILE = SOURCE / "sets" / "en.json"
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "pokemon.json"


def normalize_card(card, sets_by_id):
    card_id = str(card.get("id", "")).strip()
    set_id = card_id.rsplit("-", 1)[0] if "-" in card_id else ""
    set_info = sets_by_id.get(set_id, {})
    images = card.get("images") or {}

    return {
        "id": card_id,
        "name": str(card.get("name", "")).strip(),
        "number": str(card.get("number", "")).strip(),
        "setId": set_id,
        "set": set_info.get("name", set_id),
        "series": set_info.get("series", ""),
        "releaseDate": set_info.get("releaseDate", ""),
        "rarity": card.get("rarity", ""),
        "supertype": card.get("supertype", ""),
        "image": images.get("small", ""),
        "imageLarge": images.get("large", ""),
    }


def main():
    if not CARDS_DIR.exists() or not SETS_FILE.exists():
        raise SystemExit("Official Pokemon TCG dataset not found in source/pokemon-tcg-data")

    sets = json.loads(SETS_FILE.read_text(encoding="utf-8"))
    sets_by_id = {s.get("id", ""): s for s in sets}

    cards = []
    for file in sorted(CARDS_DIR.glob("*.json")):
        try:
            raw_cards = json.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Skipping {file.name}: {exc}")
            continue

        for raw in raw_cards:
            card = normalize_card(raw, sets_by_id)
            if not card["name"]:
                continue
            cards.append(card)

    cards.sort(key=lambda c: (c["name"].casefold(), c["releaseDate"], c["set"], c["number"]))

    payload = {
        "source": "PokemonTCG/pokemon-tcg-data",
        "language": "en",
        "count": len(cards),
        "cards": cards,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {len(cards)} cards to {OUT_FILE}")


if __name__ == "__main__":
    main()
