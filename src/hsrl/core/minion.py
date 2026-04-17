from dataclasses import dataclass, field
from .card import Card
from .enums import Keyword

@dataclass
class Minion:
    card: Card
    damage_taken: int = 0
    attacks_this_turn: int = 0
    summoning_sick: bool = True
    
    # Keyword states
    divine_shield: bool = False
    stealth: bool = False
    taunt: bool = False
    windfury: bool = False
    frozen: bool = False
    
    # Buffs
    attack_modifier: int = 0
    dies_at_end_of_turn: bool = False
    
    def __post_init__(self):
        # Initialize keyword states from card
        kw = self.card.keywords
        if Keyword.DIVINE_SHIELD in kw: self.divine_shield = True
        if Keyword.STEALTH in kw: self.stealth = True
        if Keyword.TAUNT in kw: self.taunt = True
        if Keyword.WINDFURY in kw: self.windfury = True
        if Keyword.FREEZE in kw: self.frozen = True
        
        # Charge disables summoning sickness immediately
        if Keyword.CHARGE in kw:
            self.summoning_sick = False
            
    # For backward compatibility, map has_attacked to attacks_this_turn limit
    @property
    def has_attacked(self) -> bool:
        limit = 2 if self.windfury else 1
        return self.attacks_this_turn >= limit

    @has_attacked.setter
    def has_attacked(self, val: bool):
        if val:
            self.attacks_this_turn += 1
        else:
            self.attacks_this_turn = 0
    
    @property
    def current_health(self) -> int:
        return self.card.health - self.damage_taken
        
    @property
    def current_attack(self) -> int:
        return max(0, self.card.attack + self.attack_modifier)
        
    def take_damage(self, amount: int):
        if amount <= 0:
            return
            
        if self.divine_shield:
            self.divine_shield = False
            # Prevent damage fully
            return
            
        self.damage_taken += amount
        
    def is_dead(self) -> bool:
        return self.current_health <= 0
        
    def restore_health(self, amount: int):
        self.damage_taken = max(0, self.damage_taken - amount)
