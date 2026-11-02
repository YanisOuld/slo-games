"""Catalogue of available games. Add a game = add a line here (+ write its Scene).

Values are factories (functions returning a fresh Scene), with imports inside to
avoid circular imports and load a game only when picked.
"""
from __future__ import annotations

from typing import Callable

from engine.scene import Scene


def _new_binairo() -> Scene:
    from games.binairo.scene import BinairoScene

    return BinairoScene()


def _new_snake() -> Scene:
    from games.snake.scene import SnakeScene

    return SnakeScene()


def _new_minesweeper() -> Scene:
    from games.minesweeper.scene import MinesweeperScene

    return MinesweeperScene()


def _new_runner() -> Scene:
    from games.runner.scene import RunnerScene

    return RunnerScene()


def _new_connect4() -> Scene:
    from games.connect4.scene import Connect4Scene

    return Connect4Scene()


def _new_racing() -> Scene:
    from games.racing.scene import RacingScene

    return RacingScene()


def _new_battleship() -> Scene:
    from games.battleship.scene import BattleshipScene

    return BattleshipScene()


def _new_billiards() -> Scene:
    from games.billiards.scene import BilliardsScene

    return BilliardsScene()


GAMES: dict[str, Callable[[], Scene]] = {
    "Binairo": _new_binairo,
    "Snake": _new_snake,
    "Démineur": _new_minesweeper,
    "Runner": _new_runner,
    "Puissance 4": _new_connect4,
    "Course": _new_racing,
    "Bataille navale": _new_battleship,
    "Billard": _new_billiards,
}
