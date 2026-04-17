import json
import os
import argparse
from typing import List, Dict, Any
from hsrl.cards.registry import get_all_cards, get_card, load_database
from hsrl.core.enums import HeroClass, CardType

DECK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "decks")

def validate_deck(deck: dict) -> bool:
    """Validates the structure and content of a deck dictionary."""
    if "hero_class" not in deck or "cards" not in deck:
        print("Deck dictionary must contain 'hero_class' and 'cards'.")
        return False
        
    try:
        hero_class = HeroClass[deck["hero_class"]]
    except KeyError:
        print(f"Invalid hero class: {deck['hero_class']}")
        return False
        
    cards = deck["cards"]
    if len(cards) != 30:
        print(f"Deck has {len(cards)} cards, expected 30.")
        return False
    
    counts = {}
    valid = True
    
    for card_id in cards:
        try:
            card = get_card(card_id)
            if card.hero_class not in (HeroClass.NEUTRAL, hero_class):
                print(f"Card '{card.name}' ({card.hero_class.name}) is not allowed in a {hero_class.name} deck.")
                valid = False
        except KeyError:
            print(f"Card '{card_id}' not found in registry.")
            valid = False
            continue
            
        counts[card_id] = counts.get(card_id, 0) + 1
        if counts[card_id] > 2:
            print(f"More than 2 copies of '{card_id}' found.")
            valid = False

    return valid

def load_deck(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        deck = json.load(f)
    if isinstance(deck, list):
        raise ValueError("Deck must be a dictionary with 'hero_class' and 'cards', not a flat list. Please update legacy decks.")
    if not isinstance(deck, dict):
        raise ValueError("Deck must be a JSON object")
    return deck

def save_deck(deck: dict, name: str):
    os.makedirs(DECK_DIR, exist_ok=True)
    with open(os.path.join(DECK_DIR, f"{name}.json"), 'w') as f:
        json.dump(deck, f, indent=2)

def deck_stats(deck: dict):
    costs = {i: 0 for i in range(8)} # 0-7+
    types = {"MINION": 0, "SPELL": 0, "WEAPON": 0}
    
    for card_id in deck.get("cards", []):
        try:
            c = get_card(card_id)
            cost_bucket = min(7, c.cost)
            costs[cost_bucket] += 1
            types[c.type.name] = types.get(c.type.name, 0) + 1
        except KeyError:
            pass

    print(f"=== Deck Stats ({deck.get('hero_class', 'Unknown')}) ===")
    print("Mana Curve:")
    for i in range(8):
        label = f"{i}+" if i == 7 else str(i)
        bar = "#" * costs[i]
        print(f" {label}: {bar} ({costs[i]})")
        
    print("\nTypes:")
    for t, count in types.items():
        if count > 0:
            print(f" - {t}: {count}")

def main():
    parser = argparse.ArgumentParser(description="Hearthstone Deck Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Validate
    val_p = subparsers.add_parser("validate", help="Validate a deck by filename")
    val_p.add_argument("file", help="Path to deck JSON")

    # Stats
    stat_p = subparsers.add_parser("stats", help="Get stats for a deck by filename")
    stat_p.add_argument("file", help="Path to deck JSON")

    args = parser.parse_args()
    
    # Preload to ensure registry has cards
    load_database()

    try:
        deck = load_deck(args.file)
    except Exception as e:
        print(f"Failed to load deck: {e}")
        return

    if args.command == "validate":
        if validate_deck(deck):
            print("Deck is valid!")
        else:
            print("Deck is invalid.")
            
    elif args.command == "stats":
        deck_stats(deck)

if __name__ == "__main__":
    main()
