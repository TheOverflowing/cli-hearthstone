import pytest
from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId
from hsrl.core.card import Card

def test_draw_and_fatigue():
    game = GameState()
    p1 = game.players[PlayerId.P1]
    
    c1 = Card("id", "name", 1, 1, 1)
    p1.deck = [c1, c1]
    
    game.setup_game()
    # 3 drawn cards during setup, + 1 drawn at start of turn 1.
    # Total cards in deck originally 2.
    # Draws 1 & 2 succeed.
    # Draw 3 (setup) -> fatigue 1 (health 29)
    # Draw 4 (start_turn) -> fatigue 2 (health 27)
    
    assert len(p1.hand) == 2
    assert p1.fatigue_counter == 2
    assert p1.health == 27
    
    p1.draw_card()
    assert p1.fatigue_counter == 3
    assert p1.health == 24 # 27 - 3
