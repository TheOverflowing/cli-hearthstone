import json
import os
from typing import List
from hsrl.cards.registry import _REGISTRY as CARD_REGISTRY

DECK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "decks")

def validate_deck(deck: List[str]) -> bool:
    """Validates the flat array format of a deck."""
    if len(deck) != 30:
        return False
    
    counts = {}
    for card_id in deck:
        if card_id not in CARD_REGISTRY:
            return False
        counts[card_id] = counts.get(card_id, 0) + 1
        if counts[card_id] > 2:
            return False
    return True

def load_deck(filepath: str) -> List[str]:
    with open(filepath, 'r') as f:
        deck = json.load(f)
    if not isinstance(deck, list):
        raise ValueError("Deck must be a list of card IDs")
    if not validate_deck(deck):
        raise ValueError("Invalid deck list")
    return deck

def save_deck(deck: List[str], name: str):
    os.makedirs(DECK_DIR, exist_ok=True)
    with open(os.path.join(DECK_DIR, f"{name}.json"), 'w') as f:
        json.dump(deck, f, indent=2)

if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    console.print("[bold green]Deck Manager loaded (CLI interface WIP)[/]")
