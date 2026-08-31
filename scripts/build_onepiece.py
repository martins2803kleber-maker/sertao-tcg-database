import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "source" / "optcg"
PRIMARY_CARDS = PRIMARY / "english" / "cards"
PRIMARY_PACKS = PRIMARY / "english" / "packs.json"
SECONDARY = ROOT / "source" / "apitcg"
SECONDARY_CARDS = SECONDARY / "cards" / "en"
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "onepiece.json"


def as_list(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def to_int_or_none(value):
    if value in (None, "", "-"):
        return None
    try:
        return int(str(value).replace("+", "").strip())
    except Exception:
        return value


def primary_pack_titles():
    titles = {}
    if not PRIMARY_PACKS.exists():
        return titles
    try:
        packs = json.loads(PRIMARY_PACKS.read_text(encoding="utf-8"))
        pack_iter = packs.values() if isinstance(packs, dict) else packs if isinstance(packs, list) else []
        for p in pack_iter:
            if not isinstance(p, dict):
                continue
            pid = str(p.get("id", "")).strip()
            title_parts = p.get("title_parts") or {}
            title = title_parts.get("title") or title_parts.get("label") or p.get("raw_title") or pid
            titles[pid] = title
    except Exception as exc:
        print(f"Could not parse primary packs.json: {exc}")
    return titles


def normalize_primary(raw, pack_titles):
    pack_id = str(raw.get("pack_id", "")).strip()
    image = raw.get("img_full_url") or raw.get("img_url") or ""
    if image and image.startswith("/"):
        image = "https://en.onepiece-cardgame.com" + image
    pack_name = pack_titles.get(pack_id, pack_id)
    return {
        "id": str(raw.get("id", "")).strip(),
        "baseId": str(raw.get("id", "")).split("_", 1)[0].strip(),
        "name": str(raw.get("name", "")).strip(),
        "packId": pack_id,
        "pack": pack_name,
        "packLabel": pack_name,
        "rarity": str(raw.get("rarity", "") or "").strip(),
        "category": str(raw.get("category", "") or "").strip(),
        "colors": as_list(raw.get("colors")),
        "cost": to_int_or_none(raw.get("cost")),
        "power": to_int_or_none(raw.get("power")),
        "counter": to_int_or_none(raw.get("counter")),
        "attributes": as_list(raw.get("attributes")),
        "types": as_list(raw.get("types")),
        "effect": str(raw.get("effect", "") or "").strip(),
        "trigger": str(raw.get("trigger", "") or "").strip(),
        "image": str(image or "").strip(),
        "source": "Kuroro1990/OPTCG",
    }


def normalize_secondary(raw, source_file):
    images = raw.get("images") or {}
    attribute = raw.get("attribute") or {}
    set_info = raw.get("set") or {}
    card_id = str(raw.get("id") or raw.get("code") or "").strip()
    base_id = str(raw.get("code") or card_id.split("_", 1)[0]).strip()
    category = str(raw.get("type", "") or "").strip().title()
    if category.upper() == "DON!!":
        category = "DON!!"
    color = str(raw.get("color", "") or "").strip()
    family = str(raw.get("family", "") or "").strip()
    attr_name = str(attribute.get("name", "") or "").strip() if isinstance(attribute, dict) else str(attribute or "").strip()
    pack_name = str(set_info.get("name", "") or "").strip() if isinstance(set_info, dict) else str(set_info or "").strip()
    pack_id = source_file.stem.upper()
    return {
        "id": card_id,
        "baseId": base_id,
        "name": str(raw.get("name", "") or "").strip(),
        "packId": pack_id,
        "pack": pack_name or pack_id,
        "packLabel": pack_name or pack_id,
        "rarity": str(raw.get("rarity", "") or "").strip(),
        "category": category,
        "colors": [color] if color else [],
        "cost": to_int_or_none(raw.get("cost")),
        "power": to_int_or_none(raw.get("power")),
        "counter": to_int_or_none(raw.get("counter")),
        "attributes": [attr_name] if attr_name else [],
        "types": [x.strip() for x in family.replace("/", "|").split("|") if x.strip()],
        "effect": str(raw.get("ability", "") or "").replace("<br>", "\n").strip(),
        "trigger": str(raw.get("trigger", "") or "").replace("<br>", "\n").strip(),
        "image": str(images.get("large") or images.get("small") or "").strip(),
        "source": "apitcg/one-piece-tcg-data",
    }


def quality(card):
    return sum([
        bool(card.get("image")),
        bool(card.get("effect")),
        bool(card.get("pack")),
        bool(card.get("types")),
        bool(card.get("attributes")),
    ])


def merge_cards(existing, incoming):
    if not existing:
        return incoming
    preferred, other = (existing, incoming) if quality(existing) >= quality(incoming) else (incoming, existing)
    merged = dict(preferred)
    for key in ["name", "packId", "pack", "packLabel", "rarity", "category", "effect", "trigger", "image", "baseId"]:
        if not merged.get(key) and other.get(key):
            merged[key] = other[key]
    for key in ["cost", "power", "counter"]:
        if merged.get(key) is None and other.get(key) is not None:
            merged[key] = other[key]
    for key in ["colors", "attributes", "types"]:
        vals = []
        for item in as_list(merged.get(key)) + as_list(other.get(key)):
            if item not in vals:
                vals.append(item)
        merged[key] = vals
    sources = []
    for src in [existing.get("source"), incoming.get("source")]:
        if src and src not in sources:
            sources.append(src)
    merged["source"] = " + ".join(sources)
    return merged


def add_card(store, card):
    if not card.get("id") or not card.get("name"):
        return
    # Keep distinct parallel arts/variants by their explicit variant id.
    key = card["id"]
    if key in store:
        store[key] = merge_cards(store[key], card)
    else:
        store[key] = card


def main():
    if not PRIMARY_CARDS.exists() and not SECONDARY_CARDS.exists():
        raise SystemExit("No One Piece source dataset found")

    store = {}
    primary_count = 0
    secondary_count = 0
    pack_titles = primary_pack_titles()

    if PRIMARY_CARDS.exists():
        for file in sorted(PRIMARY_CARDS.rglob("*.json")):
            try:
                parsed = json.loads(file.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"Skipping primary {file}: {exc}")
                continue
            raw_cards = [parsed] if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else []
            for raw in raw_cards:
                if not isinstance(raw, dict):
                    continue
                card = normalize_primary(raw, pack_titles)
                if card.get("id") and card.get("name"):
                    primary_count += 1
                    add_card(store, card)

    if SECONDARY_CARDS.exists():
        for file in sorted(SECONDARY_CARDS.glob("*.json")):
            try:
                parsed = json.loads(file.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"Skipping secondary {file}: {exc}")
                continue
            raw_cards = [parsed] if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else []
            for raw in raw_cards:
                if not isinstance(raw, dict):
                    continue
                card = normalize_secondary(raw, file)
                if card.get("id") and card.get("name"):
                    secondary_count += 1
                    add_card(store, card)

    cards = list(store.values())
    cards.sort(key=lambda c: (c["name"].casefold(), c["baseId"], c["id"], c["packId"]))

    def sorted_unique(values):
        return sorted({str(v).strip() for v in values if str(v).strip()}, key=str.casefold)

    meta = {
        "colors": sorted_unique(x for c in cards for x in c["colors"]),
        "categories": sorted_unique(c["category"] for c in cards),
        "rarities": sorted_unique(c["rarity"] for c in cards),
        "attributes": sorted_unique(x for c in cards for x in c["attributes"]),
        "types": sorted_unique(x for c in cards for x in c["types"]),
        "packs": sorted_unique(c["pack"] for c in cards),
    }

    payload = {
        "source": "Kuroro1990/OPTCG + apitcg/one-piece-tcg-data",
        "language": "en",
        "count": len(cards),
        "coverage": {
            "primaryRecords": primary_count,
            "secondaryRecords": secondary_count,
            "mergedUniqueCards": len(cards),
        },
        "meta": meta,
        "cards": cards,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {len(cards)} One Piece cards to {OUT_FILE}")
    print(f"Sources: primary={primary_count}, secondary={secondary_count}")


if __name__ == "__main__":
    main()
