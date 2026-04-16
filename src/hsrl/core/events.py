from dataclasses import dataclass
from typing import Callable, List, Type, Any

class Event:
    pass

@dataclass
class MinionPlayed(Event):
    player_id: Any  # PlayerId enum
    minion: Any     # Minion object

@dataclass
class MinionDied(Event):
    player_id: Any  # PlayerId
    minion: Any

@dataclass
class DamageDealt(Event):
    source: Any
    target: Any
    amount: int

@dataclass
class TurnStarted(Event):
    player_id: Any

@dataclass
class SpellPlayed(Event):
    player_id: Any
    card: Any

from enum import Enum, auto

class EventPhase(Enum):
    PRE_RESOLUTION = auto()
    MAIN = auto()

class EventBus:
    def __init__(self):
        self._listeners = {EventPhase.PRE_RESOLUTION: {}, EventPhase.MAIN: {}}

    def subscribe(self, event_type: Type[Event], listener: Callable[[Event], None], phase: EventPhase = EventPhase.MAIN):
        if event_type not in self._listeners[phase]:
            self._listeners[phase][event_type] = []
        self._listeners[phase][event_type].append(listener)

    def publish(self, event: Event):
        event_type = type(event)
        
        if event_type in self._listeners[EventPhase.PRE_RESOLUTION]:
            for listener in self._listeners[EventPhase.PRE_RESOLUTION][event_type]:
                listener(event)
                
        if event_type in self._listeners[EventPhase.MAIN]:
            for listener in self._listeners[EventPhase.MAIN][event_type]:
                listener(event)
