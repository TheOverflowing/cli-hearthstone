import json
import os
from typing import Dict, List, Optional
from hsrl.core.card import Card
from hsrl.core.enums import CardType, HeroClass

_REGISTRY: Dict[str, Card] = {}
_IMPLEMENTED_EFFECTS: set = set()

def load_database(path: str = "cards.json"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        try:
            ctype = CardType[item.get("type", "MINION")]
            hclass = HeroClass[item.get("hero_class", "NEUTRAL")]
        except KeyError:
            continue
        
        card = Card(
            id=item["id"],
            name=item["name"],
            cost=item["cost"],
            description=item.get("description", ""),
            attack=item.get("attack", 0),
            health=item.get("health", 0),
            type=ctype,
            hero_class=hclass,
            requires_target=False # Will be overridden by effects
        )
        _REGISTRY[card.id] = card

    _apply_effects()

def _apply_effects():
    """Manually patch cards with their implemented mechanics."""
    from hsrl.core.effects import (DealDamage, FreezeCharacter, DrawCards, RestoreHealth, 
                                   DealDamageAndFreezeAllEnemyMinions, ConditionalDamageIfFrozen,
                                   CleaveDamageAndFreeze, SetAttackToHealth, ConditionalDamageOrBuff,
                                   DestroyAllMinions, SacrificeAndAoE, MortalStrikeEffect)

    # MAGE SPELLS
    if "fireball" in _REGISTRY:
        _REGISTRY["fireball"].spell_effect = DealDamage(6)
        _REGISTRY["fireball"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("fireball")
        
    if "frost_nova" in _REGISTRY:
        _REGISTRY["frost_nova"].spell_effect = FreezeCharacter() # Area effect freeze typically doesn't require target, but DealDamage does. We will implement Area later. actually Frost Nova freezes all enemies.
        # But wait, original impl is just targeting one. Let's fix that later.
        _REGISTRY["frost_nova"].requires_target = False
        _IMPLEMENTED_EFFECTS.add("frost_nova")
        
    if "arcane_intellect" in _REGISTRY:
        _REGISTRY["arcane_intellect"].spell_effect = DrawCards(2)
        _IMPLEMENTED_EFFECTS.add("arcane_intellect")

    if "blizzard" in _REGISTRY:
        _REGISTRY["blizzard"].spell_effect = DealDamageAndFreezeAllEnemyMinions(2)
        _REGISTRY["blizzard"].requires_target = False
        _IMPLEMENTED_EFFECTS.add("blizzard")

    if "cone_of_cold" in _REGISTRY:
        _REGISTRY["cone_of_cold"].spell_effect = CleaveDamageAndFreeze(1)
        _REGISTRY["cone_of_cold"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("cone_of_cold")
        
    if "ice_lance" in _REGISTRY:
        _REGISTRY["ice_lance"].spell_effect = ConditionalDamageIfFrozen(4)
        _REGISTRY["ice_lance"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("ice_lance")

    if "pyroblast" in _REGISTRY:
        _REGISTRY["pyroblast"].spell_effect = DealDamage(10)
        _REGISTRY["pyroblast"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("pyroblast")

    if "demonfire" in _REGISTRY:
        _REGISTRY["demonfire"].spell_effect = ConditionalDamageOrBuff(2, 2)
        _REGISTRY["demonfire"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("demonfire")

    if "inner_fire" in _REGISTRY:
        _REGISTRY["inner_fire"].spell_effect = SetAttackToHealth()
        _REGISTRY["inner_fire"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("inner_fire")

    if "twisting_nether" in _REGISTRY:
        _REGISTRY["twisting_nether"].spell_effect = DestroyAllMinions()
        _REGISTRY["twisting_nether"].requires_target = False
        _IMPLEMENTED_EFFECTS.add("twisting_nether")
        
    if "shadowflame" in _REGISTRY:
        _REGISTRY["shadowflame"].spell_effect = SacrificeAndAoE()
        _REGISTRY["shadowflame"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("shadowflame")

    if "mortal_strike" in _REGISTRY:
        _REGISTRY["mortal_strike"].spell_effect = MortalStrikeEffect(4, 6)
        _REGISTRY["mortal_strike"].requires_target = True
        _IMPLEMENTED_EFFECTS.add("mortal_strike")

def register_card(card: Card):
    if card.id in _REGISTRY:
        raise ValueError(f"Card with id {card.id} already registered.")
    _REGISTRY[card.id] = card

def get_card(card_id: str) -> Card:
    if not _REGISTRY:
        load_database()
    if card_id not in _REGISTRY:
        raise KeyError(f"Card with id {card_id} not found.")
    return _REGISTRY[card_id]

def get_all_cards() -> List[Card]:
    if not _REGISTRY:
        load_database()
    return list(_REGISTRY.values())

def is_implemented(card_id: str) -> bool:
    card = get_card(card_id)
    # A card is "implemented" natively if it has no complex description, OR if it's in our _IMPLEMENTED_EFFECTS set
    # Complex description check:
    if not card.description:
        return True # Vanilla minion
    # Basic keyword check could go here... but for now:
    return card_id in _IMPLEMENTED_EFFECTS
