import random
from typing import Any

class Agent:
    def choose_action(self, obs: Any, action_mask: Any) -> int:
        raise NotImplementedError

    def get_action(self, state: Any, legal_actions: Any) -> Any:
        raise NotImplementedError

class RandomRLAgent(Agent):
    def choose_action(self, obs: Any, action_mask: Any) -> int:
        valid_indices = [i for i, valid in enumerate(action_mask) if valid]
        if not valid_indices:
            return 0 
        return random.choice(valid_indices)
