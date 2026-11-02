# SLO Games

A collection of puzzle and arcade games written in Python with [Pygame](https://www.pygame.org/), most of them paired with an AI: a Hamiltonian-cycle Snake solver, a logic Minesweeper solver, and an endless runner built to train a reinforcement learning agent.

> The in-game interface is in French.

## Games

| Game | Type | AI |
|---|---|---|
| **Binairo+** | Logic puzzle | – |
| **Snake** | Arcade | Hamiltonian-cycle solver with verified shortcuts |
| **Démineur** (Minesweeper) | Logic puzzle | Constraint solver with hints |
| **Runner** | Endless runner | Reinforcement learning (in progress) |

### Binairo+
Fill a 10×10 grid with white and black cells. No more than two cells of the same color in a row, and every row and column holds as many whites as blacks. `=` and `x` hints between two cells tell you whether they are the same color or opposite colors.

- **Click** a cell: cycle empty → white → black
- **Vérifier**: check your solution

### Snake
The classic: eat, grow, don't hit a wall or yourself. The snake speeds up as your score goes up.

- **Arrows / WASD**: move
- **IA : ON**: hand control to the AI. It follows a Hamiltonian cycle (a path through every cell, so it never traps itself) and only takes a shortcut toward the food after checking it can still reach its own tail. Pressing a key takes control back.

### Démineur (Minesweeper)
Three levels: Easy (9×9, 10 mines), Medium (16×16, 40), Hard (24×16, 75). The first click is always safe and opens an area.

- **Left click**: reveal a cell. On a number whose mines are all flagged: reveal all its other neighbours
- **Right click**: place or remove a flag
- **Indice**: the solver highlights a safe cell (green), a certain mine (red), or its best guess with the risk (orange)
- **IA : ON**: watch the solver play

The solver only sees what a player sees. It applies the basic rules plus subset reasoning between neighbouring numbers, and guesses the least risky cell when nothing is certain. Over a few hundred test games it won about 94% on Easy, 87% on Medium and 45% on Hard.

### Runner
An endless runner: the character runs on its own, faster and faster, through a procedurally generated world.

- **Space / Up / W / Z**: jump (hold for a higher jump)
- **Down / S**: duck (in the air: fall faster)
- **Esc**: pause

The world is split into **zones**. The first is 1 km long and each next one is 1.3× longer. Each zone unlocks a new threat:

| Zone | Starts at | New |
|---|---|---|
| 1 | 0 m | crates, pits, platforms |
| 2 | 1 000 m | drones |
| 3 | 2 300 m | slimes (stomp them for bonus points) and combos |
| 4 | 3 990 m | bobbing drones |
| 5 | 6 187 m | ceiling spikes (short hops only) |
| 6 | ~9 040 m | missiles, announced by a warning |
| 7+ | ~12 760 m | everything mixed |

Score = meters + 10 per coin + 50 per stomped slime.

The game logic is built for reinforcement learning: it doesn't depend on Pygame, runs at a fixed timestep (`step(action)` = 1/60 s), is reproducible from a seed, and humans and agents use the same three actions (nothing, jump, duck). The agent will live in `games/runner/ai/`.

## Getting started

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/YanisOuld/slo-games.git
cd slo-games
uv run python main.py
```

`uv` installs the dependencies (Pygame) on first run.

## Project structure

```
engine/            Shared engine, knows no specific game
  app.py           The single main loop; switching screen = switching scene
  scene.py         Scene base class (on_enter, handle_event, update, draw)
  widget.py        Reusable widgets: Label, Button
games/
  registry.py      Game catalogue: one line per game
  menu/            Main menu (game cards)
  binairo/
  snake/
    ai/            Hamiltonian-cycle agent
  minesweeper/
    ai/            Logic solver
  runner/
    ai/            Reinforcement learning agent (coming soon)
main.py            Entry point
```

Each game follows the same MVC layout:

| File | Role |
|---|---|
| `models.py` | Pure data types (no Pygame) |
| `game.py` | Game rules (no Pygame): testable and fast to run headless |
| `panels.py` | Views: they draw, never modify the game |
| `scene.py` | Controller: turns input into game actions; the only place that changes the model |
| `constants.py` | Layout, tuning and colors |
| `ai/` | Agents that read the game state and pick a move, just like a player |

### Adding a game
1. Create `games/<name>/` with a `Scene` subclass in `scene.py`.
2. Register it in [`games/registry.py`](games/registry.py).
3. Optionally, give it an icon, a color and a tagline in `_STYLES` in [`games/menu/cards.py`](games/menu/cards.py).
