import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data"
OUT_FILE = OUT_DIR / "yugioh.json"
API_EN = "https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes"
API_PT = "https://db.ygoprodeck.com/api/v7/cardinfo.php?language=pt&misc=yes"

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SertaoTCG/3.0"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)

def normalize(raw, localized=None, artwork=None, artwork_index=0):
    localized = localized or {}
    misc = (raw.get("misc_info") or [{}])[0] or {}
    sets = raw.get("card_sets") or []
    first_set = sets[0] if sets else {}
    artwork = artwork or ((raw.get("card_images") or [{}])[0] or {})
    normalized_sets = [{"name":s.get("set_name",""),"code":s.get("set_code",""),"rarity":s.get("set_rarity",""),"rarityCode":s.get("set_rarity_code",""),"price":s.get("set_price","")} for s in sets if isinstance(s,dict)]
    base_id = raw.get("id")
    image_id = artwork.get("id") or base_id
    return {
        "id": image_id,
        "baseId": base_id,
        "variantId": f"{base_id}:{image_id}:{artwork_index}",
        "artworkIndex": artwork_index,
        "isAltArt": artwork_index > 0 or str(image_id) != str(base_id),
        "konamiId": misc.get("konami_id"),
        "name": localized.get("name") or raw.get("name", ""),
        "nameEn": raw.get("name", ""),
        "type": raw.get("type", ""), "frameType": raw.get("frameType", ""), "race": raw.get("race", ""), "attribute": raw.get("attribute", ""),
        "level": raw.get("level"), "rank": raw.get("level") if "XYZ" in str(raw.get("type","")).upper() else None,
        "linkval": raw.get("linkval"), "linkmarkers": raw.get("linkmarkers") or [], "scale": raw.get("scale"), "atk": raw.get("atk"), "def": raw.get("def"),
        "desc": localized.get("desc") or raw.get("desc", ""), "descEn": raw.get("desc", ""),
        "pendDesc": localized.get("pend_desc") or raw.get("pend_desc", ""), "monsterDesc": localized.get("monster_desc") or raw.get("monster_desc", ""),
        "archetype": raw.get("archetype", ""), "set": first_set.get("set_name", ""), "setCode": first_set.get("set_code", ""), "rarity": first_set.get("set_rarity", ""), "sets": normalized_sets,
        "image": artwork.get("image_url", ""), "imageSmall": artwork.get("image_url_small", ""), "imageCropped": artwork.get("image_url_cropped", ""),
        "tcgDate": misc.get("tcg_date", ""), "ocgDate": misc.get("ocg_date", ""), "formats": misc.get("formats") or []
    }

def main():
    en_cards = (get_json(API_EN).get("data") or [])
    if not en_cards: raise SystemExit("YGOPRODeck English database returned no cards")
    pt_by_id = {}
    try:
        for card in get_json(API_PT).get("data") or []:
            if card.get("id") is not None: pt_by_id[str(card.get("id"))] = card
    except Exception as exc:
        print(f"Portuguese overlay unavailable: {exc}")
    cards=[]; alt_count=0
    for raw in en_cards:
        localized=pt_by_id.get(str(raw.get("id")),{})
        images=raw.get("card_images") or [{}]
        for idx,img in enumerate(images):
            card=normalize(raw,localized,img,idx)
            if card["name"]:
                cards.append(card)
                if card["isAltArt"]: alt_count += 1
    cards.sort(key=lambda c:(str(c["name"]).casefold(),str(c["baseId"]),c["artworkIndex"]))
    payload={"source":"YGOPRODeck EN complete, every card_images artwork + PT overlay","language":"pt/en","count":len(cards),"uniqueCards":len(en_cards),"artworkVariants":alt_count,"coverage":{"englishCards":len(en_cards),"portugueseOverlay":len(pt_by_id),"indexedArtworkRecords":len(cards)},"cards":cards}
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"Wrote {len(cards)} Yu-Gi-Oh searchable artwork records from {len(en_cards)} unique cards; alt artworks={alt_count}")
if __name__ == "__main__": main()
