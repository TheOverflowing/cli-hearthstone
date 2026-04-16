import pytest
from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId
from hsrl.core.card import Card
from hsrl.core.minion import Minion
from hsrl.core.actions import PlayMinion, Attack

def test_play_and_attack():
    game = GameState()
    p1 = game.players[PlayerId.P1]
    p1.mana_crystals = 10
    
    c1 = Card("test1", "yeti", 4, 4, 5)
    c2 = Card("test2", "raptor", 2, 3, 2)
    p1.hand.append(c1)
    
    # Play minion
    game.step(PlayMinion(player_id=PlayerId.P1, hand_index=0, board_position=0))
    assert len(p1.hand) == 0
    assert len(p1.board) == 1
    assert p1.board[0].card.id == "test1"
    assert p1.board[0].summoning_sick == True
    
    # Cannot attack immediately due to sickness (except charge, which is not checked here, so we assume we wait)
    # The Action enumeration handles legal actions, not the step. Step will just fail if we don't protect it, but it actually doesn't check summoning sick inside step.
    # Let's manually unset summoning sickness to simulate a turn passing
    p1.board[0].summoning_sick = False
    
    p2 = game.get_opponent()
    m2 = Minion(card=c2)
    m2.summoning_sick = False
    p2.board.append(m2)
    
    # P1 Yeti attacks P2 Raptor
    game.step(Attack(player_id=PlayerId.P1, attacker_index=0, target_index=0))
    
    # Raptor takes 4 damage (has 2 health), dies, gets removed
    assert m2.is_dead()
    
    # Yeti takes 3 damage (has 5 health), survives with 2 health
    yeti = p1.board[0]
    assert yeti.current_health == 2
    assert yeti.has_attacked == True
    
    # Dead minion is removed from board
    assert len(p2.board) == 0
