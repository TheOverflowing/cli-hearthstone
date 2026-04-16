from typing import List, Optional
from hsrl.core.game import GameState
from hsrl.core.card import Card
from hsrl.core.enums import PlayerId, HeroClass

def make_scenario(
    p1_hand: Optional[List[Card]] = None,
    p1_deck: Optional[List[Card]] = None,
    p1_mana: int = 1,
    p1_health: int = 30,
    p1_class: HeroClass = HeroClass.NEUTRAL,
    p2_hand: Optional[List[Card]] = None,
    p2_deck: Optional[List[Card]] = None,
    p2_mana: int = 1,
    p2_health: int = 30,
    p2_class: HeroClass = HeroClass.NEUTRAL,
    turn_number: int = 1,
    current_player: PlayerId = PlayerId.P1
) -> GameState:
    """Helper to quickly set up a specific game state scenario for tests."""
    game = GameState()
    game.turn_number = turn_number
    game.current_player_id = current_player
    
    p1 = game.players[PlayerId.P1]
    p2 = game.players[PlayerId.P2]
    
    p1.hero_class = p1_class
    p1.health = p1_health
    p1.mana_crystals = p1_mana
    p1.max_mana = p1_mana
    
    p2.hero_class = p2_class
    p2.health = p2_health
    p2.mana_crystals = p2_mana
    p2.max_mana = p2_mana

    if p1_hand:
        p1.hand = p1_hand[:]
    if p2_hand:
        p2.hand = p2_hand[:]
        
    if p1_deck:
        p1.deck = p1_deck[:]
    if p2_deck:
        p2.deck = p2_deck[:]

    # Avoid fatigue on draw
    if not p1.deck:
        p1.deck = [Card("dummy", "Dummy", 1) for _ in range(30)]
    if not p2.deck:
        p2.deck = [Card("dummy", "Dummy", 1) for _ in range(30)]
        
    return game
