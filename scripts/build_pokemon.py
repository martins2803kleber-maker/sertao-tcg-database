import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "pokemon-tcg-data"
CARDS_DIR = SOURCE / "cards" / "en"
SETS_FILE = SOURCE / "sets" / "en.json"
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "pokemon.json"
TCGDEX_URL = "https://api.tcgdex.net/v2/en/cards"


def clean_list(value):
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_card(card, sets_by_id):
    card_id = str(card.get("id", "")).strip()
    set_id = card_id.rsplit("-", 1)[0] if "-" in card_id else ""
    set_info = sets_by_id.get(set_id, {})
    images = card.get("images") or {}
    legalities = card.get("legalities") or {}

    attacks = []
    for attack in card.get("attacks") or []:
        if not isinstance(attack, dict):
            continue
        attacks.append({
            "name": str(attack.get("name", "")).strip(),
            "cost": clean_list(attack.get("cost")),
            "convertedEnergyCost": attack.get("convertedEnergyCost"),
            "damage": str(attack.get("damage", "")).strip(),
            "text": str(attack.get("text", "")).strip(),
        })

    abilities = []
    for ability in card.get("abilities") or []:
        if not isinstance(ability, dict):
            continue
        abilities.append({
            "name": str(ability.get("name", "")).strip(),
            "text": str(ability.get("text", "")).strip(),
            "type": str(ability.get("type", "")).strip(),
        })

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
        "subtypes": clean_list(card.get("subtypes")),
        "hp": str(card.get("hp", "")).strip(),
        "types": clean_list(card.get("types")),
        "evolvesFrom": str(card.get("evolvesFrom", "")).strip(),
        "evolvesTo": clean_list(card.get("evolvesTo")),
        "rules": clean_list(card.get("rules")),
        "ancientTrait": card.get("ancientTrait") or None,
        "abilities": abilities,
        "attacks": attacks,
        "weaknesses": card.get("weaknesses") or [],
        "resistances": card.get("resistances") or [],
        "retreatCost": clean_list(card.get("retreatCost")),
        "convertedRetreatCost": card.get("convertedRetreatCost"),
        "artist": str(card.get("artist", "")).strip(),
        "regulationMark": str(card.get("regulationMark", "")).strip(),
        "legalities": {
            "standard": legalities.get("standard", ""),
            "expanded": legalities.get("expanded", ""),
            "unlimited": legalities.get("unlimited", ""),
        },
        "image": images.get("small", ""),
        "imageLarge": images.get("large", ""),
        "source": "PokemonTCG/pokemon-tcg-data",
    }


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SertaoTCG/2.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def fetch_tcgdex_briefs():
    cards = []
    page = 1
    per_page = 1000
    while page <= 100:
        query = urllib.parse.urlencode({
            "pagination:page": page,
            "pagination:itemsPerPage": per_page,
        })
        batch = get_json(f"{TCGDEX_URL}?{query}")
        if not isinstance(batch, list) or not batch:
            break
        cards.extend(batch)
        print(f"TCGdex page {page}: {len(batch)} cards")
        if len(batch) < per_page:
            break
        page += 1
    return cards


def normalize_tcgdex_brief(raw):
    card_id = str(raw.get("id", "")).strip()
    set_id = card_id.rsplit("-", 1)[0] if "-" in card_id else ""
    image_base = str(raw.get("image", "") or "").rstrip("/")
    local_id = str(raw.get("localId", "") or "").strip()
    return {
        "id": card_id,
        "name": str(raw.get("name", "") or "").strip(),
        "number": local_id,
        "setId": set_id,
        "set": set_id,
        "series": "",
        "releaseDate": "",
        "rarity": "",
        "supertype": "",
        "subtypes": [],
        "hp": "",
        "types": [],
        "evolvesFrom": "",
        "evolvesTo": [],
        "rules": [],
        "ancientTrait": None,
        "abilities": [],
        "attacks": [],
        "weaknesses": [],
        "resistances": [],
        "retreatCost": [],
        "convertedRetreatCost": None,
        "artist": "",
        "regulationMark": "",
        "legalities": {"standard": "", "expanded": "", "unlimited": ""},
        "image": f"{image_base}/low.webp" if image_base else "",
        "imageLarge": f"{image_base}/high.webp" if image_base else "",
        "source": "TCGdex",
    }


def sorted_unique(values):
    return sorted({str(v).strip() for v in values if str(v).strip()}, key=str.casefold)


def main():
    if not CARDS_DIR.exists() or not SETS_FILE.exists():
        raise SystemExit("Official Pokemon TCG dataset not found in source/pokemon-tcg-data")

    sets = json.loads(SETS_FILE.read_text(encoding="utf-8"))
    sets_by_id = {s.get("id", ""): s for s in sets}

    by_id = {}
    primary_count = 0
    for file in sorted(CARDS_DIR.glob("*.json")):
        try:
            raw_cards = json.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Skipping {file.name}: {exc}")
            continue

        for raw in raw_cards:
            card = normalize_card(raw, sets_by_id)
            if not card["name"] or not card["id"]:
                continue
            by_id[card["id"]] = card
            primary_count += 1

    tcgdex_count = 0
    tcgdex_added = 0
    try:
        tcgdex_cards = fetch_tcgdex_briefs()
        tcgdex_count = len(tcgdex_cards)
        for raw in tcgdex_cards:
            card = normalize_tcgdex_brief(raw)
            if not card["id"] or not card["name"]:
                continue
            if card["id"] not in by_id:
                by_id[card["id"]] = card
                tcgdex_added += 1
            else:
                existing = by_id[card["id"]]
                if not existing.get("image") and card.get("image"):
                    existing["image"] = card["image"]
                if not existing.get("imageLarge") and card.get("imageLarge"):
                    existing["imageLarge"] = card["imageLarge"]
                existing["source"] = "PokemonTCG/pokemon-tcg-data + TCGdex"
    except Exception as exc:
        print(f"TCGdex supplement unavailable, keeping official dataset: {exc}")

    cards = list(by_id.values())
    cards.sort(key=lambda c: (c["name"].casefold(), c["releaseDate"], c["set"], c["number"]))

    meta = {
        "supertypes": sorted_unique(c["supertype"] for c in cards),
        "subtypes": sorted_unique(s for c in cards for s in c["subtypes"]),
        "types": sorted_unique(t for c in cards for t in c["types"]),
        "rarities": sorted_unique(c["rarity"] for c in cards),
        "sets": sorted_unique(c["set"] for c in cards),
        "series": sorted_unique(c["series"] for c in cards),
        "artists": sorted_unique(c["artist"] for c in cards),
        "regulationMarks": sorted_unique(c["regulationMark"] for c in cards),
    }

    payload = {
        "source": "PokemonTCG/pokemon-tcg-data + TCGdex supplement",
        "language": "en",
        "count": len(cards),
        "coverage": {
            "officialRecords": primary_count,
            "tcgdexRecords": tcgdex_count,
            "tcgdexAdded": tcgdex_added,
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
    print(f"Wrote {len(cards)} cards to {OUT_FILE}")
    print(f"Coverage: official={primary_count}, tcgdex={tcgdex_count}, added={tcgdex_added}")


if __name__ == "__main__":
    main()
