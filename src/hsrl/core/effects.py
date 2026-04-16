from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

class Effect(ABC):
    @abstractmethod
    def apply(self, state: Any, source_player_id: Any, target_player_id: Any = None, target_index: int = None):
        pass

@dataclass
class DrawCards(Effect):
    amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        player = state.players[source_player_id]
        for _ in range(self.amount):
            player.draw_card()

@dataclass
class DealDamage(Effect):
    amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        # We need a target to deal damage to.
        # target_index = -1 is hero.
        if target_player_id is None or target_index is None:
            return # Fizzle if no valid target specified
            
        target_player = state.players[target_player_id]
        if target_index == -1:
            target_player.take_damage(self.amount)
        else:
            if 0 <= target_index < len(target_player.board):
                target_minion = target_player.board[target_index]
                target_minion.take_damage(self.amount)
                # In actual mechanics we might need to resolve deaths here,
                # but we'll let step() resolve deaths naturally.

@dataclass
class FreezeCharacter(Effect):
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None: return
        target_player = state.players[target_player_id]
        if target_index == -1:
            target_player.frozen = True
        elif 0 <= target_index < len(target_player.board):
            target_player.board[target_index].frozen = True

@dataclass
class DestroyMinion(Effect):
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None or target_index == -1: return
        target_player = state.players[target_player_id]
        if 0 <= target_index < len(target_player.board):
            target_minion = target_player.board[target_index]
            target_minion.damage_taken = target_minion.card.health # Instant dead

@dataclass
class DealDamageToAllMinions(Effect):
    amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        for pid in [state.current_player_id, state.current_player_id.opponent()]:
            for minion in state.players[pid].board:
                minion.take_damage(self.amount)

@dataclass
class DealDamageScalingWithArmor(Effect):
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None: return
        amount = state.players[source_player_id].armor
        target_player = state.players[target_player_id]
        if target_index == -1:
            target_player.take_damage(amount)
        elif 0 <= target_index < len(target_player.board):
            target_player.board[target_index].take_damage(amount)

@dataclass
class TransformMinion(Effect):
    new_card: Any
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None or target_index == -1: return
        target_player = state.players[target_player_id]
        if 0 <= target_index < len(target_player.board):
            from .minion import Minion
            target_player.board[target_index] = Minion(card=self.new_card)

@dataclass
class GainArmor(Effect):
    amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        state.players[source_player_id].armor += self.amount
