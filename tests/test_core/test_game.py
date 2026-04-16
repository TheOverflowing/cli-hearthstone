import pytest
from hsrl.core.enums import PlayerId, Phase, HeroClass, CardType
from hsrl.core.game import GameState
from hsrl.core.actions import EndTurn, MulliganCards, PlaySpell, UseHeroPower
from hsrl.core.card import Card
from hsrl.core.effects import DealDamage, FreezeCharacter
from tests.utils import make_scenario

def test_game_initialization():
    game = make_scenario(p1_mana=0, p2_mana=0)
    assert game.turn_number == 1
    assert game.current_player_id == PlayerId.P1
    
    # In make scenario, we just returned a populated gamestate, we still need to mimic starting game correctly.
    # Note: make_scenario already created decks because p1_deck was None.
    game.phase = Phase.START_TURN
    game.setup_game()
    assert game.phase == Phase.MULLIGAN
    
    game.step(MulliganCards(PlayerId.P1, []))
    game.step(MulliganCards(PlayerId.P2, []))
    
    assert game.phase == Phase.MAIN_PHASE
    
    p1 = game.get_current_player()
    assert p1.health == 30
    assert len(p1.hand) == 4 # 3 setup + 1 turn draw
    assert p1.max_mana == 1
    assert p1.mana_crystals == 1

def test_turn_flow_and_mana():
    game = make_scenario(p1_mana=0, p2_mana=0)
    game.phase = Phase.START_TURN
    game.setup_game()
    game.step(MulliganCards(PlayerId.P1, []))
    game.step(MulliganCards(PlayerId.P2, []))
    
    p1 = game.players[PlayerId.P1]
    p2 = game.players[PlayerId.P2]
    
    # End P1 turn 1
    game.step(EndTurn(player_id=PlayerId.P1))
    
    assert game.current_player_id == PlayerId.P2
    assert game.turn_number == 1
    assert p2.max_mana == 1
    assert p2.mana_crystals == 1
    
    # End P2 turn 1
    game.step(EndTurn(player_id=PlayerId.P2))
    
    assert game.current_player_id == PlayerId.P1
    assert game.turn_number == 2
    assert p1.max_mana == 2
    assert p1.mana_crystals == 2

def test_win_condition():
    game = make_scenario()
    p2 = game.get_opponent()
    
    assert not game.is_terminal()
    assert game.get_winner() is None
    
    # Deal lethal damage
    p2.take_damage(30)
    
    assert game.is_terminal()
    assert game.get_winner() == PlayerId.P1

def test_play_spell():
    spell = Card("fireball", "Fireball", 4, 0, 0, CardType.SPELL, requires_target=True, spell_effect=DealDamage(6))
    game = make_scenario(
        p1_hand=[spell],
        p1_mana=10,
        p2_health=30
    )
    # the phase is initially START_TURN in make_scenario if we don't set it, but GameState default is START_TURN. 
    # to play, we should be MAIN_PHASE.
    game.phase = Phase.MAIN_PHASE
    p1 = game.players[PlayerId.P1]
    
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, -1))
    
    p2 = game.get_opponent()
    assert p2.health == 24
    assert p1.mana_crystals == 6

def test_hero_power_mage():
    game = make_scenario(
        p1_class=HeroClass.MAGE,
        p1_mana=2,
        p2_health=30
    )
    game.phase = Phase.MAIN_PHASE
    p1 = game.players[PlayerId.P1]
    
    game.step(UseHeroPower(PlayerId.P1, PlayerId.P2, -1))
    
    p2 = game.get_opponent()
    assert p2.health == 29
    assert p1.mana_crystals == 0
    assert p1.hero_power_used_this_turn == True

def test_hero_power_warrior():
    game = make_scenario(
        p1_class=HeroClass.WARRIOR,
        p1_mana=2
    )
    game.phase = Phase.MAIN_PHASE
    p1 = game.players[PlayerId.P1]
    
    game.step(UseHeroPower(PlayerId.P1))
    
    assert p1.armor == 2
    assert p1.mana_crystals == 0

def test_freeze_character():
    frost_nova = Card("nova", "Nova", 3, 0, 0, CardType.SPELL, requires_target=True, spell_effect=FreezeCharacter())
    game = make_scenario(
        p1_hand=[frost_nova],
        p1_mana=10
    )
    game.phase = Phase.MAIN_PHASE
    p1 = game.players[PlayerId.P1]
    p2 = game.get_opponent()
    
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, -1))
    
    assert p2.frozen == True
    
    # End turn
    game.step(EndTurn(PlayerId.P1))
    
    # End P2 turn, P2 should be unfrozen
    game.step(EndTurn(PlayerId.P2))
    assert p2.frozen == False
