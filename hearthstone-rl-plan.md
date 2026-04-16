# CLI Hearthstone RL — Technical Plan

A phased plan for building a CLI Hearthstone simulator suitable for reinforcement learning, structured for incremental vibe-coding with an AI assistant.

---

## Tech Stack

- **Python 3.11+** — better type hints and performance
- **uv** or **Poetry** — dependency management (uv is faster and more modern)
- **pytest** — testing
- **pydantic** — data validation and serialization
- **rich** — CLI rendering (pretty terminal output)
- **gymnasium** — RL environment interface
- **stable-baselines3** + **sb3-contrib** — RL algorithms (later phase)
- **numpy** — observation arrays

---

## Project Structure

```
hearthstone-rl/
├── pyproject.toml
├── README.md
├── DESIGN.md
├── src/
│   └── hsrl/
│       ├── __init__.py
│       ├── core/              # Game engine (pure logic, no I/O)
│       │   ├── __init__.py
│       │   ├── enums.py       # CardType, Zone, Phase, etc.
│       │   ├── entity.py      # Base Entity class
│       │   ├── card.py        # Card definitions
│       │   ├── minion.py      # Minion runtime state
│       │   ├── player.py      # Player state
│       │   ├── game.py        # GameState, main game loop
│       │   ├── actions.py     # Action types and validation
│       │   ├── events.py      # Event bus / trigger system
│       │   └── effects.py     # Card effect implementations
│       ├── cards/             # Card database
│       │   ├── __init__.py
│       │   ├── registry.py    # Card lookup
│       │   └── sets/          # Card definitions by set
│       │       ├── basic.py
│       │       └── neutral.py
│       ├── cli/               # CLI rendering (consumer of core)
│       │   ├── __init__.py
│       │   ├── renderer.py    # Pretty-print game state
│       │   ├── input.py       # Human input parsing
│       │   └── play.py        # Interactive play loop
│       ├── agents/            # Non-RL agents
│       │   ├── __init__.py
│       │   ├── base.py        # Agent interface
│       │   ├── random_agent.py
│       │   └── human_agent.py
│       └── rl/                # RL layer (consumer of core)
│           ├── __init__.py
│           ├── env.py         # Gymnasium environment
│           ├── observation.py # State → array encoding
│           └── action_space.py # Action encoding/masking
└── tests/
    ├── test_core/
    ├── test_cards/
    └── test_rl/
```

**Key architectural rule:** `core/` must not import from `cli/`, `rl/`, or `agents/`. The dependency arrow points inward only.

---

## Phase 1: Minimal Game Engine (Week 1–2)

**Goal:** Two players, heroes only, just attacking each other. No cards yet.

**Deliverables:**
- `GameState` class tracking two players, health, mana, turn number
- `Player` class with health (30), mana crystals, max mana
- Turn phases: start turn → main phase → end turn
- Actions: `EndTurn` (and `HeroAttack` later when weapons exist)
- Win condition: health ≤ 0
- Unit tests for turn flow, mana increment, win detection

At this stage the game is trivially boring, but you've established the action/state loop that everything else plugs into.

---

## Phase 2: Minions and Combat (Week 2–3)

**Goal:** Play minions from hand, attack with them.

**Deliverables:**
- `Card` dataclass with `cost`, `attack`, `health`, `name`, `id`
- `Minion` runtime class (separate from `Card` — board minions have state: damage, buffs, has_attacked, summoning_sick)
- `Hand`, `Deck`, `Board` zones (capacity: 10, 60, 7)
- Actions: `PlayMinion(card_id, position)`, `Attack(attacker_id, target_id)`
- Legal action enumeration: given a state, return all legal actions
- Draw mechanic (with fatigue damage when deck empty)
- Starting hand: 3 or 4 cards (mulligan comes later)
- 10–20 vanilla minions (stat sticks, no effects yet)

Legal action enumeration becomes critical here. Build it correctly now — the RL env depends on it.

---

## Phase 3: CLI and Human Play (Week 3)

**Goal:** You can actually play a game against yourself or a random agent.

**Deliverables:**
- `Renderer` prints game state: both boards, hands (hide opponent's), mana, health
- `HumanAgent` takes input like `play 2 3` (play hand index 2 at board position 3) or `attack 1 opp0`
- `RandomAgent` picks uniformly from legal actions
- `play.py` script: `python -m hsrl.cli.play --p1 human --p2 random`

Use `rich` for colored output — makes debugging much more pleasant. Treat this phase as a reward for finishing the engine work.

---

## Phase 4: Event System and Card Effects (Week 4–5)

**Goal:** Support cards with effects (battlecry, deathrattle, taunt, etc.)

This is the hardest phase. Get it right.

**Deliverables:**
- Event bus: `MinionPlayed`, `MinionDied`, `DamageDealt`, `TurnStarted`, etc.
- `Effect` base class; effects register as listeners on events
- Keyword abstractions: `Taunt`, `Charge`, `DivineShield`, `Stealth`, `Windfury`
- Battlecry framework: effects triggered when minion is played
- Deathrattle framework: effects triggered when minion dies
- Targeting system: validate targets for effects that need them
- 20–30 cards with real effects (Fire Elemental, Chillwind Yeti, Voidwalker, Loot Hoarder, Novice Engineer, etc.)

**Design tip:** represent effects declaratively when possible. Instead of custom Python functions per card, use composable primitives like `DealDamage(target, amount)`, `DrawCards(player, n)`, `SummonMinion(card_id)`. Much easier to test and debug.

---

## Phase 5: Spells and Heroes (Week 5–6)

**Goal:** Add spells and hero powers.

**Deliverables:**
- `Spell` card type
- Action: `PlaySpell(card_id, target?)`
- A few classes — start with Mage (Fireball, Frostbolt, Arcane Intellect, Polymorph) and Warrior (Shield Slam, Execute, Whirlwind)
- Hero powers: Fireblast (Mage), Armor Up (Warrior)
- Action: `UseHeroPower(target?)`
- Deck validation: 30 cards, class restriction

---

## Phase 6: RL Environment (Week 6–7)

**Goal:** Wrap the engine in a Gymnasium environment.

**Deliverables:**
- `HearthstoneEnv(gym.Env)` with `reset()` and `step(action)`
- Observation space: `Dict` with keys like `my_board`, `opp_board`, `my_hand`, `mana`, `my_health`, `opp_health`. Each a fixed-size numpy array with padding.
- Action space: `Discrete(N)` where N is the max possible actions. Use an action encoding scheme that maps integers to game actions.
- `info` dict includes `action_mask`: boolean array of legal actions
- Reward: +1 win, −1 loss, 0 otherwise (start simple)
- Determinism: `reset(seed=...)` fully seeds the RNG

Observation design is where you'll iterate most. Start with a flat, padded representation; optimize later.

---

## Phase 7: Training a Baseline Agent (Week 7–8)

**Goal:** Train something that beats the random agent.

**Deliverables:**
- Integration with `sb3-contrib.MaskablePPO` (PPO with action masking)
- Training script with logging (tensorboard or wandb)
- Self-play loop: periodically update the opponent to a copy of the current agent
- Evaluation script: win rate vs random agent, vs older versions of itself

Expect to spend real time tuning hyperparameters and debugging reward signals. Getting above random is easy; getting to actually-decent play is where the real learning happens.

---

## Phase 8: Expansion (Ongoing)

Once the above works, you can expand:
- More cards (aim for 200–300 before stopping)
- More classes
- Mulligan phase
- Secrets (tricky — delayed triggers)
- Weapons
- Better observation encodings (graph neural networks, card embeddings)
- MCTS + RL hybrid (AlphaZero-style)

---

## Vibe-Coding Tips

When handing tasks to an AI assistant:

1. **Do one file at a time.** "Implement `src/hsrl/core/player.py` with these requirements…" works much better than "build the whole engine."

2. **Write the test first, or alongside.** "Here's the test for `Deck.draw()` — now implement it." AI tools are great at this and it keeps them honest.

3. **Paste the existing interfaces.** When adding a new module, include the relevant enum definitions and class signatures from existing modules so the AI doesn't invent conflicting APIs.

4. **Keep a `DESIGN.md`.** Record decisions like "minions are separate from cards," "effects are declarative," "action space is flat Discrete." Paste relevant excerpts when starting new sessions.

5. **Card-by-card after Phase 4.** Adding cards becomes a repeatable pattern — "implement these 5 cards following the same structure as the existing ones."

6. **Commit after each phase.** You'll want to roll back when a redesign goes sideways.

---

## Quick Start Checklist

- [ ] Set up repo with `uv init` or `poetry new`
- [ ] Create folder structure above
- [ ] Write `DESIGN.md` with your architectural decisions
- [ ] Phase 1: minimal game loop + tests
- [ ] Phase 2: minions + combat + legal action enumeration
- [ ] Phase 3: CLI + human/random play
- [ ] Phase 4: event system + 20 real cards
- [ ] Phase 5: spells + hero powers + 2 classes
- [ ] Phase 6: Gymnasium env wrapper
- [ ] Phase 7: train MaskablePPO agent
- [ ] Phase 8: expand and experiment
