#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "assets" / "widgets" / "daily_card.json"

GAMES = ["pokemon", "yugioh", "onepiece"]


def load_cards(game):
    raw = json.loads((DATA / f"{game}.json").read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("cards"), list):
        return raw["cards"]
    return []


def first(*values):
    for v in values:
        if v not in (None, "", []):
            return v
    return ""


def image_candidates(game, c):
    out = []
    def add(v):
        if isinstance(v, str) and v.strip() and v.strip() not in out:
            out.append(v.strip())

    if game == "pokemon":
        add(c.get("imageLarge")); add(c.get("image")); add(c.get("imageSmall"))
        imgs = c.get("images") or {}
        if isinstance(imgs, dict):
            add(imgs.get("large")); add(imgs.get("small"))
    elif game == "yugioh":
        add(c.get("image")); add(c.get("imageUrl")); add(c.get("image_url"))
        ci = c.get("card_images") or []
        if ci and isinstance(ci[0], dict):
            add(ci[0].get("image_url")); add(ci[0].get("image_url_small"))
        cid = first(c.get("id"), c.get("cardId"))
        if cid:
            add(f"https://images.ygoprodeck.com/images/cards/{cid}.jpg")
    else:
        code = str(first(c.get("baseId"), c.get("originalId"), c.get("id"))).upper()
        if "_" in code:
            code = code.split("_")[0]
        if code and "-" in code:
            set_code = code.split("-")[0]
            out.append(f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece/{set_code}/{code}_EN.webp")
            out.append(f"https://en.onepiece-cardgame.com/images/cardlist/card/{code}.png")
        add(c.get("image")); add(c.get("imageLarge")); add(c.get("imageEn")); add(c.get("imageUrl")); add(c.get("image_url"))
    return out


def compact(game, c, date_key):
    name = first(c.get("namePt"), c.get("nameEn"), c.get("name"), c.get("nameJa"), "Carta do dia")
    if game == "pokemon":
        code = first(c.get("localId"), c.get("id"), c.get("number"))
        effect_bits = []
        for k in ("description", "effect"):
            if c.get(k): effect_bits.append(str(c[k]))
        for a in c.get("attacks") or []:
            if isinstance(a, dict):
                t = str(first(a.get("name"), "Ataque"))
                if a.get("damage"): t += f" — {a['damage']}"
                if a.get("effect"): t += f"\n{a['effect']}"
                effect_bits.append(t)
        meta = {
            "Tipo": first(c.get("category"), c.get("supertype")),
            "Raridade": c.get("rarity", ""), "HP": c.get("hp", ""),
        }
    elif game == "yugioh":
        code = first(c.get("id"), c.get("cardId"))
        effect_bits = [str(first(c.get("desc"), c.get("description"), c.get("effect"), "Sem texto disponível."))]
        meta = {"Tipo": c.get("type", ""), "Atributo": c.get("attribute", ""), "Raça": c.get("race", ""), "ATK": c.get("atk", ""), "DEF": c.get("def", "")}
    else:
        code = first(c.get("baseId"), c.get("originalId"), c.get("id"))
        effect_bits = [str(first(c.get("effect"), c.get("effectEn"), c.get("effectJa"), "Sem texto disponível."))]
        meta = {"Categoria": c.get("category", ""), "Raridade": c.get("rarity", ""), "Cor": c.get("colors", ""), "Custo": c.get("cost", ""), "Poder": c.get("power", "")}

    return {
        "date": date_key,
        "game": game,
        "name": name,
        "code": code,
        "images": image_candidates(game, c)[:4],
        "effect": "\n\n".join(x for x in effect_bits if x),
        "trigger": first(c.get("trigger"), c.get("triggerEn"), c.get("triggerJa")) if game == "onepiece" else "",
        "meta": {k: v for k, v in meta.items() if v not in (None, "", [])},
    }


def main():
    now = datetime.utcnow()
    date_key = now.strftime("%Y-%m-%d")
    seed = int(now.strftime("%Y%m%d"))
    game = GAMES[seed % len(GAMES)]
    cards = load_cards(game)
    usable = [c for c in cards if isinstance(c, dict) and image_candidates(game, c)]
    if not usable:
        raise SystemExit(f"No usable cards for {game}")
    idx = (seed * 9301 + 49297) % len(usable)
    payload = compact(game, usable[idx], date_key)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({game}: {payload['name']})")


if __name__ == "__main__":
    main()
