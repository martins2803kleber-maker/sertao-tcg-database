import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "optcg"
CARDS_DIR = SOURCE / "english" / "cards"
PACKS_FILE = SOURCE / "english" / "packs.json"
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "onepiece.json"


def normalize_card(raw, pack_titles):
    pack_id = str(raw.get("pack_id", "")).strip()
    colors = raw.get("colors") or []
    attributes = raw.get("attributes") or []
    types = raw.get("types") or []

    image = raw.get("img_full_url") or raw.get("img_url") or ""
    if image and image.startswith("/"):
        image = "https://en.onepiece-cardgame.com" + image

    return {
        "id": str(raw.get("id", "")).strip(),
        "name": str(raw.get("name", "")).strip(),
        "packId": pack_id,
        "pack": pack_titles.get(pack_id, pack_id),
        "rarity": raw.get("rarity", ""),
        "category": raw.get("category", ""),
        "colors": colors,
        "cost": raw.get("cost"),
        "power": raw.get("power"),
        "counter": raw.get("counter"),
        "attributes": attributes,
        "types": types,
        "effect": raw.get("effect", ""),
        "trigger": raw.get("trigger", ""),
        "image": image,
    }


def main():
    if not CARDS_DIR.exists():
        raise SystemExit("One Piece dataset not found in source/optcg/english/cards")

    pack_titles = {}
    if PACKS_FILE.exists():
        try:
            packs = json.loads(PACKS_FILE.read_text(encoding="utf-8"))
            if isinstance(packs, dict):
                pack_iter = packs.values()
            elif isinstance(packs, list):
                pack_iter = packs
            else:
                pack_iter = []

            for p in pack_iter:
                if not isinstance(p, dict):
                    continue
                pid = str(p.get("id", ""))
                title = (p.get("title_parts") or {}).get("title") or p.get("raw_title") or pid
                pack_titles[pid] = title
        except Exception as exc:
            print(f"Could not parse packs.json: {exc}")

    cards = []
    seen = set()

    # The upstream dataset stores one JSON file per card inside pack subfolders.
    for file in sorted(CARDS_DIR.rglob("*.json")):
        try:
            parsed = json.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Skipping {file}: {exc}")
            continue

        if isinstance(parsed, dict):
            raw_cards = [parsed]
        elif isinstance(parsed, list):
            raw_cards = parsed
        else:
            continue

        for raw in raw_cards:
            if not isinstance(raw, dict):
                continue

            card = normalize_card(raw, pack_titles)
            if not card["name"] or not card["id"]:
                continue

            # Keep alternate arts as distinct entries when image differs.
            unique_key = (card["id"], card["image"], card["packId"])
            if unique_key in seen:
                continue
            seen.add(unique_key)
            cards.append(card)

    cards.sort(key=lambda c: (c["name"].casefold(), c["id"], c["packId"], c["image"]))

    meta = {
        "colors": sorted({x for c in cards for x in c["colors"] if x}),
        "categories": sorted({c["category"] for c in cards if c["category"]}),
        "rarities": sorted({c["rarity"] for c in cards if c["rarity"]}),
        "attributes": sorted({x for c in cards for x in c["attributes"] if x}),
        "types": sorted({x for c in cards for x in c["types"] if x}),
        "packs": sorted({c["pack"] for c in cards if c["pack"]}),
    }

    payload = {
        "source": "Kuroro1990/OPTCG (English dataset)",
        "language": "en",
        "count": len(cards),
        "meta": meta,
        "cards": cards,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {len(cards)} One Piece cards to {OUT_FILE}")


if __name__ == "__main__":
    main()
