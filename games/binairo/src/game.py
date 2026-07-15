from __future__ import annotations

'''
Creation of a Binairo game:

2. How to generate a final map 
3. How to generate a starting map
4. How to add hints
5. How to give points in the game

'''
from .gameplay import Gameplay
from .navigator import Navigator
from .schemas import PyGameAbstract

from .constants import BOXES_PER_ROW

class Binairo(PyGameAbstract):

    def __init__(self, size: int = BOXES_PER_ROW):
        self.game: Gameplay = Gameplay(size)
        self.navigator: Navigator = None
        self.size: int = size
        self.score: float = 0.0

    def draw(self, screen, font = None, font_hints = None):
        self.game.draw(screen, font, font_hints)

    def deal_click(self, pos):
        self.game.deal_click(pos)
        is_end = self.game.verify()
        print(f"Is the game ended {is_end}")