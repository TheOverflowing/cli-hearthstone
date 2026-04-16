from dataclasses import dataclass
from .card import Card

@dataclass
class Weapon:
    card: Card
    attack: int
    durability: int

    def use_durability(self):
        self.durability -= 1

    def is_destroyed(self) -> bool:
        return self.durability <= 0
