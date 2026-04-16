from hsrl.core.card import Card
from hsrl.cards.registry import register_card
from hsrl.core.enums import Keyword, CardType, HeroClass
from hsrl.core.effects import DrawCards, DealDamage, GainArmor

class SecretEffect:
    # Minimal placeholder for a secret trigger logic
    pass

def init_basic_set():
    # Phase 2 Vanillas
    register_card(Card(id="CS2_172", name="Bloodfen Raptor", cost=2, attack=3, health=2, description="A basic 3/2 beast."))
    register_card(Card(id="CS2_182", name="Chillwind Yeti", cost=4, attack=4, health=5, description="A solid 4/5 body."))
    register_card(Card(id="CS2_200", name="Boulderfist Ogre", cost=6, attack=6, health=7, description="Me smash! (6/7)"))
    register_card(Card(id="CS2_118", name="Magma Rager", cost=3, attack=5, health=1, description="5/1 stats."))
    register_card(Card(id="CS2_125", name="Ironfur Grizzly", cost=3, attack=3, health=3, keywords=[Keyword.TAUNT], description="Taunt"))
    register_card(Card(id="CS2_127", name="Silverback Patriarch", cost=3, attack=1, health=4, keywords=[Keyword.TAUNT], description="Taunt"))
    
    # Phase 4 Effect Cards
    register_card(Card(id="EX1_015", name="Novice Engineer", cost=2, attack=1, health=1, battlecry=DrawCards(1), description="Battlecry: Draw a card."))
    register_card(Card(id="EX1_096", name="Loot Hoarder", cost=2, attack=2, health=1, deathrattle=DrawCards(1), description="Deathrattle: Draw a card."))
    register_card(Card(id="CS2_152", name="Sen'jin Shieldmasta", cost=4, attack=3, health=5, keywords=[Keyword.TAUNT], description="Taunt"))
    register_card(Card(id="EX1_008", name="Argent Squire", cost=1, attack=1, health=1, keywords=[Keyword.DIVINE_SHIELD], description="Divine Shield"))
    register_card(Card(id="CS2_173", name="Bluegill Warrior", cost=2, attack=2, health=1, keywords=[Keyword.CHARGE], description="Charge"))
    
    # Targeted Battlecry
    register_card(Card(id="CS2_042", name="Fire Elemental", cost=6, attack=6, health=5, requires_target=True, battlecry=DealDamage(3), description="Battlecry: Deal 3 damage."))

    # Phase 8 Cards
    register_card(Card(id="CS2_106", name="Fiery War Axe", cost=2, type=CardType.WEAPON, hero_class=HeroClass.WARRIOR, weapon_stats=(3, 2), description="A 3/2 weapon."))
    register_card(Card(id="EX1_289", name="Ice Barrier", cost=3, type=CardType.SECRET, hero_class=HeroClass.MAGE, secret_effect=SecretEffect(), description="Secret: When your hero is attacked, gain 8 Armor."))
    register_card(Card(id="CS2_029", name="Fireball", cost=4, type=CardType.SPELL, hero_class=HeroClass.MAGE, requires_target=True, spell_effect=DealDamage(6), description="Deal 6 damage."))
