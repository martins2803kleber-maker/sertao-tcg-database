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
TCGDEX_BASE = "https://api.tcgdex.net/v2"


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
        if isinstance(attack, dict):
            attacks.append({
                "name": str(attack.get("name", "")).strip(),
                "cost": clean_list(attack.get("cost")),
                "convertedEnergyCost": attack.get("convertedEnergyCost"),
                "damage": str(attack.get("damage", "")).strip(),
                "text": str(attack.get("text", "")).strip(),
            })
    abilities = []
    for ability in card.get("abilities") or []:
        if isinstance(ability, dict):
            abilities.append({
                "name": str(ability.get("name", "")).strip(),
                "text": str(ability.get("text", "")).strip(),
                "type": str(ability.get("type", "")).strip(),
            })
    return {
        "id": card_id,
        "originalId": card_id,
        "language": "en",
        "languages": ["en"],
        "name": str(card.get("name", "")).strip(),
        "nameJa": "",
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
    req = urllib.request.Request(url, headers={"User-Agent": "SertaoTCG/5.0"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def fetch_tcgdex(lang):
    cards = []
    page = 1
    per_page = 1000
    while page <= 100:
        query = urllib.parse.urlencode({"pagination:page": page, "pagination:itemsPerPage": per_page})
        batch = get_json(f"{TCGDEX_BASE}/{lang}/cards?{query}")
        if not isinstance(batch, list) or not batch:
            break
        cards.extend(batch)
        print(f"TCGdex {lang} page {page}: {len(batch)} cards")
        if len(batch) < per_page:
            break
        page += 1
    return cards


def image_urls(raw):
    image_base = str(raw.get("image", "") or "").rstrip("/")
    if not image_base:
        return "", ""
    return f"{image_base}/low.webp", f"{image_base}/high.webp"


def normalize_tcgdex(raw, lang):
    original_id = str(raw.get("id", "")).strip()
    set_id = original_id.rsplit("-", 1)[0] if "-" in original_id else ""
    image, image_large = image_urls(raw)
    return {
        "id": original_id,
        "originalId": original_id,
        "language": lang,
        "languages": [lang],
        "name": str(raw.get("name", "") or "").strip(),
        "nameJa": str(raw.get("name", "") or "").strip() if lang == "ja" else "",
        "number": str(raw.get("localId", "") or "").strip(),
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
        "image": image,
        "imageLarge": image_large,
        "source": f"TCGdex {lang}",
    }


def merge_language(existing, incoming):
    if not existing:
        return incoming
    merged = dict(existing)
    langs = list(merged.get("languages") or [merged.get("language", "en")])
    for lang in incoming.get("languages") or [incoming.get("language", "")]:
        if lang and lang not in langs:
            langs.append(lang)
    merged["languages"] = langs

    if incoming.get("language") == "ja":
        merged["nameJa"] = incoming.get("name") or merged.get("nameJa", "")
    elif not merged.get("name"):
        merged["name"] = incoming.get("name", "")

    if not merged.get("image") and incoming.get("image"):
        merged["image"] = incoming["image"]
    if not merged.get("imageLarge") and incoming.get("imageLarge"):
        merged["imageLarge"] = incoming["imageLarge"]

    sources = []
    for src in str(merged.get("source", "")).split(" + ") + str(incoming.get("source", "")).split(" + "):
        if src and src not in sources:
            sources.append(src)
    merged["source"] = " + ".join(sources)
    return merged


def sorted_unique(values):
    return sorted({str(v).strip() for v in values if str(v).strip()}, key=str.casefold)


def main():
    if not CARDS_DIR.exists() or not SETS_FILE.exists():
        raise SystemExit("Official Pokemon TCG dataset not found")

    sets = json.loads(SETS_FILE.read_text(encoding="utf-8"))
    sets_by_id = {s.get("id", ""): s for s in sets}
    store = {}
    official_count = 0

    for file in sorted(CARDS_DIR.glob("*.json")):
        try:
            raw_cards = json.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Skipping {file.name}: {exc}")
            continue
        for raw in raw_cards:
            card = normalize_card(raw, sets_by_id)
            if card["id"] and card["name"]:
                store[card["originalId"]] = card
                official_count += 1

    coverage = {"officialEnglish": official_count}

    try:
        briefs_en = fetch_tcgdex("en")
        coverage["tcgdex_en"] = len(briefs_en)
        en_added = 0
        for raw in briefs_en:
            card = normalize_tcgdex(raw, "en")
            cid = card["originalId"]
            if not cid or not card["name"]:
                continue
            if cid not in store:
                store[cid] = card
                en_added += 1
            else:
                store[cid] = merge_language(store[cid], card)
        coverage["tcgdex_en_added"] = en_added
    except Exception as exc:
        print(f"TCGdex en unavailable: {exc}")

    try:
        briefs_ja = fetch_tcgdex("ja")
        coverage["tcgdex_ja"] = len(briefs_ja)
        ja_merged = 0
        ja_only_added = 0
        ja_skipped_no_image = 0
        for raw in briefs_ja:
            card = normalize_tcgdex(raw, "ja")
            cid = card["originalId"]
            if not cid or not card["name"]:
                continue
            if cid in store:
                store[cid] = merge_language(store[cid], card)
                ja_merged += 1
                continue
            # A Japanese-only printing is useful only when it has a real scan.
            # This prevents blank/broken cards in the public catalog.
            if not card.get("image"):
                ja_skipped_no_image += 1
                continue
            store[cid] = card
            ja_only_added += 1
        coverage["tcgdex_ja_mergedWithExisting"] = ja_merged
        coverage["tcgdex_ja_only_added"] = ja_only_added
        coverage["tcgdex_ja_skipped_no_image"] = ja_skipped_no_image
    except Exception as exc:
        print(f"TCGdex ja unavailable: {exc}")

    # Final hard guarantee: never publish a card without an image.
    before_image_filter = len(store)
    store = {k: v for k, v in store.items() if v.get("image") or v.get("imageLarge")}
    coverage["removedWithoutImageFinal"] = before_image_filter - len(store)

    cards = list(store.values())
    cards.sort(key=lambda c: (c["name"].casefold(), c.get("set", ""), c.get("number", ""), c.get("id", "")))
    coverage["mergedSearchableRecords"] = len(cards)
    coverage["japaneseOnlySearchable"] = sum(1 for c in cards if c.get("language") == "ja" and c.get("languages") == ["ja"])
    coverage["multilingualMerged"] = sum(1 for c in cards if "ja" in (c.get("languages") or []) and "en" in (c.get("languages") or []))

    meta = {
        "languages": sorted_unique(lang for c in cards for lang in (c.get("languages") or [c.get("language", "")])),
        "supertypes": sorted_unique(c["supertype"] for c in cards),
        "subtypes": sorted_unique(s for c in cards for s in c["subtypes"]),
        "types": sorted_unique(t for c in cards for t in c["types"]),
        "rarities": sorted_unique(c["rarity"] for c in cards),
        "sets": sorted_unique(c["set"] for c in cards),
    }
    payload = {
        "source": "PokemonTCG English + TCGdex English/Japanese (language-deduplicated)",
        "language": "en with ja metadata / ja-only when unique",
        "count": len(cards),
        "coverage": coverage,
        "meta": meta,
        "cards": cards,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(cards)} Pokemon unique searchable records")
    print(coverage)


if __name__ == "__main__":
    main()
