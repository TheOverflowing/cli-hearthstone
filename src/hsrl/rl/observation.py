import numpy as np
import gymnasium as gym
from typing import Dict, Any

from hsrl.core.game import GameState
from hsrl.core.enums import Keyword, CardType

MAX_HAND = 10
MAX_BOARD = 7
CARD_FEATS = 13
HERO_FEATS = 8

class ObservationEncoder:
    def __init__(self):
        self.observation_space = gym.spaces.Dict({
            "my_hero": gym.spaces.Box(low=-100.0, high=100.0, shape=(HERO_FEATS,), dtype=np.float32),
            "opp_hero": gym.spaces.Box(low=-100.0, high=100.0, shape=(HERO_FEATS,), dtype=np.float32),
            "my_hand": gym.spaces.Box(low=-100.0, high=100.0, shape=(MAX_HAND, CARD_FEATS), dtype=np.float32),
            "my_board": gym.spaces.Box(low=-100.0, high=100.0, shape=(MAX_BOARD, CARD_FEATS), dtype=np.float32),
            "opp_board": gym.spaces.Box(low=-100.0, high=100.0, shape=(MAX_BOARD, CARD_FEATS), dtype=np.float32),
        })

    def _encode_hero(self, player) -> np.ndarray:
        # [health, armor, mana, max_mana, frozen, class_neutral, class_mage, class_warrior]
        vec = np.zeros(HERO_FEATS, dtype=np.float32)
        vec[0] = player.health
        vec[1] = player.armor
        vec[2] = player.mana_crystals
        vec[3] = player.max_mana
        vec[4] = 1.0 if player.frozen else 0.0
        vec[5 + player.hero_class.value - 1] = 1.0 # Assuming HeroClass enums map 1,2,3...
        return vec

    def _encode_card(self, card, minion=None) -> np.ndarray:
        vec = np.zeros(CARD_FEATS, dtype=np.float32)
        if card is None and minion is None:
            return vec
            
        c = minion.card if minion else card
        vec[0] = c.cost
        vec[1] = minion.current_attack if minion else c.attack
        vec[2] = minion.current_health if minion else c.health
        vec[3] = 1.0 if c.type == CardType.SPELL else 0.0
        
        # Keywords
        kws = c.keywords
        vec[4] = 1.0 if Keyword.TAUNT in kws else 0.0
        vec[5] = 1.0 if Keyword.CHARGE in kws else 0.0
        vec[6] = 1.0 if Keyword.DIVINE_SHIELD in kws else 0.0
        vec[7] = 1.0 if Keyword.STEALTH in kws else 0.0
        vec[8] = 1.0 if Keyword.WINDFURY in kws else 0.0
        vec[9] = 1.0 if Keyword.FREEZE in kws else 0.0
        
        if minion:
            vec[10] = 1.0 if minion.summoning_sick else 0.0
            vec[11] = 1.0 if minion.frozen else 0.0
            vec[12] = float(minion.attacks_this_turn)
            
        return vec

    def encode_state(self, state: GameState) -> Dict[str, np.ndarray]:
        my_p = state.get_current_player()
        opp_p = state.get_opponent()
        
        obs = {}
        obs["my_hero"] = self._encode_hero(my_p)
        obs["opp_hero"] = self._encode_hero(opp_p)
        
        my_hand = np.zeros((MAX_HAND, CARD_FEATS), dtype=np.float32)
        for i, card in enumerate(my_p.hand):
            if i < MAX_HAND:
                my_hand[i] = self._encode_card(card)
        obs["my_hand"] = my_hand
        
        my_board = np.zeros((MAX_BOARD, CARD_FEATS), dtype=np.float32)
        for i, minion in enumerate(my_p.board):
            if i < MAX_BOARD:
                my_board[i] = self._encode_card(None, minion)
        obs["my_board"] = my_board
        
        opp_board = np.zeros((MAX_BOARD, CARD_FEATS), dtype=np.float32)
        for i, minion in enumerate(opp_p.board):
            if i < MAX_BOARD:
                opp_board[i] = self._encode_card(None, minion)
        obs["opp_board"] = opp_board
        
        return obs
