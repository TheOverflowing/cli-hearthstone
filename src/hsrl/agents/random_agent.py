import random
from typing import List
from .base import Agent
from hsrl.core.game import GameState
from hsrl.core.actions import Action

class RandomAgent(Agent):
    def get_action(self, state: GameState, legal_actions: List[Action]) -> Action:
        return random.choice(legal_actions)
