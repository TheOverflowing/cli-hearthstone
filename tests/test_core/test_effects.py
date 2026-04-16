import pytest
from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId, Keyword
from hsrl.core.card import Card
from hsrl.core.minion import Minion
from hsrl.core.actions import PlayMinion, Attack
from hsrl.core.effects import DealDamage, DrawCards

def setup_game_with_decks(game):
    for _ in range(10):
        game.players[PlayerId.P1].deck.append(Card("x", "y", 1, 1, 1))
        game.players[PlayerId.P2].deck.append(Card("x", "y", 1, 1, 1))
    game.setup_game()

def test_charge():
    game = GameState()
    setup_game_with_decks(game)
    p1 = game.players[PlayerId.P1]
    p1.mana_crystals = 10
    
    charge_card = Card("c", "charge", 1, 2, 1, keywords=[Keyword.CHARGE])
    p1.hand.append(charge_card)
    
    game.step(PlayMinion(PlayerId.P1, len(p1.hand)-1, 0))
    
    # Should not have summoning sickness, so can attack
    m1 = p1.board[0]
    assert m1.summoning_sick == False
    
    # Check legal actions to verify we can attack the enemy hero immediately
    legals = game.get_legal_actions()
    attack_action = Attack(PlayerId.P1, 0, -1)
    assert attack_action in legals

def test_taunt_filtering():
    game = GameState()
    setup_game_with_decks(game)
    p1 = game.players[PlayerId.P1]
    p2 = game.get_opponent()
    
    m1 = Minion(card=Card("1", "atk", 1, 2, 2))
    m1.summoning_sick = False
    p1.board.append(m1)
    
    # Give P2 a normal minion and a taunt minion
    m_normal = Minion(card=Card("2", "norm", 1, 1, 1))
    m_taunt = Minion(card=Card("3", "taunt", 1, 1, 1, keywords=[Keyword.TAUNT]))
    p2.board.extend([m_normal, m_taunt])
    
    legals = game.get_legal_actions()
    
    # Find attack actions for m1
    attacks = [a for a in legals if isinstance(a, Attack) and a.attacker_index == 0]
    # Taunt restricts target to index 1 (m_taunt)
    assert len(attacks) == 1
    assert attacks[0].target_index == 1

def test_divine_shield():
    minion = Minion(card=Card("1", "ds", 1, 1, 1, keywords=[Keyword.DIVINE_SHIELD]))
    assert minion.divine_shield == True
    assert minion.current_health == 1
    
    # Takes 5 damage, drops shield, health unchanged
    minion.take_damage(5)
    assert minion.divine_shield == False
    assert minion.current_health == 1
    
    # Takes 1 damage, dies
    minion.take_damage(1)
    assert minion.is_dead()

def test_battlecry_damage():
    game = GameState()
    setup_game_with_decks(game)
    p1 = game.players[PlayerId.P1]
    p2 = game.get_opponent()
    p1.mana_crystals = 10
    
    # P2 hero is at 30 hp.
    assert p2.health == 30
    
    bc_card = Card("bc", "fire", 1, 1, 1, requires_target=True, battlecry=DealDamage(3))
    p1.hand.append(bc_card)
    
    # Play minion targeting P2 hero (-1)
    game.step(PlayMinion(PlayerId.P1, len(p1.hand)-1, 0, PlayerId.P2, -1))
    
    # P2 hero takes 3 damage
    assert p2.health == 27
    assert len(p1.board) == 1

def test_deathrattle_draw():
    game = GameState()
    setup_game_with_decks(game)
    p1 = game.players[PlayerId.P1]
    p2 = game.get_opponent()
    
    dr_card = Card("dr", "loot", 1, 1, 1, deathrattle=DrawCards(1))
    dr_minion = Minion(card=dr_card)
    dr_minion.summoning_sick = False
    p1.board.append(dr_minion)
    
    # Enemy minion to crash into
    p2.board.append(Minion(Card("t", "target", 1, 5, 5)))
    
    initial_hand_size = len(p1.hand)
    
    # Attack to die
    game.step(Attack(PlayerId.P1, 0, 0))
    
    # DR Minion dies and draws a card.
    assert len(p1.board) == 0
    assert len(p1.hand) == initial_hand_size + 1
