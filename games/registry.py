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


GAMES: dict[str, Callable[[], Scene]] = {
    "Binairo": _new_binairo,
    "Snake": _new_snake,
    "Démineur": _new_minesweeper,
    "Runner": _new_runner,
}
