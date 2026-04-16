import pytest
from hsrl.core.enums import PlayerId, Phase
from hsrl.core.game import GameState
from hsrl.core.actions import EndTurn
from hsrl.core.card import Card

def test_game_initialization():
    game = GameState()
    assert game.turn_number == 1
    assert game.current_player_id == PlayerId.P1
    assert game.phase == Phase.START_TURN
    
    # Give some empty cards so we don't fatigue during setup
    for _ in range(10):
        game.players[PlayerId.P1].deck.append(Card("x", "y", 1, 1, 1))
        game.players[PlayerId.P2].deck.append(Card("x", "y", 1, 1, 1))
        
    game.setup_game()
    assert game.phase == Phase.MULLIGAN
    
    from hsrl.core.actions import MulliganCards
    game.step(MulliganCards(PlayerId.P1, []))
    game.step(MulliganCards(PlayerId.P2, []))
    
    assert game.phase == Phase.MAIN_PHASE
    
    p1 = game.get_current_player()
    assert p1.health == 30
    assert len(p1.hand) == 4 # 3 setup + 1 turn draw
    assert p1.max_mana == 1
    assert p1.mana_crystals == 1

def test_turn_flow_and_mana():
    game = GameState()
    # Give some empty cards so we don't fatigue
    for _ in range(10):
        game.players[PlayerId.P1].deck.append(Card("x", "y", 1, 1, 1))
        game.players[PlayerId.P2].deck.append(Card("x", "y", 1, 1, 1))
        
    game.setup_game()
    from hsrl.core.actions import MulliganCards
    game.step(MulliganCards(PlayerId.P1, []))
    game.step(MulliganCards(PlayerId.P2, []))
    
    p1 = game.players[PlayerId.P1]
    p2 = game.players[PlayerId.P2]
    
    # End P1 turn 1
    action = EndTurn(player_id=PlayerId.P1)
    game.step(action)
    
    assert game.current_player_id == PlayerId.P2
    assert game.turn_number == 1
    assert p2.max_mana == 1
    assert p2.mana_crystals == 1
    
    # End P2 turn 1
    action = EndTurn(player_id=PlayerId.P2)
    game.step(action)
    
    assert game.current_player_id == PlayerId.P1
    assert game.turn_number == 2
    assert p1.max_mana == 2
    assert p1.mana_crystals == 2

def test_win_condition():
    game = GameState()
    p2 = game.get_opponent()
    
    assert not game.is_terminal()
    assert game.get_winner() is None
    
    # Deal lethal damage
    p2.take_damage(30)
    
    assert game.is_terminal()
    assert game.get_winner() == PlayerId.P1

def test_play_spell():
    from hsrl.core.enums import CardType
    from hsrl.core.actions import PlaySpell
    from hsrl.core.effects import DealDamage
    
    game = GameState()
    p1 = game.players[PlayerId.P1]
    p1.mana_crystals = 10
    
    spell = Card("fireball", "Fireball", 4, 0, 0, CardType.SPELL, requires_target=True, spell_effect=DealDamage(6))
    p1.hand.append(spell)
    
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, -1))
    
    p2 = game.get_opponent()
    assert p2.health == 24
    assert p1.mana_crystals == 6

def test_hero_power_mage():
    from hsrl.core.enums import HeroClass
    from hsrl.core.actions import UseHeroPower
    
    game = GameState()
    p1 = game.players[PlayerId.P1]
    p1.hero_class = HeroClass.MAGE
    p1.mana_crystals = 2
    
    game.step(UseHeroPower(PlayerId.P1, PlayerId.P2, -1))
    
    p2 = game.get_opponent()
    assert p2.health == 29
    assert p1.mana_crystals == 0
    assert p1.hero_power_used_this_turn == True

def test_hero_power_warrior():
    from hsrl.core.enums import HeroClass
    from hsrl.core.actions import UseHeroPower
    
    game = GameState()
    p1 = game.players[PlayerId.P1]
    p1.hero_class = HeroClass.WARRIOR
    p1.mana_crystals = 2
    
    game.step(UseHeroPower(PlayerId.P1))
    
    assert p1.armor == 2
    assert p1.mana_crystals == 0

def test_freeze_character():
    from hsrl.core.effects import FreezeCharacter
    from hsrl.core.actions import PlaySpell, EndTurn
    from hsrl.core.enums import CardType
    
    game = GameState()
    p1 = game.players[PlayerId.P1]
    p1.mana_crystals = 10
    
    frost_nova = Card("nova", "Nova", 3, 0, 0, CardType.SPELL, requires_target=True, spell_effect=FreezeCharacter())
    p1.hand.append(frost_nova)
    
    game.step(PlaySpell(PlayerId.P1, 0, PlayerId.P2, -1))
    
    p2 = game.get_opponent()
    assert p2.frozen == True
    
    # End turn
    game.step(EndTurn(PlayerId.P1))
    
    # End P2 turn, P2 should be unfrozen
    game.step(EndTurn(PlayerId.P2))
    assert p2.frozen == False
