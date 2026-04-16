import json
import os
import argparse
from typing import List, Dict, Any
from hsrl.cards.registry import get_all_cards, get_card, load_database
from hsrl.core.enums import HeroClass, CardType

DECK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "decks")

def validate_deck(deck: List[str]) -> bool:
    """Validates the flat array format of a deck."""
    if len(deck) != 30:
        print(f"Deck has {len(deck)} cards, expected 30.")
        return False
    
    counts = {}
    valid = True
    
    # We should also check for class consistency. 
    # A deck must are all neutral or of exactly 1 class.
    classes_found = set()
    
    for card_id in deck:
        try:
            card = get_card(card_id)
            if card.hero_class != HeroClass.NEUTRAL:
                classes_found.add(card.hero_class)
        except KeyError:
            print(f"Card '{card_id}' not found in registry.")
            valid = False
            continue
            
        counts[card_id] = counts.get(card_id, 0) + 1
        if counts[card_id] > 2:
            print(f"More than 2 copies of '{card_id}' found.")
            valid = False

    if len(classes_found) > 1:
        print(f"Deck contains cards from multiple classes: {[c.name for c in classes_found]}")
        valid = False
        
    return valid

def load_deck(filepath: str) -> List[str]:
    with open(filepath, 'r') as f:
        deck = json.load(f)
    if not isinstance(deck, list):
        raise ValueError("Deck must be a list of card IDs")
    return deck

def save_deck(deck: List[str], name: str):
    os.makedirs(DECK_DIR, exist_ok=True)
    with open(os.path.join(DECK_DIR, f"{name}.json"), 'w') as f:
        json.dump(deck, f, indent=2)

def deck_stats(deck: List[str]):
    costs = {i: 0 for i in range(8)} # 0-7+
    types = {"MINION": 0, "SPELL": 0, "WEAPON": 0}
    
    for card_id in deck:
        try:
            c = get_card(card_id)
            cost_bucket = min(7, c.cost)
            costs[cost_bucket] += 1
            types[c.type.name] = types.get(c.type.name, 0) + 1
        except KeyError:
            pass

    print("=== Deck Stats ===")
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
