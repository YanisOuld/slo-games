import pygame
import math
import random
from typing import List
from dataclasses import dataclass

from .schemas import BoxType, Coord, HintDirection,  HintType, PyGameAbstract, Statistics
from .constants import ACTION_CHANCE, BOXES_PER_ROW, BOX_SIZE, HINT_CHANCE

from .tools import Tools

class Box(PyGameAbstract):

    def __init__(self, x, y, height, width,  type: BoxType = BoxType.NONE):
        self.type: BoxType = type
        self.x: int = x
        self.y: int = y
        self.height: int = height
        self.width: int = width

    def __eq__(self, other):
        return self.type == other.type

    def draw(self, screen):
        pygame.draw.rect(
            screen, self.type.value, (self.x, self.y ,self.height, self.width)
        )
        pygame.draw.rect(
            screen, "blue", (self.x, self.y ,self.height, self.width), 1
        )
    
    def update_type(self):
        self.type = BoxType.next(self.type)

@dataclass
class Hint(PyGameAbstract):
    coord1: Coord
    coord2: Coord
    t: HintType
    direction: HintDirection

    def draw(self, screen, font):
        '''
            How to draw a hint 
            - if it is horizontal we take the bigger x and we add one between the coord
            - if it is vertical we take the bigger y and we add one between the coord
            - the other is the middle 

        '''
        if HintDirection.is_horizontal(self.direction):
            x_px = int((max(self.coord1.x, self.coord2.x)) * BOX_SIZE) - 5
            y_px = int((self.coord1.y + 0.5) * BOX_SIZE) - 5
        else:
            x_px = int((self.coord1.x + 0.5) * BOX_SIZE) - 5
            y_px = int((max(self.coord1.y, self.coord2.y)) * BOX_SIZE) - 5

        text = font.render(self.t.value, True, "red")
        screen.blit(text, (x_px, y_px))

type Grid = List[List[Box]]

class Gameplay(PyGameAbstract):

    def __init__(self, number_rows = BOXES_PER_ROW):
        self.number_rows = number_rows
        self.player_game: Grid = None
        self.hints: List[Hint] =  []
        self.answer: Grid = None
        self.tools: Tools = Tools(number_rows)
        
        self.answer = self.initialize()
        self.player_game = self.generate_start_map(self.answer)
        self.tools.set_statistics(self.get_statistics())

    def initialize(self) -> Grid:
        grid = self._get_checkers_grid()
        max_permutations = self._get_number_permutations()
        tries = 0
        count = 0
        while count < max_permutations:
            x, y = self._get_random_pos()
            tries+=1
            if self._is_squared_checkers(grid, x, y):
                count+=1
                self._permute_box(grid, x, y, x, y -1)
                self._permute_box(grid, x - 1, y, x -1, y -1)
                if self._has_triplets(grid):
                    self._permute_box(grid, x, y, x, y -1)
                    self._permute_box(grid, x - 1, y, x -1, y -1)
                    count-=1
        print(f"The number of tries is {tries} and the number of permutation is {count} which give a percentage of false positive {(1 - (count / tries))* 100} %")
        return grid
    
    def generate_start_map(self, final_map: Grid) -> Grid:
        starting_grid = self._get_full_map()

        for i in range(len(final_map)):
            for j in range(len(final_map[i])):
                is_action = random.random() < ACTION_CHANCE
                if is_action:
                    starting_grid[i][j] = final_map[i][j]
                else:
                    is_hint = random.random() < HINT_CHANCE
                    if is_hint:
                        direction = HintDirection.choose_direction()
                        self.add_hints(Coord(i, j), direction)
        return starting_grid
            
    
    def add_hints(self, coord1: Coord, direction: HintDirection):
        coord2 = Coord(coord1.x + direction.value[0], coord1.y + direction.value[1])
        if not self._is_inside(coord2.x, coord2.y):
            direction = HintDirection.get_reversed_direction(direction)
            coord2 = Coord(coord1.x + direction.value[0], coord1.y + direction.value[1])
        
        t = HintType.INVERSE
        if self.answer[coord1.x][coord1.y] == self.answer[coord2.x][coord2.y]:
            t = HintType.EQUAL
        new_hint = Hint(coord1, coord2, t, direction)
        self.hints.append(new_hint)
        
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
        for i in range(self.number_rows):
            for j in range(self.number_rows):
                if self.player_game[i][j] != self.answer[i][j]:
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
    
    def _has_triplets(self, grid: Grid) -> bool:
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
    
    def _is_squared_checkers(self, grid: Grid, x, y):
        return grid[x][y] == grid[x -1][y -1] and grid[x - 1][y] == grid[x][y - 1] and grid[x][y] != grid[x][y -1]

    def _is_inside(self, x, y) -> bool:
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
        return int(self.number_rows ** 2)
    
    # Drawing 
    def draw(self, screen, font, font_hints):
        for row in self.player_game:
            for box in row:
                box.draw(screen=screen)
        for hint in self.hints:
            hint.draw(screen, font_hints)
        self.tools.draw(screen, font)