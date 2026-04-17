from dataclasses import dataclass, field
from typing import List, Optional
from .enums import PlayerId, HeroClass
from .card import Card
from .minion import Minion
from .weapon import Weapon

@dataclass
class Player:
    id: PlayerId
    hero_class: HeroClass = HeroClass.MAGE
    health: int = 30
    max_health: int = 30
    armor: int = 0
    mana_crystals: int = 0
    max_mana: int = 0
    hero_power_used_this_turn: bool = False
    hero_attacked_this_turn: bool = False
    frozen: bool = False
    
    # Zones
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    board: List[Minion] = field(default_factory=list)
    weapon: Optional[Weapon] = None
    secrets: List[Card] = field(default_factory=list)
    
    # Trackers
    fatigue_counter: int = 0
    attack_this_turn: int = 0  # extra attack from spells
    
    def get_attack(self) -> int:
        base = self.attack_this_turn
        if self.weapon:
            base += self.weapon.attack
        return base
    
    def gain_mana_crystal(self):
        if self.max_mana < 10:
            self.max_mana += 1
            
    def refresh_mana(self):
        self.mana_crystals = self.max_mana
        
    def take_damage(self, amount: int):
        if self.armor >= amount:
            self.armor -= amount
        else:
            remaining = amount - self.armor
            self.armor = 0
            self.health -= remaining

    def restore_health(self, amount: int):
        if amount <= 0: return
        self.health = min(self.max_health, self.health + amount)
        
    def draw_card(self) -> Optional[Card]:
        if not self.deck:
            self.fatigue_counter += 1
            self.take_damage(self.fatigue_counter)
            return None
            
        card = self.deck.pop(0)  # Top of deck is index 0
        if len(self.hand) < 10:
            self.hand.append(card)
            return card
        else:
            # Overdrawn! Card is destroyed (discarded into void)
            return None
