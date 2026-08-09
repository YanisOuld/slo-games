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


GAMES: dict[str, Callable[[], Scene]] = {
    "Binairo": _new_binairo,
}
