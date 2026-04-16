# CLI Hearthstone RL — Design & Architecture

## Core Principles
1. **Dependency Inward Only**: `core/` must not import from `cli/`, `rl/`, or `agents/`.
2. **Phase Isolation**: Build features incrementally, strictly adhering to the planned phases.
3. **Data Classes**: Pure game logic (entities like Player, Action) use standard Python `dataclasses`.
4. **Action representation**: State transitions are strictly performed by applying an `Action`.

## Game Logic
- **Minions vs Cards**: Minions on board have runtime state (damage, buffs). Cards are static base definitions.
- **Effects**: Declared with composable primitives (e.g. `DealDamage`, `DrawCards`) triggered by an event bus, rather than customized python funcs per card.
- **Action Space**: Flat and discrete for RL convenience. `Action` objects are the source of truth for the engine.
