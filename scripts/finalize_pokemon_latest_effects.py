import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from enrich_pokemon_descriptions import (
    DB_FILE,
    JWA_30C,
    POKEBEACH_DELTA,
    apply_external_description,
    dedupe_cards,
    fetch_html,
    norm,
    norm_number,
    norm_set,
)


def parse_delta_trainers(html):
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
        tag = getattr(sib, "name", None)
        if tag == "h2":
            break
        if tag == "hr":
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
    for chunk in chunks:
        if not chunk:
            continue
        m = re.match(r"^(.+?)\s+-\s+Trainer\b", chunk[0], flags=re.I)
        if not m:
            continue
        name = m.group(1).strip()
        out[norm(name)] = {
            "description": "\n".join(chunk).strip(),
            "source": "PokeBeach Storm Emeralda translation tracker",
            "status": "community translation until official English localization",
        }
    return out


def parse_30c_english_number_text(html):
    soup = BeautifulSoup(html, "html.parser")
    headings = soup.find_all(["h2", "h3"])
    active = False
    by_number = {}

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

        pieces = []
        for sib in heading.next_siblings:
            tag = getattr(sib, "name", None)
            if tag in ("h2", "h3"):
                break
            if hasattr(sib, "get_text"):
                text = sib.get_text(" ", strip=True)
            else:
                text = str(sib).strip()
            if text:
                pieces.append(text)

        joined = "\n".join(pieces)
        m = re.search(r"\b(\d{3})/128\b", joined)
        if not m:
            continue

        description = ""
        for piece in pieces:
            if "Type:" in piece and ("HP:" in piece or "Pokémon" in piece or "Pokemon" in piece):
                description = piece.strip()
                break
        if not description:
            continue

        number = norm_number(m.group(1))
        by_number[number] = {
            "description": description,
            "source": "Joseph Writer Anderson 30th Celebration translation tracker",
            "status": "English translation/reveal tracker; verify official wording after release",
        }

    return by_number


def main():
    payload = json.loads(Path(DB_FILE).read_text(encoding="utf-8"))
    cards = payload.get("cards") or []

    delta_trainers = {}
    c30_by_number = {}

    try:
        delta_trainers = parse_delta_trainers(fetch_html(POKEBEACH_DELTA))
    except Exception as exc:
        print(f"Delta trainer text unavailable: {exc}")

    try:
        c30_by_number = parse_30c_english_number_text(fetch_html(JWA_30C))
    except Exception as exc:
        print(f"30th English-number text unavailable: {exc}")

    delta_added = 0
    c30_added = 0

    for card in cards:
        sid = norm_set(card.get("setId"))
        set_name = norm(card.get("set"))
        name_key = norm(card.get("nameEn") or card.get("name") or card.get("namePt") or card.get("nameJa"))
        number = norm_number(card.get("number"))

        is_delta = sid == "m6" or "delta reign" in set_name or "storm emeralda" in set_name
        if is_delta and name_key in delta_trainers:
            rec = delta_trainers[name_key]
            if apply_external_description(card, rec["description"], rec["source"], rec["status"]):
                delta_added += 1

        is_30c = sid == "30c" or "30th celebration" in set_name
        if is_30c and number in c30_by_number:
            rec = c30_by_number[number]
            if apply_external_description(card, rec["description"], rec["source"], rec["status"]):
                c30_added += 1

    cards, duplicate_count = dedupe_cards(cards)

    latest_missing = 0
    latest_total = 0
    for card in cards:
        sid = norm_set(card.get("setId"))
        set_name = norm(card.get("set"))
        is_latest = (
            sid in ("m6", "30c", "m6a")
            or "delta reign" in set_name
            or "storm emeralda" in set_name
            or "30th celebration" in set_name
        )
        if not is_latest:
            continue
        latest_total += 1
        if not (card.get("description") or card.get("desc") or card.get("effectText")):
            latest_missing += 1

    cards.sort(key=lambda c: (
        str(c.get("namePt") or c.get("nameEn") or c.get("name") or "").casefold(),
        str(c.get("set") or "").casefold(),
        norm_number(c.get("number")),
        str(c.get("id") or ""),
    ))

    payload["cards"] = cards
    payload["count"] = len(cards)
    coverage = payload.setdefault("coverage", {})
    coverage["deltaTrainerDescriptionsAdded"] = delta_added
    coverage["celebration30EnglishNumberDescriptionsAdded"] = c30_added
    coverage["duplicatesRemovedFinalPass"] = duplicate_count
    coverage["latestCardsTotalFinal"] = latest_total
    coverage["latestCardsStillWithoutDescriptionFinal"] = latest_missing
    coverage["mergedSearchableRecords"] = len(cards)

    Path(DB_FILE).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Delta trainer descriptions applied: {delta_added}")
    print(f"30th /128 descriptions applied: {c30_added}")
    print(f"Final duplicate records removed: {duplicate_count}")
    print(f"Latest cards with no effect text remaining: {latest_missing}/{latest_total}")
    print(f"Pokemon final count: {len(cards)}")


if __name__ == "__main__":
    main()
