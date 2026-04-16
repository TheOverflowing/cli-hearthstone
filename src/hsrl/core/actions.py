from dataclasses import dataclass
from typing import Optional
from .enums import PlayerId

@dataclass
class Action:
    player_id: PlayerId

@dataclass
class EndTurn(Action):
    pass

@dataclass
class PlayMinion(Action):
    """Play a minion. If requires_target is true, must supply target_player_id and target_index."""
    hand_index: int
    board_position: int
    target_player_id: Optional[PlayerId] = None
    target_index: Optional[int] = None

@dataclass
class Attack(Action):
    attacker_index: int
    target_index: int

@dataclass
class PlaySpell(Action):
    hand_index: int
    target_player_id: Optional[PlayerId] = None
    target_index: Optional[int] = None

@dataclass
class UseHeroPower(Action):
    target_player_id: Optional[PlayerId] = None
    target_index: Optional[int] = None

@dataclass
class MulliganCards(Action):
    indices: list[int]

@dataclass
class PlayWeapon(Action):
    hand_index: int
    target_player_id: Optional[PlayerId] = None
    target_index: Optional[int] = None

@dataclass
class PlaySecret(Action):
    hand_index: int
