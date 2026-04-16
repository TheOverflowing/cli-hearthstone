from typing import Dict
from hsrl.core.card import Card

_REGISTRY: Dict[str, Card] = {}

def register_card(card: Card):
    if card.id in _REGISTRY:
        raise ValueError(f"Card with id {card.id} already registered.")
    _REGISTRY[card.id] = card

def get_card(card_id: str) -> Card:
    if card_id not in _REGISTRY:
        raise KeyError(f"Card with id {card_id} not found.")
    return _REGISTRY[card_id]
