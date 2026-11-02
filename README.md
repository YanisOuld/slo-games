# SLO Games

A collection of puzzle and arcade games written in Python with [Pygame](https://www.pygame.org/), most of them paired with an AI: a Hamiltonian-cycle Snake solver, a logic Minesweeper solver, and an endless runner built to train a reinforcement learning agent, Connect Four against a minimax AI, a top-down racing game ready for learning drivers, Battleship against a probabilistic AI, and 8-ball pool.

> The in-game interface is in French.

## Games

| Game | Type | AI |
|---|---|---|
| **Binairo+** | Logic puzzle | – |
| **Snake** | Arcade | Hamiltonian-cycle solver with verified shortcuts |
| **Démineur** (Minesweeper) | Logic puzzle | Constraint solver with hints |
| **Runner** | Endless runner | Reinforcement learning (in progress) |
| **Puissance 4** (Connect Four) | Two-player duel | Minimax with alpha-beta pruning; self-play learning next |
| **Course** (Racing) | Time trial, 4 tracks | Learning drivers (in progress): sensors and continuous controls ready |
| **Bataille navale** (Battleship) | Duel vs AI | Random, hunt & target, and probability-density AIs, with a live heat map |
| **Billard** (8-ball pool) | Physics duel | Ghost-ball geometry; Hard replays its best shots in simulation |

### Binairo+
Fill a 20×20 grid with white and black cells. No more than two cells of the same color in a row, and every row and column holds as many whites as blacks. `=` and `x` hints between two cells tell you whether they are the same color or opposite colors.

- **Left click** a cell: cycle empty → light → blue (**right click**: the other way)
- Mistakes show up live in red: three in a row, a broken hint, a line with too many of one color
- Counters under and beside the grid show how many of each color each line still needs, and turn into a check mark once the line is valid
- A full grid is checked automatically (or press **Vérifier**)

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

### Puissance 4 (Connect Four)
Drop discs into a 7×6 grid; the first to line up four (horizontally, vertically or diagonally) wins. Play against the AI or against a friend on the same computer. The starting player alternates every game.

- **Click** a column (or press **1–7**): drop a disc
- **Mode**: vs IA / 2 joueurs
- **Niveau**: Easy, Medium, Hard (the AI looks 1, 3 or 6 moves ahead)
- **Annuler**: undo your last move (and the AI's reply)

The AI is a negamax search with alpha-beta pruning and a heuristic that scores open lines of 2 and 3 and control of the center column. It runs in a background thread so the falling-disc animation stays smooth. The game logic has cheap, exact `play()` / `undo()`, ready for learning agents (MCTS, self-play) that will be measured against this baseline.

### Course (Racing)
A top-down time trial: 3 laps on one of 4 tracks of increasing difficulty (Ovale, Serpent, Épingles, Grand Prix). The best lap of each track is kept, and its **ghost** races with you.

- **Arrows / ZQSD**: throttle, brake / reverse, steer
- **Space**: handbrake (the rear loses grip: drift!)
- **R**: restart
- **Capteurs**: show the car's distance sensors

The car model is arcade but physical: the velocity is split into a forward part (engine, brakes, drag) and a sideways part damped by tyre grip, so lowering grip makes the car slide. Laps are counted from forward progress along the track's centerline, so driving backwards or cutting can't count. Tracks are smooth closed splines checked so their walls never fold over themselves.

Built for learning drivers: the logic doesn't depend on Pygame, runs at a fixed timestep, controls are continuous (`throttle` and `steer` in -1..1), and `sensors()` returns 7 distance rays to the walls. The learning code will live in `games/racing/ai/`.

### Bataille navale (Battleship)
Place your fleet (5 ships), then take turns firing at the enemy's grid. Designed for a touchscreen: everything is a tap or a one-finger drag, no keyboard or right click.

- **Drag** a ship onto your grid; **tap** a placed ship to rotate it; **Aléatoire** places the fleet randomly
- **Tap** a cell of the enemy grid to fire
- **Niveau**: Easy (random shots), Medium (hunts on a checkerboard, then targets around hits), Hard (probability density)
- **Chaleur**: show the heat map: where a smart shooter thinks ships are, on both grids

The hard AI counts, for every ship still afloat, every position it could still occupy given the misses and sunk ships, weighting positions that explain existing hits much more. Each cell's count is its likelihood; the AI fires at the hottest cell. Over 200 games it sinks a fleet in 45 shots on average (Medium: 52, Easy: 96).

### Billard (8-ball pool)
American 8-ball against the AI or a friend: solids vs stripes, then the black. Touch-first controls:

- **Drag on the cloth**: aim (the guide shows where the cue ball hits and where the object ball goes)
- **Pull the power gauge down and let go**: shoot (let go near the top to cancel)
- **Ball in hand** (after a foul): drag the cue ball anywhere
- **Mode**: vs IA / 2 joueurs, **Niveau**: Easy / Medium / Hard, **Guide**: aiming guide on/off

Rules: the first legal pot assigns the groups; keep shooting while you pot your own balls; fouls (cue ball potted, nothing hit, wrong ball first) give ball in hand; pot the black after your group to win, too early and you lose.

Physics: equal-mass balls with elastic, slightly lossy collisions, cushions as segments between the pocket mouths (their ends act as jaws), table friction plus drag, small fixed substeps, and only moving balls are simulated.

AI: for every legal ball and pocket it computes the "ghost ball" spot, keeps shots whose paths are clear and cut angle playable, and scores them. Easy aims sloppily among the top shots, Medium plays the best one, Hard replays its best shots several times in a copy of the table with its own aiming error and picks the most reliable. In AI-vs-AI tests, Hard pots 67% of its aimed shots (Medium 42%, Easy 21%).

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
  sidebar.py       Side panel shared by the games
  theme.py         Shared color palette
games/
  registry.py      Game catalogue: one line per game
  menu/            Main menu (carousel of game cards)
  binairo/
  snake/
    ai/            Hamiltonian-cycle agent
  minesweeper/
    ai/            Logic solver
  runner/
    ai/            Reinforcement learning agent (coming soon)
  connect4/
    ai/            Minimax agent (learning agents next)
  racing/
    tracks.py      Track geometry (splines, walls)
    ai/            Learning drivers (coming soon)
  battleship/
    ai/            Random, hunt & target, probability agents + heat map
  billiards/
    physics.py     Ball / cushion / pocket physics
    ai/            Ghost-ball shot finder, simulation check on Hard
  icons.py         Game icons shared by the menu and the sidebars
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
