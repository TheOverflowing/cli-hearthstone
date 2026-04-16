import gymnasium as gym
import numpy as np
from typing import Tuple, Dict, Any, Optional

from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId
from hsrl.rl.observation import ObservationEncoder
from hsrl.rl.action_space import ActionEncoder, TOTAL_ACTIONS
from hsrl.agents.base import Agent, RandomAgent

class HearthstoneGame:
    """
    Low-level, symmetric, no "agent" concept baked in.
    Returns observations from the perspective of the *current* active player.
    """
    def __init__(self):
        self.state = GameState()
        self.obs_encoder = ObservationEncoder()
        self.action_encoder = ActionEncoder()

    def reset(self, seed=None) -> Tuple[Dict[str, np.ndarray], int]:
        if seed is not None:
            # We would seed RNG if we had stochastic mechanics implemented
            pass
            
        self.state = GameState()
        self.state.setup_game()
        
        obs = self.obs_encoder.encode_state(self.state)
        # We return the player ID integer. Let's say 0 for P1, 1 for P2.
        pid_int = 0 if self.state.current_player_id == PlayerId.P1 else 1
        return obs, pid_int
        
    def _get_reward(self) -> float:
        if not self.state.is_terminal(): return 0.0
        winner = self.state.get_winner()
        if winner == self.state.current_player_id: return 1.0
        if winner is None: return 0.0 # Draw
        return -1.0 # Loss
        
    def _get_info(self) -> Dict[str, Any]:
        return {
            "action_mask": self.action_encoder.get_action_mask(self.state)
        }

    def step(self, action_idx: int) -> Tuple[Dict[str, np.ndarray], float, bool, Dict[str, Any]]:
        action = self.action_encoder.decode_action(action_idx, self.state)
        # Execute the action
        pre_step_player = self.state.current_player_id
        
        try:
            self.state.step(action)
        except Exception as e:
            # If the action was masked, this shouldn't happen.
            # If it does, we pass EndTurn
            from hsrl.core.actions import EndTurn
            self.state.step(EndTurn(pre_step_player))
            
        reward = self._get_reward()
        done = self.state.is_terminal()
        obs = self.obs_encoder.encode_state(self.state)
        info = self._get_info()
        
        return obs, reward, done, info

class HearthstoneEnv(gym.Env):
    """
    Gym-compatible wrapper for single-agent RL.
    Alternates turns automatically with a given opponent agent.
    """
    def __init__(self, opponent: Agent = None, agent_plays_as: int = 0):
        super().__init__()
        self.game = HearthstoneGame()
        self.opponent = opponent if opponent is not None else RandomAgent()
        self.agent_id = agent_plays_as
        
        self.observation_space = self.game.obs_encoder.observation_space
        self.action_space = gym.spaces.Discrete(TOTAL_ACTIONS)
        
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        super().reset(seed=seed)
        obs, current_player_id = self.game.reset(seed=seed)
        info = self.game._get_info()
        
        # If it's opponent's turn first, run their actions until it's our turn
        # Usually P1 goes first. If agent is P2, sim P1's turn
        while not self.game.state.is_terminal() and current_player_id != self.agent_id:
            opp_action = self.opponent.choose_action(obs, info["action_mask"])
            obs, reward, done, info = self.game.step(opp_action)
            current_player_id = 0 if self.game.state.current_player_id == PlayerId.P1 else 1

        return obs, info

    def step(self, action: int) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        obs, reward, done, info = self.game.step(action)
        current_player_id = 0 if self.game.state.current_player_id == PlayerId.P1 else 1
        
        # Simulate opponent until it's our turn again or game ends
        while not done and current_player_id != self.agent_id:
            opp_action = self.opponent.choose_action(obs, info["action_mask"])
            obs, op_reward, done, info = self.game.step(opp_action)
            current_player_id = 0 if self.game.state.current_player_id == PlayerId.P1 else 1
            # Reward from our perspective is inverse of opponent's terminal reward
            # Wait, `op_reward` is from the perspective of the current_player_id inside `step`
            # When the game terminates, `is_terminal()` will cause `_get_reward` to be eval'd
            # for the player whose action just completed or who is active.
            # Realistically, terminal reward is +1 for winner, -1 for loser.
            # If we just compute from GameState directly here:
            if done:
                winner = self.game.state.get_winner()
                p_id = PlayerId.P1 if self.agent_id == 0 else PlayerId.P2
                if winner == p_id:
                    reward = 1.0
                elif winner is None:
                    reward = 0.0
                else:
                    reward = -1.0
        
        # Determine actual absolute reward for the agent here to be safe
        if done:
            winner = self.game.state.get_winner()
            p_id = PlayerId.P1 if self.agent_id == 0 else PlayerId.P2
            if winner == p_id:
                reward = 1.0
            elif winner is None:
                reward = 0.0
            else:
                reward = -1.0
        else:
            reward = 0.0
            
        truncated = False
        return obs, reward, done, truncated, info
