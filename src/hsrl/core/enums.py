from enum import Enum, auto

class Phase(Enum):
    MULLIGAN = auto()
    START_TURN = auto()
    MAIN_PHASE = auto()
    END_TURN = auto()

class PlayerId(Enum):
    P1 = auto()
    P2 = auto()

    def opponent(self) -> "PlayerId":
        return PlayerId.P2 if self == PlayerId.P1 else PlayerId.P1

class Keyword(Enum):
    TAUNT = auto()
    CHARGE = auto()
    DIVINE_SHIELD = auto()
    STEALTH = auto()
    WINDFURY = auto()
    FREEZE = auto()
    SECRET = auto()

class CardType(Enum):
    MINION = auto()
    SPELL = auto()
    WEAPON = auto()
    HERO = auto()
    SECRET = auto()

class HeroClass(Enum):
    NEUTRAL = auto()
    MAGE = auto()
    WARRIOR = auto()
    PRIEST = auto()
    HUNTER = auto()
    PALADIN = auto()
    WARLOCK = auto()
    DRUID = auto()
    SHAMAN = auto()
    ROGUE = auto()
