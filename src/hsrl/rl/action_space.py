import numpy as np
from typing import List, Tuple, Optional
from hsrl.core.enums import PlayerId
from hsrl.core.actions import Action, EndTurn, UseHeroPower, Attack, PlayMinion, PlaySpell
from hsrl.core.game import GameState

# Action Space Dimensions
NUM_TARGETS = 16 
NUM_ATTACK_TARGETS = 8
MAX_HAND = 10
MAX_BOARD = 7

OFFSET_END_TURN = 0
OFFSET_HERO_POWER = 1
OFFSET_ATTACK = OFFSET_HERO_POWER + NUM_TARGETS
OFFSET_PLAY_CARD = OFFSET_ATTACK + (MAX_BOARD * NUM_ATTACK_TARGETS)

TOTAL_ACTIONS = OFFSET_PLAY_CARD + (MAX_HAND * NUM_TARGETS)

class ActionEncoder:
    """
    Stateful or static encoder that maps engine `Action`s to indices 0..232 and vice versa.
    Target Schema (0-15):
        0: Opponent Hero
        1-7: Opponent Minions (0-6)
        8: Friendly Hero
        9-15: Friendly Minions (0-6)
        
    Attack Target Schema (0-7):
        0: Opponent Hero
        1-7: Opponent Minions (0-6)
    """
    
    @staticmethod
    def _encode_target(player_id: PlayerId, target_pid: Optional[PlayerId], target_idx: Optional[int]) -> int:
        if target_pid is None or target_idx is None:
            return 0 # Default target bin if no target required
            
        opp_id = target_pid.opponent() # Actually we just care if it's friend or foe
        is_friendly = (target_pid == player_id)
        
        if is_friendly:
            return 8 if target_idx == -1 else 9 + target_idx
        else:
            return 0 if target_idx == -1 else 1 + target_idx

    @staticmethod
    def _decode_target(encoded_target: int, player_id: PlayerId) -> Tuple[PlayerId, int]:
        if encoded_target == 0:
            return (player_id.opponent(), -1)
        elif 1 <= encoded_target <= 7:
            return (player_id.opponent(), encoded_target - 1)
        elif encoded_target == 8:
            return (player_id, -1)
        elif 9 <= encoded_target <= 15:
            return (player_id, encoded_target - 9)
        return (None, None)

    @staticmethod
    def _encode_attack_target(target_idx: int) -> int:
        # For attacks, target_idx -1 is opp hero, 0..N is opp minion
        return 0 if target_idx == -1 else 1 + target_idx
        
    @staticmethod
    def _decode_attack_target(encoded_target: int) -> int:
        return -1 if encoded_target == 0 else encoded_target - 1

    def get_action_mask(self, state: GameState) -> np.ndarray:
        mask = np.zeros(TOTAL_ACTIONS, dtype=bool)
        if state.is_terminal():
            return mask
            
        legals = state.get_legal_actions()
        p_id = state.current_player_id
        
        for action in legals:
            idx = self.encode_action(action, p_id)
            if idx is not None:
                mask[idx] = True
        return mask

    def encode_action(self, action: Action, player_id: PlayerId) -> Optional[int]:
        if isinstance(action, EndTurn):
            return OFFSET_END_TURN
            
        elif isinstance(action, UseHeroPower):
            t = self._encode_target(player_id, action.target_player_id, action.target_index)
            return OFFSET_HERO_POWER + t
            
        elif isinstance(action, Attack):
            # We ignore invalid attackers/targets > limits for safety max
            if action.attacker_index >= MAX_BOARD: return None
            t = self._encode_attack_target(action.target_index)
            if t >= NUM_ATTACK_TARGETS: return None
            return OFFSET_ATTACK + (action.attacker_index * NUM_ATTACK_TARGETS) + t
            
        elif isinstance(action, PlayMinion) or isinstance(action, PlaySpell):
            hand_idx = action.hand_index
            if hand_idx >= MAX_HAND: return None
            
            # Since we drop board position generation, we have to encode it.
            # But the state generator might yield multiple board_positions for the same minion
            # To simplify rl, we just map it down to target. We only care about one position.
            target_pid = getattr(action, "target_player_id", None)
            target_idx = getattr(action, "target_index", None)
            t = self._encode_target(player_id, target_pid, target_idx)
            
            return OFFSET_PLAY_CARD + (hand_idx * NUM_TARGETS) + t
            
        return None

    def decode_action(self, idx: int, state: GameState) -> Action:
        p_id = state.current_player_id
        if idx == OFFSET_END_TURN:
            return EndTurn(p_id)
            
        elif OFFSET_HERO_POWER <= idx < OFFSET_ATTACK:
            t_idx = idx - OFFSET_HERO_POWER
            t_pid, inner_t_idx = self._decode_target(t_idx, p_id)
            return UseHeroPower(p_id, t_pid, inner_t_idx)
            
        elif OFFSET_ATTACK <= idx < OFFSET_PLAY_CARD:
            rel = idx - OFFSET_ATTACK
            attacker = rel // NUM_ATTACK_TARGETS
            t_enc = rel % NUM_ATTACK_TARGETS
            target = self._decode_attack_target(t_enc)
            return Attack(p_id, attacker, target)
            
        elif OFFSET_PLAY_CARD <= idx < TOTAL_ACTIONS:
            rel = idx - OFFSET_PLAY_CARD
            hand_idx = rel // NUM_TARGETS
            t_enc = rel % NUM_TARGETS
            t_pid, inner_t_idx = self._decode_target(t_enc, p_id)
            
            # We must determine if this is PlayMinion or PlaySpell by inspecting the hand
            player = state.get_current_player()
            if hand_idx < len(player.hand):
                card = player.hand[hand_idx]
                from hsrl.core.enums import CardType
                if card.type == CardType.SPELL:
                    if card.requires_target:
                        return PlaySpell(p_id, hand_idx, t_pid, inner_t_idx)
                    return PlaySpell(p_id, hand_idx)
                else:
                    # Minion
                    # Auto-pick rightmost board position
                    board_pos = len(player.board)
                    if card.requires_target:
                        return PlayMinion(p_id, hand_idx, board_pos, t_pid, inner_t_idx)
                    return PlayMinion(p_id, hand_idx, board_pos)
            else:
                # Invalid action selected (mask fail logic?). Just return EndTurn safely
                return EndTurn(p_id)
                
        return EndTurn(p_id)
