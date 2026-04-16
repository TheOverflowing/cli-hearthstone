from dataclasses import dataclass, field
from typing import Dict, List
from .enums import Phase, PlayerId, CardType, HeroClass
from .player import Player
from .minion import Minion
from .actions import Action, EndTurn, PlayMinion, Attack, PlaySpell, UseHeroPower, MulliganCards, PlayWeapon, PlaySecret
from itertools import combinations
from .events import EventBus, MinionPlayed, MinionDied, DamageDealt, TurnStarted, SpellPlayed

@dataclass
class GameState:
    players: Dict[PlayerId, Player] = field(default_factory=lambda: {
        PlayerId.P1: Player(id=PlayerId.P1),
        PlayerId.P2: Player(id=PlayerId.P2)
    })
    current_player_id: PlayerId = PlayerId.P1
    turn_number: int = 1
    phase: Phase = Phase.START_TURN
    event_bus: EventBus = field(default_factory=EventBus)

    def setup_game(self):
        for _ in range(3):
            self.players[PlayerId.P1].draw_card()
        for _ in range(4):
            self.players[PlayerId.P2].draw_card()
        # The player going second gets the coin. Left as an exercise for another time.
        self.phase = Phase.MULLIGAN

    def get_current_player(self) -> Player:
        return self.players[self.current_player_id]

    def get_opponent(self) -> Player:
        return self.players[self.current_player_id.opponent()]

    def is_terminal(self) -> bool:
        return any(p.health <= 0 for p in self.players.values())

    def get_winner(self) -> PlayerId:
        if not self.is_terminal(): return None
        alive = [p.id for p in self.players.values() if p.health > 0]
        return alive[0] if len(alive) == 1 else None

    def _get_valid_attack_targets(self, opp: Player) -> List[int]:
        # Indices: -1 is hero, 0..N are minions
        taunts = [i for i, m in enumerate(opp.board) if m.taunt and not m.stealth]
        if taunts:
            return taunts # Enforce taunt
            
        targets = [-1] # Hero is targeted
        for i, m in enumerate(opp.board):
            if not m.stealth:
                targets.append(i)
        return targets

    def _get_all_targets(self) -> List[tuple]:
        # For battlecries: Returns (PlayerId, idx)
        targets = []
        for p_id in [PlayerId.P1, PlayerId.P2]:
            targets.append((p_id, -1)) # heroes
            for i, m in enumerate(self.players[p_id].board):
                if not m.stealth: # cannot target stealth
                    targets.append((p_id, i))
        return targets

    def get_legal_actions(self) -> List[Action]:
        if self.is_terminal(): return []
            
        actions = []
        if self.phase == Phase.MULLIGAN:
            p_id = self.current_player_id
            player = self.get_current_player()
            hand_size = len(player.hand)
            # A mulligan tosses some subset of the hand
            indices = list(range(hand_size))
            for r in range(hand_size + 1):
                for subset in combinations(indices, r):
                    actions.append(MulliganCards(p_id, list(subset)))
            return actions

        if self.phase == Phase.MAIN_PHASE:
            p_id = self.current_player_id
            player = self.get_current_player()
            opp = self.get_opponent()
            
            actions.append(EndTurn(player_id=p_id))
            
            # Play Cards
            for i, card in enumerate(player.hand):
                if player.mana_crystals >= card.cost:
                    if getattr(card, "type", CardType.MINION) == CardType.MINION:
                        if len(player.board) < 7:
                            positions = range(len(player.board) + 1)
                            if card.requires_target:
                                for target_pid, target_idx in self._get_all_targets():
                                    for pos in positions:
                                        actions.append(PlayMinion(p_id, i, pos, target_pid, target_idx))
                            else:
                                for pos in positions:
                                    actions.append(PlayMinion(p_id, i, pos))
                    elif getattr(card, "type", CardType.MINION) == CardType.SPELL:
                        if card.requires_target:
                            for target_pid, target_idx in self._get_all_targets():
                                actions.append(PlaySpell(p_id, i, target_pid, target_idx))
                        else:
                            actions.append(PlaySpell(p_id, i))
                    elif getattr(card, "type", CardType.MINION) == CardType.SECRET:
                        if len(player.secrets) < 5:
                            actions.append(PlaySecret(p_id, i))
                    elif getattr(card, "type", CardType.MINION) == CardType.WEAPON:
                        if card.requires_target:
                            for target_pid, target_idx in self._get_all_targets():
                                actions.append(PlayWeapon(p_id, i, target_pid, target_idx))
                        else:
                            actions.append(PlayWeapon(p_id, i))

            # Hero Power
            if not player.hero_power_used_this_turn and player.mana_crystals >= 2:
                if player.hero_class == HeroClass.MAGE:
                    for target_pid, target_idx in self._get_all_targets():
                        actions.append(UseHeroPower(p_id, target_pid, target_idx))
                elif player.hero_class == HeroClass.WARRIOR:
                    actions.append(UseHeroPower(p_id))
            
            # Attack
            valid_targets = self._get_valid_attack_targets(opp)
            
            # Hero attack
            if player.get_attack() > 0 and not player.hero_attacked_this_turn and not player.frozen:
                for t_idx in valid_targets:
                    actions.append(Attack(p_id, -1, t_idx))

            for i, minion in enumerate(player.board):
                if not minion.summoning_sick and not minion.has_attacked and minion.current_attack > 0 and not minion.frozen:
                    for t_idx in valid_targets:
                        actions.append(Attack(p_id, i, t_idx))
        return actions

    def step(self, action: Action):
        if self.is_terminal(): raise ValueError("Terminal game state.")
        if action.player_id != self.current_player_id: raise ValueError(f"Action from non-active player: {action.player_id}")
        
        player = self.get_current_player()
        opp = self.get_opponent()
            
        if isinstance(action, EndTurn):
            self._end_turn()

        elif isinstance(action, MulliganCards):
            cards_tossed = []
            import random
            # pop in reverse order to not shift indices
            for idx in sorted(action.indices, reverse=True):
                cards_tossed.append(player.hand.pop(idx))
            for _ in range(len(action.indices)):
                player.draw_card()
            player.deck.extend(cards_tossed)
            random.shuffle(player.deck)

            if self.current_player_id == PlayerId.P1:
                self.current_player_id = PlayerId.P2
            else:
                self.current_player_id = PlayerId.P1
                self._start_turn()
            
        elif isinstance(action, PlayMinion):
            card = player.hand.pop(action.hand_index)
            player.mana_crystals -= card.cost
            minion = Minion(card=card)
            player.board.insert(action.board_position, minion)
            
            if card.battlecry:
                card.battlecry.apply(self, player.id, action.target_player_id, action.target_index)
                
            self._resolve_deaths()
            self.event_bus.publish(MinionPlayed(player.id, minion))
            
        elif isinstance(action, Attack):
            t_id = opp.id
            if action.attacker_index == -1:
                # Hero attacking
                player.hero_attacked_this_turn = True
                atk = player.get_attack()
                
                if action.target_index == -1:
                    opp.take_damage(atk)
                    self.event_bus.publish(DamageDealt(player, opp, atk))
                    player.take_damage(opp.get_attack())
                    if opp.get_attack() > 0:
                        self.event_bus.publish(DamageDealt(opp, player, opp.get_attack()))
                else:
                    target = opp.board[action.target_index]
                    target.take_damage(atk)
                    self.event_bus.publish(DamageDealt(player, target, atk))
                    player.take_damage(target.current_attack)
                    if target.current_attack > 0:
                        self.event_bus.publish(DamageDealt(target, player, target.current_attack))
                        
                if player.weapon:
                    player.weapon.use_durability()
                    if player.weapon.is_destroyed():
                        player.weapon = None
            else:
                attacker = player.board[action.attacker_index]
                attacker.has_attacked = True
                attacker.stealth = False # Attacking breaks stealth
                
                if action.target_index == -1:
                    # Attack hero
                    opp.take_damage(attacker.current_attack)
                    self.event_bus.publish(DamageDealt(attacker, opp, attacker.current_attack))
                else:
                    # Attack minion
                    target = opp.board[action.target_index]
                    target.take_damage(attacker.current_attack)
                    self.event_bus.publish(DamageDealt(attacker, target, attacker.current_attack))
                    
                    attacker.take_damage(target.current_attack)
                    if target.current_attack > 0:
                        self.event_bus.publish(DamageDealt(target, attacker, target.current_attack))
                    
            self._resolve_deaths()
            
        elif isinstance(action, PlaySpell):
            card = player.hand.pop(action.hand_index)
            player.mana_crystals -= card.cost
            
            if card.spell_effect:
                card.spell_effect.apply(self, player.id, action.target_player_id, action.target_index)
                
            self._resolve_deaths()
            self.event_bus.publish(SpellPlayed(player.id, card))
            
        elif isinstance(action, PlayWeapon):
            card = player.hand.pop(action.hand_index)
            player.mana_crystals -= card.cost
            from .weapon import Weapon
            player.weapon = Weapon(card=card, attack=card.weapon_stats[0], durability=card.weapon_stats[1])
            if card.battlecry:
                card.battlecry.apply(self, player.id, getattr(action, "target_player_id", None), getattr(action, "target_index", None))
            self._resolve_deaths()
            
        elif isinstance(action, PlaySecret):
            card = player.hand.pop(action.hand_index)
            player.mana_crystals -= card.cost
            player.secrets.append(card)
            self._resolve_deaths()
            
        elif isinstance(action, UseHeroPower):
            player.mana_crystals -= 2
            player.hero_power_used_this_turn = True
            
            if player.hero_class == HeroClass.MAGE:
                if action.target_index == -1:
                    target = self.players[action.target_player_id]
                    target.take_damage(1)
                else:
                    target = self.players[action.target_player_id].board[action.target_index]
                    target.take_damage(1)
            elif player.hero_class == HeroClass.WARRIOR:
                player.armor += 2
                
            self._resolve_deaths()
        else:
            raise ValueError()

    def _resolve_deaths(self):
        for p in self.players.values():
            alive = []
            for m in p.board:
                if m.is_dead():
                    if m.card.deathrattle:
                        m.card.deathrattle.apply(self, p.id, None, None)
                    self.event_bus.publish(MinionDied(p.id, m))
                else:
                    alive.append(m)
            p.board = alive

    def _start_turn(self):
        self.phase = Phase.START_TURN
        player = self.get_current_player()
        
        player.gain_mana_crystal()
        player.refresh_mana()
        player.draw_card()
        player.hero_power_used_this_turn = False
        player.hero_attacked_this_turn = False
        player.attack_this_turn = 0
        
        for m in player.board:
            m.has_attacked = False
            # Sickness persists until next turn start, and then turns off.
            m.summoning_sick = False
            
        self.event_bus.publish(TurnStarted(player.id))
        self.phase = Phase.MAIN_PHASE

    def _end_turn(self):
        # Unfreeze characters at end of their turn
        player = self.get_current_player()
        player.frozen = False
        for m in player.board:
            m.frozen = False
            
        self.phase = Phase.END_TURN
        self.current_player_id = self.current_player_id.opponent()
        if self.current_player_id == PlayerId.P1:
            self.turn_number += 1
        self._start_turn()
