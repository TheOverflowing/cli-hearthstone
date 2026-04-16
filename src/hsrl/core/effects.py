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

@dataclass
class RestoreHealth(Effect):
    amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None: return
        target_player = state.players[target_player_id]
        if target_index == -1:
            target_player.health = min(30, target_player.health + self.amount)
        elif 0 <= target_index < len(target_player.board):
            target_minion = target_player.board[target_index]
            target_minion.damage_taken = max(0, target_minion.damage_taken - self.amount)

@dataclass
class DealDamageAndFreezeAllEnemyMinions(Effect):
    amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        opp = state.players[source_player_id.opponent()]
        for minion in opp.board:
            minion.take_damage(self.amount)
            minion.frozen = True

@dataclass
class ConditionalDamageIfFrozen(Effect):
    damage: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None: return
        target_player = state.players[target_player_id]
        target = target_player if target_index == -1 else target_player.board[target_index]
        if target.frozen:
            target.take_damage(self.damage)
        else:
            target.frozen = True

@dataclass
class CleaveDamageAndFreeze(Effect):
    damage: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None or target_index == -1: return
        target_player = state.players[target_player_id]
        indices_to_hit = [target_index - 1, target_index, target_index + 1]
        for idx in indices_to_hit:
            if 0 <= idx < len(target_player.board):
                m = target_player.board[idx]
                m.take_damage(self.damage)
                m.frozen = True

@dataclass
class SetAttackToHealth(Effect):
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None or target_index == -1: return
        target_minion = state.players[target_player_id].board[target_index]
        target_minion.attack_modifier += (target_minion.current_health - target_minion.current_attack)

@dataclass
class ConditionalDamageOrBuff(Effect):
    damage: int
    buff_amount: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None or target_index == -1: return
        target_minion = state.players[target_player_id].board[target_index]
        
        # simplified fallback check for demonfire
        has_demon = False
        if "demon" in target_minion.card.description.lower() or target_minion.card.id in ["flame_imp", "pit_lord", "blood_imp", "felguard", "doomguard", "succubus", "voidwalker", "dread_infernal", "void_terror"]:
            has_demon = True
            
        if target_player_id == source_player_id and has_demon:
            target_minion.attack_modifier += self.buff_amount
            target_minion.card.health += self.buff_amount # permanently buff health so current_health rises
        else:
            target_minion.take_damage(self.damage)

@dataclass
class DestroyAllMinions(Effect):
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        for pid in [state.current_player_id, state.current_player_id.opponent()]:
            for minion in state.players[pid].board:
                minion.damage_taken = minion.card.health

@dataclass
class SacrificeAndAoE(Effect):
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None or target_index == -1: return
        if target_player_id != source_player_id: return
        target_minion = state.players[target_player_id].board[target_index]
        dmg = target_minion.current_attack
        target_minion.damage_taken = target_minion.card.health
        
        opp = state.players[source_player_id.opponent()]
        for m in opp.board:
            m.take_damage(dmg)

@dataclass
class MortalStrikeEffect(Effect):
    base_dmg: int
    enhance_dmg: int
    def apply(self, state, source_player_id, target_player_id=None, target_index=None):
        if target_player_id is None or target_index is None: return
        sp = state.players[source_player_id]
        amt = self.enhance_dmg if sp.health <= 12 else self.base_dmg
        target = state.players[target_player_id] if target_index == -1 else state.players[target_player_id].board[target_index]
        target.take_damage(amt)

