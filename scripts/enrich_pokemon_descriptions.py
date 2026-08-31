import json
import re
import unicodedata
import urllib.request
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError as exc:
    raise SystemExit("beautifulsoup4 is required") from exc

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / "data" / "pokemon.json"

POKEBEACH_DELTA = "https://www.pokebeach.com/2026/07/storm-emeralda-all-76-main-set-cards-revealed"
JWA_30C = "https://www.josephwriteranderson.com/blog/entire-pokmon-30th-celebration-set-list-revealed"


def fetch_html(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 SertaoTCG/8.0 (+catalog effect updater)"
    })
    with urllib.request.urlopen(req, timeout=180) as response:
        return response.read().decode("utf-8", errors="replace")


def norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text


def norm_set(value):
    return re.sub(r"[^a-z0-9]", "", norm(value))


def norm_number(value):
    s = str(value or "").strip().upper()
    if not s:
        return ""
    m = re.fullmatch(r"0*(\d+)([A-Z]*)", s)
    if m:
        return f"{int(m.group(1))}{m.group(2)}"
    return re.sub(r"[^A-Z0-9]", "", s)


def canonical_key(card):
    sid = norm_set(card.get("setId"))
    number = norm_number(card.get("number"))
    if sid and number:
        return f"set:{sid}|num:{number}"
    oid = norm(card.get("originalId") or card.get("id"))
    if oid:
        return f"id:{oid}"
    return f"fallback:{norm(card.get('name'))}|{norm(card.get('set'))}|{number}"


def uniq_list(values):
    out = []
    seen = set()
    for item in values or []:
        token = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if token in seen:
            continue
        seen.add(token)
        out.append(item)
    return out


def richness(card):
    score = 0
    for field in ("imageLarge", "image", "namePt", "nameEn", "nameJa", "hp", "artist", "rarity", "regulationMark"):
        if card.get(field):
            score += 2
    score += 5 * len(card.get("attacks") or [])
    score += 5 * len(card.get("abilities") or [])
    score += 3 * len(card.get("rules") or [])
    if card.get("description") or card.get("desc") or card.get("effectText"):
        score += 8
    if card.get("source", "").startswith("PokemonTCG/"):
        score += 4
    return score


def merge_cards(a, b):
    if richness(b) > richness(a):
        a, b = b, a
    merged = dict(a)

    for field in (
        "namePt", "nameEn", "nameJa", "name", "image", "imageLarge", "hp", "rarity",
        "supertype", "artist", "regulationMark", "series", "releaseDate", "description",
        "desc", "effectText", "translationSource", "descriptionStatus"
    ):
        if not merged.get(field) and b.get(field):
            merged[field] = b[field]

    for field in (
        "subtypes", "types", "evolvesTo", "rules", "abilities", "attacks",
        "weaknesses", "resistances", "retreatCost", "languages"
    ):
        merged[field] = uniq_list((merged.get(field) or []) + (b.get(field) or []))

    if not merged.get("evolvesFrom") and b.get("evolvesFrom"):
        merged["evolvesFrom"] = b["evolvesFrom"]
    if merged.get("convertedRetreatCost") is None and b.get("convertedRetreatCost") is not None:
        merged["convertedRetreatCost"] = b["convertedRetreatCost"]
    if not merged.get("ancientTrait") and b.get("ancientTrait"):
        merged["ancientTrait"] = b["ancientTrait"]

    sources = []
    for src in str(merged.get("source", "")).split(" + ") + str(b.get("source", "")).split(" + "):
        src = src.strip()
        if src and src not in sources:
            sources.append(src)
    merged["source"] = " + ".join(sources)
    return merged


def dedupe_cards(cards):
    store = {}
    duplicate_count = 0
    for card in cards:
        key = canonical_key(card)
        if key in store:
            store[key] = merge_cards(store[key], card)
            duplicate_count += 1
        else:
            store[key] = card
    return list(store.values()), duplicate_count


def structured_description(card):
    lines = []

    ancient = card.get("ancientTrait")
    if isinstance(ancient, dict):
        name = str(ancient.get("name", "")).strip()
        text = str(ancient.get("text", "")).strip()
        if name or text:
            lines.append(("Ancient Trait: " + name + (" — " if name and text else "") + text).strip())

    for ability in card.get("abilities") or []:
        if not isinstance(ability, dict):
            continue
        name = str(ability.get("name", "")).strip()
        text = str(ability.get("text", "")).strip()
        kind = str(ability.get("type", "") or "Ability").strip()
        line = f"{kind}: {name}" if name else kind
        if text:
            line += f" — {text}"
        lines.append(line)

    for attack in card.get("attacks") or []:
        if not isinstance(attack, dict):
            continue
        cost = "".join(f"[{x}]" for x in (attack.get("cost") or []))
        name = str(attack.get("name", "")).strip()
        damage = str(attack.get("damage", "")).strip()
        text = str(attack.get("text", "")).strip()
        head = " ".join(x for x in (cost, name, damage) if x).strip()
        if text:
            head += (" — " if head else "") + text
        if head:
            lines.append(head)

    for rule in card.get("rules") or []:
        rule = str(rule or "").strip()
        if rule:
            lines.append(rule)

    return "\n".join(uniq_list(lines)).strip()


def parse_delta_translations(html):
    soup = BeautifulSoup(html, "html.parser")
    heading = None
    for h2 in soup.find_all("h2"):
        if "Main Set Card Translations" in h2.get_text(" ", strip=True):
            heading = h2
            break
    if not heading:
        return {}

    chunks = []
    current = []
    for sib in heading.next_siblings:
        name = getattr(sib, "name", None)
        if name == "h2":
            break
        if name == "hr":
            if current:
                chunks.append(current)
                current = []
            continue
        if hasattr(sib, "get_text"):
            text = sib.get_text(" ", strip=True)
        else:
            text = str(sib).strip()
        if text:
            current.append(text)
    if current:
        chunks.append(current)

    out = {}
    header_re = re.compile(
        r"^(.+?)\s+-\s+(Grass|Fire|Water|Lightning|Psychic|Fighting|Darkness|Metal|Dragon|Colorless)\s+-\s+HP\s*\d+",
        re.I,
    )

    for chunk in chunks:
        if not chunk:
            continue
        m = header_re.search(chunk[0])
        if not m:
            continue
        card_name = m.group(1).strip()
        description = "\n".join(chunk).strip()
        if card_name and description:
            out[norm(card_name)] = {
                "description": description,
                "source": "PokeBeach Storm Emeralda translation tracker",
                "status": "community translation until official English localization",
            }
    return out


def parse_30c_translations(html):
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.find_all(["h2", "h3"])
    active = False
    records = []

    for heading in headings:
        title = heading.get_text(" ", strip=True)
        if heading.name == "h2":
            if "30th Celebration Main Set List with English Translations" in title:
                active = True
                continue
            if active:
                break
        if not active or heading.name != "h3":
            continue

        name = title.strip()
        pieces = []
        for sib in heading.next_siblings:
            sib_name = getattr(sib, "name", None)
            if sib_name in ("h2", "h3"):
                break
            if hasattr(sib, "get_text"):
                text = sib.get_text(" ", strip=True)
            else:
                text = str(sib).strip()
            if text:
                pieces.append(text)
        joined = "\n".join(pieces).strip()
        if not joined:
            continue

        number_match = re.search(r"\b(\d{3})/(?:128|103)\b", joined)
        number = norm_number(number_match.group(1)) if number_match else ""

        desc = ""
        for piece in pieces:
            if "Type:" in piece and ("HP:" in piece or "Pokémon" in piece or "Pokemon" in piece):
                desc = piece.strip()
                break
        if not desc:
            continue
        records.append({
            "name": name,
            "name_norm": norm(name),
            "number": number,
            "description": desc,
            "source": "Joseph Writer Anderson 30th Celebration translation tracker",
            "status": "English translation/reveal tracker; verify official wording after release",
        })

    exact = {}
    by_name = {}
    for rec in records:
        if rec["number"]:
            exact[(rec["name_norm"], rec["number"])] = rec
        by_name.setdefault(rec["name_norm"], []).append(rec)
    return exact, by_name


def apply_external_description(card, description, source, status):
    description = str(description or "").strip()
    if not description:
        return False
    existing = structured_description(card)
    if existing and len(existing) >= max(120, len(description) // 2):
        final = existing
    else:
        final = description
        # The recent supplemental cards do not yet have structured attacks/abilities.
        # Keeping the translated text in rules makes older Blogger modal renderers show it too.
        if not card.get("abilities") and not card.get("attacks"):
            rules = list(card.get("rules") or [])
            if description not in rules:
                rules.append(description)
            card["rules"] = rules
    card["description"] = final
    card["desc"] = final
    card["effectText"] = final
    card["translationSource"] = source
    card["descriptionStatus"] = status
    return True


def enrich(cards):
    stats = {
        "duplicatesRemoved": 0,
        "structuredDescriptions": 0,
        "deltaDescriptionsAdded": 0,
        "celebration30DescriptionsAdded": 0,
        "descriptionsAvailable": 0,
        "latestCardsStillWithoutDescription": 0,
    }

    cards, duplicates = dedupe_cards(cards)
    stats["duplicatesRemoved"] = duplicates

    delta = {}
    try:
        delta = parse_delta_translations(fetch_html(POKEBEACH_DELTA))
        print(f"Delta translation records parsed: {len(delta)}")
    except Exception as exc:
        print(f"Delta translation source unavailable: {exc}")

    c30_exact, c30_by_name = {}, {}
    try:
        c30_exact, c30_by_name = parse_30c_translations(fetch_html(JWA_30C))
        print(f"30th translation records parsed: {len(c30_exact)} exact / {len(c30_by_name)} names")
    except Exception as exc:
        print(f"30th translation source unavailable: {exc}")

    for card in cards:
        # First create a universal text field from structured data for every older card.
        existing = structured_description(card)
        if existing:
            card["description"] = existing
            card["desc"] = existing
            card["effectText"] = existing
            stats["structuredDescriptions"] += 1

        sid = norm_set(card.get("setId"))
        set_name = norm(card.get("set"))
        name_key = norm(card.get("nameEn") or card.get("name") or card.get("namePt") or card.get("nameJa"))
        number = norm_number(card.get("number"))

        is_delta = sid == "m6" or "delta reign" in set_name or "storm emeralda" in set_name
        if is_delta and name_key in delta:
            rec = delta[name_key]
            if apply_external_description(card, rec["description"], rec["source"], rec["status"]):
                stats["deltaDescriptionsAdded"] += 1

        is_30c = sid in ("30c", "m6a") or "30th celebration" in set_name
        if is_30c:
            rec = c30_exact.get((name_key, number))
            if not rec:
                candidates = c30_by_name.get(name_key) or []
                if len(candidates) == 1:
                    rec = candidates[0]
            if rec and apply_external_description(card, rec["description"], rec["source"], rec["status"]):
                stats["celebration30DescriptionsAdded"] += 1

        if card.get("description") or card.get("desc") or card.get("effectText"):
            stats["descriptionsAvailable"] += 1
        elif is_delta or is_30c:
            stats["latestCardsStillWithoutDescription"] += 1

    cards, duplicates2 = dedupe_cards(cards)
    stats["duplicatesRemoved"] += duplicates2
    cards.sort(key=lambda c: (
        str(c.get("namePt") or c.get("nameEn") or c.get("name") or "").casefold(),
        str(c.get("set") or "").casefold(),
        norm_number(c.get("number")),
        str(c.get("id") or ""),
    ))
    return cards, stats


def main():
    payload = json.loads(DB_FILE.read_text(encoding="utf-8"))
    cards = payload.get("cards") or []
    cards, stats = enrich(cards)

    payload["cards"] = cards
    payload["count"] = len(cards)
    coverage = payload.setdefault("coverage", {})
    coverage.update(stats)
    coverage["mergedSearchableRecords"] = len(cards)

    meta = payload.setdefault("meta", {})
    meta["sets"] = sorted({str(c.get("set", "")).strip() for c in cards if str(c.get("set", "")).strip()}, key=str.casefold)

    DB_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Pokemon final catalog after dedupe/effects: {len(cards)}")
    print(stats)


if __name__ == "__main__":
    main()
