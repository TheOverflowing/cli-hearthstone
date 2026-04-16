import pytest
from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId, Keyword
from hsrl.core.card import Card
from hsrl.core.minion import Minion
from hsrl.core.actions import PlayMinion, Attack
from hsrl.core.effects import DealDamage, DrawCards, FreezeCharacter
from tests.utils import make_scenario


def setup_game_with_decks(game):
    for _ in range(10):
        game.players[PlayerId.P1].deck.append(Card("x", "y", 1, attack=1, health=1))
        game.players[PlayerId.P2].deck.append(Card("x", "y", 1, attack=1, health=1))
    game.setup_game()
    from hsrl.core.actions import MulliganCards
    game.step(MulliganCards(PlayerId.P1, []))
    game.step(MulliganCards(PlayerId.P2, []))

def test_charge():
    game = GameState()
    setup_game_with_decks(game)
    p1 = game.players[PlayerId.P1]
    p1.mana_crystals = 10
    
    charge_card = Card("c", "charge", 1, attack=2, health=1, keywords=[Keyword.CHARGE])
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
    
    m1 = Minion(card=Card("1", "atk", 1, attack=2, health=2))
    m1.summoning_sick = False
    p1.board.append(m1)
    
    # Give P2 a normal minion and a taunt minion
    m_normal = Minion(card=Card("2", "norm", 1, attack=1, health=1))
    m_taunt = Minion(card=Card("3", "taunt", 1, attack=1, health=1, keywords=[Keyword.TAUNT]))
    p2.board.extend([m_normal, m_taunt])
    
    legals = game.get_legal_actions()
    
    # Find attack actions for m1
    attacks = [a for a in legals if isinstance(a, Attack) and a.attacker_index == 0]
    # Taunt restricts target to index 1 (m_taunt)
    assert len(attacks) == 1
    assert attacks[0].target_index == 1

def test_divine_shield():
    minion = Minion(card=Card("1", "ds", 1, attack=1, health=1, keywords=[Keyword.DIVINE_SHIELD]))
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
    
    bc_card = Card("bc", "fire", 1, attack=1, health=1, requires_target=True, battlecry=DealDamage(3))
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
    
    dr_card = Card("dr", "loot", 1, attack=1, health=1, deathrattle=DrawCards(1))
    dr_minion = Minion(card=dr_card)
    dr_minion.summoning_sick = False
    p1.board.append(dr_minion)
    
    # Enemy minion to crash into
    p2.board.append(Minion(Card("t", "target", 1, attack=5, health=5)))
    
    initial_hand_size = len(p1.hand)
    
    # Attack to die
    game.step(Attack(PlayerId.P1, 0, 0))
    
    # DR Minion dies and draws a card.
    assert len(p1.board) == 0
    assert len(p1.hand) == initial_hand_size + 1

def test_cone_of_cold():
    from hsrl.cards.registry import get_card
    from hsrl.core.actions import PlaySpell
    from hsrl.core.enums import Phase
    cone = get_card("cone_of_cold")
    game = make_scenario(p1_hand=[cone], p1_mana=10, p2_deck=[])
    
    dummy1 = Minion(card=Card("1", "M1", 1, attack=1, health=5))
    dummy2 = Minion(card=Card("2", "M2", 1, attack=1, health=5))
    dummy3 = Minion(card=Card("3", "M3", 1, attack=1, health=5))
    game.players[PlayerId.P2].board = [dummy1, dummy2, dummy3]
    
    game.phase = Phase.MAIN_PHASE
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, 1)) # Hit the middle one
    
    assert dummy1.current_health == 4
    assert dummy2.current_health == 4
    assert dummy3.current_health == 4
    assert dummy1.frozen == True
    assert dummy2.frozen == True
    assert dummy3.frozen == True

def test_ice_lance():
    from hsrl.cards.registry import get_card
    from hsrl.core.actions import PlaySpell
    from hsrl.core.enums import Phase
    ice_lance1 = get_card("ice_lance")
    ice_lance2 = get_card("ice_lance")
    game = make_scenario(p1_hand=[ice_lance1, ice_lance2], p1_mana=10)
    
    dummy = Minion(card=Card("1", "M1", 1, attack=1, health=10))
    game.players[PlayerId.P2].board = [dummy]
    game.phase = Phase.MAIN_PHASE
    
    # First lance freezes
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, 0))
    assert dummy.frozen == True
    assert dummy.current_health == 10
    
    # Second lance deals 4
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, 0))
    assert dummy.frozen == True
    assert dummy.current_health == 6

def test_inner_fire():
    from hsrl.cards.registry import get_card
    from hsrl.core.actions import PlaySpell
    from hsrl.core.enums import Phase
    inner = get_card("inner_fire")
    game = make_scenario(p1_hand=[inner], p1_mana=10)
    
    dummy = Minion(card=Card("1", "M1", 1, attack=1, health=5))
    game.players[PlayerId.P1].board = [dummy]
    game.phase = Phase.MAIN_PHASE
    
    assert dummy.current_attack == 1
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P1, 0))
    assert dummy.current_attack == 5

def test_shadowflame():
    from hsrl.cards.registry import get_card
    from hsrl.core.actions import PlaySpell
    from hsrl.core.enums import Phase
    shadowflame = get_card("shadowflame")
    game = make_scenario(p1_hand=[shadowflame], p1_mana=10)
    
    friendly = Minion(card=Card("1", "F1", 1, attack=4, health=2))
    game.players[PlayerId.P1].board = [friendly]
    
    enemy1 = Minion(card=Card("1", "E1", 1, attack=1, health=5))
    enemy2 = Minion(card=Card("2", "E2", 1, attack=1, health=5))
    game.players[PlayerId.P2].board = [enemy1, enemy2]
    
    game.phase = Phase.MAIN_PHASE
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P1, 0))
    
    assert len(game.players[PlayerId.P1].board) == 0 # friendly sacrificed
    assert enemy1.current_health == 1
    assert enemy2.current_health == 1

