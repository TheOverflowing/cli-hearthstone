from dataclasses import dataclass, field
from typing import List, Optional, Any
from .enums import Keyword, CardType, HeroClass

@dataclass
class Card:
    """Base definition for a Card. Static logic with no active game state."""
    id: str
    name: str
    cost: int
    description: str = ""
    attack: int = 0
    health: int = 0
    type: CardType = CardType.MINION
    hero_class: HeroClass = HeroClass.NEUTRAL
    keywords: List[Keyword] = field(default_factory=list)
    battlecry: Optional[Any] = None   # Any is Effect, avoid circular imports for now
    deathrattle: Optional[Any] = None # Any is Effect
    spell_effect: Optional[Any] = None
    secret_effect: Optional[Any] = None
    weapon_stats: Optional[tuple] = None # (attack, durability)
    requires_target: bool = False
