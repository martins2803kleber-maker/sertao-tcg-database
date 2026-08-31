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
            attacks.append({"name":str(attack.get("name","")).strip(),"cost":clean_list(attack.get("cost")),"convertedEnergyCost":attack.get("convertedEnergyCost"),"damage":str(attack.get("damage","")).strip(),"text":str(attack.get("text","")).strip()})
    abilities = []
    for ability in card.get("abilities") or []:
        if isinstance(ability, dict):
            abilities.append({"name":str(ability.get("name","")).strip(),"text":str(ability.get("text","")).strip(),"type":str(ability.get("type","")).strip()})
    return {
        "id":card_id,"originalId":card_id,"language":"en","name":str(card.get("name","")).strip(),"number":str(card.get("number","")).strip(),
        "setId":set_id,"set":set_info.get("name",set_id),"series":set_info.get("series",""),"releaseDate":set_info.get("releaseDate",""),
        "rarity":card.get("rarity",""),"supertype":card.get("supertype",""),"subtypes":clean_list(card.get("subtypes")),"hp":str(card.get("hp","")).strip(),"types":clean_list(card.get("types")),
        "evolvesFrom":str(card.get("evolvesFrom","")).strip(),"evolvesTo":clean_list(card.get("evolvesTo")),"rules":clean_list(card.get("rules")),"ancientTrait":card.get("ancientTrait") or None,
        "abilities":abilities,"attacks":attacks,"weaknesses":card.get("weaknesses") or [],"resistances":card.get("resistances") or [],"retreatCost":clean_list(card.get("retreatCost")),
        "convertedRetreatCost":card.get("convertedRetreatCost"),"artist":str(card.get("artist","")).strip(),"regulationMark":str(card.get("regulationMark","")).strip(),
        "legalities":{"standard":legalities.get("standard",""),"expanded":legalities.get("expanded",""),"unlimited":legalities.get("unlimited","")},
        "image":images.get("small",""),"imageLarge":images.get("large",""),"source":"PokemonTCG/pokemon-tcg-data"
    }


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"SertaoTCG/4.0"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def fetch_tcgdex(lang):
    cards=[]; page=1; per_page=1000
    while page <= 100:
        query=urllib.parse.urlencode({"pagination:page":page,"pagination:itemsPerPage":per_page})
        batch=get_json(f"{TCGDEX_BASE}/{lang}/cards?{query}")
        if not isinstance(batch,list) or not batch: break
        cards.extend(batch)
        print(f"TCGdex {lang} page {page}: {len(batch)} cards")
        if len(batch) < per_page: break
        page += 1
    return cards


def normalize_tcgdex(raw, lang):
    original_id=str(raw.get("id","")).strip()
    set_id=original_id.rsplit("-",1)[0] if "-" in original_id else ""
    image_base=str(raw.get("image","") or "").rstrip("/")
    public_id=original_id if lang == "en" else f"JP:{original_id}"
    return {
        "id":public_id,"originalId":original_id,"language":lang,"name":str(raw.get("name","") or "").strip(),"number":str(raw.get("localId","") or "").strip(),
        "setId":set_id,"set":set_id,"series":"","releaseDate":"","rarity":"","supertype":"","subtypes":[],"hp":"","types":[],"evolvesFrom":"","evolvesTo":[],"rules":[],
        "ancientTrait":None,"abilities":[],"attacks":[],"weaknesses":[],"resistances":[],"retreatCost":[],"convertedRetreatCost":None,"artist":"","regulationMark":"",
        "legalities":{"standard":"","expanded":"","unlimited":""},"image":f"{image_base}/low.webp" if image_base else "","imageLarge":f"{image_base}/high.webp" if image_base else "",
        "source":f"TCGdex {lang}"
    }


def sorted_unique(values):
    return sorted({str(v).strip() for v in values if str(v).strip()}, key=str.casefold)


def main():
    if not CARDS_DIR.exists() or not SETS_FILE.exists():
        raise SystemExit("Official Pokemon TCG dataset not found")
    sets=json.loads(SETS_FILE.read_text(encoding="utf-8")); sets_by_id={s.get("id",""):s for s in sets}
    by_key={}; official_count=0
    for file in sorted(CARDS_DIR.glob("*.json")):
        try: raw_cards=json.loads(file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Skipping {file.name}: {exc}"); continue
        for raw in raw_cards:
            card=normalize_card(raw,sets_by_id)
            if card["id"] and card["name"]:
                by_key[f"en:{card['originalId']}"]=card; official_count += 1

    coverage={"officialEnglish":official_count}
    for lang in ("en","ja"):
        try:
            briefs=fetch_tcgdex(lang); coverage[f"tcgdex_{lang}"]=len(briefs); added=0
            for raw in briefs:
                card=normalize_tcgdex(raw,lang)
                if not card["originalId"] or not card["name"]: continue
                key=f"{lang}:{card['originalId']}"
                if key not in by_key:
                    by_key[key]=card; added += 1
                else:
                    existing=by_key[key]
                    if not existing.get("image") and card.get("image"): existing["image"]=card["image"]
                    if not existing.get("imageLarge") and card.get("imageLarge"): existing["imageLarge"]=card["imageLarge"]
            coverage[f"tcgdex_{lang}_added"]=added
        except Exception as exc:
            print(f"TCGdex {lang} unavailable: {exc}")

    cards=list(by_key.values())
    cards.sort(key=lambda c:(c.get("language",""),c["name"].casefold(),c.get("set",""),c.get("number","")))
    coverage["mergedSearchableRecords"]=len(cards)
    meta={"languages":sorted_unique(c.get("language","") for c in cards),"supertypes":sorted_unique(c["supertype"] for c in cards),"subtypes":sorted_unique(s for c in cards for s in c["subtypes"]),"types":sorted_unique(t for c in cards for t in c["types"]),"rarities":sorted_unique(c["rarity"] for c in cards),"sets":sorted_unique(c["set"] for c in cards)}
    payload={"source":"PokemonTCG English + TCGdex English/Japanese","language":"en/ja","count":len(cards),"coverage":coverage,"meta":meta,"cards":cards}
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"Wrote {len(cards)} Pokemon searchable records")
    print(coverage)

if __name__ == "__main__": main()
