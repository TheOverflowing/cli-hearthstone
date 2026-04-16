import os
import json
import requests
import re

URL = "https://api.hearthstonejson.com/v1/latest/enUS/cards.json"
SETS_TO_IMPORT = ["EXPERT1"]

def to_snake_case(name):
    # Map special characters or spaces to empty or underscore
    s = name.replace("'", "").replace("-", "_").replace(" ", "_")
    s = re.sub(r'[^a-zA-Z0-9_]', '', s)
    return s.lower()

def run():
    print(f"Fetching {URL} ...")
    resp = requests.get(URL)
    resp.raise_for_status()
    all_cards = resp.json()

    print(f"Loaded {len(all_cards)} from HearthstoneJSON.")
    
    # Filter for playable cards (Minion, Spell, Weapon) in the chosen sets
    expert1_cards = [
        c for c in all_cards
        if c.get("set") in SETS_TO_IMPORT
        and c.get("type", "") in ["MINION", "SPELL", "WEAPON"]
    ]

    print(f"Found {len(expert1_cards)} cards in {SETS_TO_IMPORT}.")

    # Our format output
    output = []
    seen_ids = set()

    for c in expert1_cards:
        # Generate ID
        base_id = to_snake_case(c["name"])
        card_id = base_id
        if card_id in seen_ids:
            card_id = f'{c["set"].lower()}_{base_id}'
        seen_ids.add(card_id)

        # Parse text
        text = c.get("text", "")
        # Remove HS markup like [x] $ or tags like <b> </b>
        clean_text = re.sub(r'<[^>]*>', '', text)
        clean_text = clean_text.replace('[x]', '').replace('$', '').replace('\n', ' ').replace('_', '')

        # Class
        card_class = c.get("playerClass", "NEUTRAL")
        if card_class not in ["NEUTRAL", "MAGE", "WARRIOR", "PRIEST", "HUNTER", "PALADIN", "WARLOCK", "DRUID", "SHAMAN", "ROGUE"]:
            continue

        out_card = {
            "id": card_id,
            "name": c["name"],
            "cost": c.get("cost", 0),
            "type": c["type"],
            "hero_class": card_class,
            "description": clean_text.strip(),
            "attack": c.get("attack", 0),
            "health": c.get("durability", c.get("health", 0)), 
            "mechanics": c.get("mechanics", [])
        }
        output.append(out_card)

    with open("cards.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(output)} cards to cards.json.")

if __name__ == "__main__":
    run()
