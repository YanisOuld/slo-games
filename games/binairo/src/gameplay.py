import pygame
import math
import random
from typing import List

from .schemas import BoxType, Coord, PyGameAbstract, Statistics
from .constants import BOXES_PER_ROW, BOX_SIZE

from .tools import Tools

class Box(PyGameAbstract):

    def __init__(self, x, y, height, width,  type: BoxType = BoxType.NONE):
        self.type: BoxType = type
        self.x: int = x
        self.y: int = y
        self.height: int = height
        self.width: int = width

    def draw(self, screen):
        pygame.draw.rect(
            screen, self.type.value, (self.x, self.y ,self.height, self.width)
        )
    
    def update_type(self):
        self.type = BoxType.next(self.type)

class Hint(PyGameAbstract):
    '''
    '''

    def draw():
        pass

type Grid = List[List[Box]]

class Gameplay(PyGameAbstract):

    def __init__(self, number_rows = BOXES_PER_ROW):
        self.number_rows = number_rows
        self.player_game: Grid = None
        self.answer: Grid = None
        self.tools: Tools = Tools(number_rows)
        
        self.answer = self.initialize()
        # TODO We need a logic to create a starting map from the answer ! We want to also create hints !
        self.player_game = self.answer
        self.tools.set_statistics(self.get_statistics())

    def initialize(self) -> Grid:
        grid = self._get_checkers_grid()
        max_permutations = self._get_number_permutations()
        count = 0
        while count < max_permutations:
            x, y = self._get_random_pos()
            if self._is_squared_checkers(grid, x, y):
                count+=1
                self._permute_box(grid, x, y, x, y -1)
                self._permute_box(grid, x - 1, y, x -1, y -1)
                if self._has_triplets(grid):
                    self._permute_box(grid, x, y, x, y -1)
                    self._permute_box(grid, x - 1, y, x -1, y -1)
                    count-=1
        
        return grid
    
    # Initialization tools 
    
    def _get_full_map(self, t = BoxType.NONE):
        return [[Box(i * BOX_SIZE, j * BOX_SIZE, BOX_SIZE, BOX_SIZE, t) for j in range(self.number_rows)] for i in range(self.number_rows)]
    
    def _get_checkers_grid(self):
        grid =  self._get_full_map()
        for i in range(self.number_rows):
            for j in range(self.number_rows):
                if (i + j) % 2 == 0:
                    grid[i][j].type = BoxType.WHITE
                else:
                    grid[i][j].type = BoxType.BLACK
        return grid
    
    # Gathering information tools from the game

    def verify(self) -> bool:
        for i in range(self.size):
            for j in range(self.size):
                if self.game[i][j].type != self.answer[i][j].type:
                    return False
        return True

    def get_statistics(self) -> Statistics:
        number_white = 0
        number_black = 0
        number_none = 0
        x = [[0,0,0] for _ in range(self.number_rows)]
        y = [[0,0,0] for _ in range(self.number_rows)]

        for i in range(self.number_rows):
            for j in range(self.number_rows):
                if self.player_game[i][j].type == BoxType.WHITE:
                    number_white+=1 
                    x[i][0]+= 1
                    y[j][0] += 1
                elif self.player_game[i][j].type == BoxType.BLACK:
                    number_black+=1 
                    x[i][1]+= 1
                    y[j][1] += 1
                elif self.player_game[i][j].type == BoxType.NONE:
                    number_none+=1 
                    x[i][2]+= 1
                    y[j][2] += 1 

        return {
            "number_white": number_white,
            "number_black": number_black,
            "number_none": number_none, 
            "x": x,
            "y": y,
        }
    
    def _has_triplets(self, grid) -> bool:
        for i in range(self.number_rows):
            for j in range(self.number_rows):
                center = BoxType.convert_to_int(grid[i][j].type)
                right_1 = BoxType.convert_to_int(grid[i+1][j].type) if self._is_inside(i+1, j) else 4
                right_2 = BoxType.convert_to_int(grid[i+2][j].type) if self._is_inside(i+2, j) else 4
                top_1 = BoxType.convert_to_int(grid[i][j+1].type) if self._is_inside(i, j+1) else 4
                top_2 = BoxType.convert_to_int(grid[i][j+2].type) if self._is_inside(i, j+2) else 4
                horizontal = center + right_1 + right_2
                vertical = center + top_1 + top_2
                if horizontal == 3 or horizontal == 0 or vertical == 3 or vertical == 0:
                    return True
        
        return False
    
    def _is_squared_checkers(self, checkers, x, y):
        return checkers[x][y].type == checkers[x -1][y -1].type and checkers[x - 1][y].type == checkers[x][y - 1].type and checkers[x][y].type != checkers[x][y -1].type

    def _is_inside(self, x, y):
        return x >= 0 and x < self.number_rows and y >= 0 and y < self.number_rows

    # Action tools

    def deal_click(self, pos):
        x, y = pos
        x, y = x // BOX_SIZE, y // BOX_SIZE
        self._update_box(x, y)

    def _get_random_pos(self) -> Coord:
        x = int(math.ceil(random.random() * (self.number_rows -1)))
        y = int(math.ceil(random.random() * (self.number_rows -1)))
        return x, y
    
    def _permute_box(self, checkers, x, y, w, z):
        checkers[x][y].type, checkers[w][z].type = checkers[w][z].type, checkers[x][y].type

    def _update_box(self, x, y):
        self.player_game[x][y].update_type()
        self.tools.set_statistics(self.get_statistics())
    
    def _get_number_permutations(self):
        return int(self.number_rows * 4)
    
    # Drawing 
    
    def draw(self, screen, font):
        for row in self.player_game:
            for box in row:
                box.draw(screen=screen)
        self.tools.draw(screen, font)