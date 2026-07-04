from __future__ import annotations


'''
Creation of a Binairo game:

2. How to generate a final map 
3. How to generate a starting map
4. How to add hints
5. How to give points in the game

'''


from abc import ABC, abstractmethod
import pygame
from typing import List
from enum import Enum

BOX_SIZE=23
BOXES_PER_ROW=24

OFFSET_TEXT= 5

class PyGameAbstract(ABC):
    @abstractmethod
    def draw():
        pass


class BoxType(Enum):
    WHITE = (255,255,255)
    BLACK = (0,0,0)
    NONE = (180,180,180)

    def next(actual_type):
        types = list(BoxType)
        index = types.index(actual_type)
        next_index = (index + 1) % len(types)
        return types[next_index]

class Box(PyGameAbstract):
    ...  

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


class Grid(PyGameAbstract):
    '''
    
    '''
    def __init__(self, number_rows = BOXES_PER_ROW):
        self.number_rows = number_rows
        self.grid: List[List[Box]] = [[None for _ in range(number_rows)] for _ in range(number_rows)]

    def initialize(self, grid = None) -> None:
        '''
        TODO: We need to update the way to initialize a game
        '''
        if grid is not None:
            self.grid = grid
            return
        
        for i in range(self.number_rows):
            for j in range(self.number_rows):
                x = i * BOX_SIZE
                y = j * BOX_SIZE
                if (i + j) % 2 == 0:
                    self.grid[i][j] = Box(x, y, BOX_SIZE, BOX_SIZE, BoxType.WHITE)
                else:
                    self.grid[i][j] = Box(x, y, BOX_SIZE, BOX_SIZE, BoxType.NONE)
    
    def draw(self, screen):
        for row in self.grid:
            for box in row:
                box.draw(screen=screen)
    
    def get_grid(self):
        return self.grid

    def _update_box(self, x, y):
        self.grid[x][y].update_type()

    def convert_box(self, pos):
        x, y = pos
        x, y = x // BOX_SIZE, y // BOX_SIZE
        self._update_box(x, y)

    def _is_inside(self, x, y):
        return x >= 0 and x < self.number_rows and y >= 0 and y < self.number_rows

    def get_statistics(self):
        number_white = 0
        number_black = 0
        number_none = 0
        x = [[0,0,0] for _ in range(self.number_rows)]
        y = [[0,0,0] for _ in range(self.number_rows)]

        for i in range(self.number_rows):
            for j in range(self.number_rows):
                if self.grid[i][j].type == BoxType.WHITE:
                    number_white+=1 
                    x[i][0]+= 1
                    y[j][0] += 1
                elif self.grid[i][j].type == BoxType.BLACK:
                    number_black+=1 
                    x[i][1]+= 1
                    y[j][1] += 1
                elif self.grid[i][j].type == BoxType.NONE:
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

class Navigator(PyGameAbstract):
    ...


COLOR_TOOL = (250,249,246)


class Tools(PyGameAbstract):
    def __init__(self, size):
        self.size = size

        ...
    def draw(self, screen, font):
        for i in range(self.size):
            x = i * BOX_SIZE
            y = (self.size) * BOX_SIZE
            pygame.draw.rect(
                screen, COLOR_TOOL, (x, y, BOX_SIZE, BOX_SIZE)
            )
            raw_text = self.create_statistic_text()
            text = font.render(raw_text, True, (0, 0, 0))
            screen.blit(text, (x + OFFSET_TEXT,y + OFFSET_TEXT))
        
        for j in range(self.size):
            x = (self.size) * BOX_SIZE
            y = j * BOX_SIZE
            pygame.draw.rect(
                screen, COLOR_TOOL, (x, y, BOX_SIZE, BOX_SIZE)
            )

            text = font.render("1/1", True, (0, 0, 0))
            screen.blit(text, (x + OFFSET_TEXT, y + OFFSET_TEXT))
    
    def create_statistic_text(self, type, position) -> str:
        pass

class Binairo(PyGameAbstract):
    '''
    
    '''

    def __init__(self, size: int):
        self.game: Grid = Grid(size)
        self.answer: Grid = Grid(size)
        self.navigator: Navigator = None
        self.tools: Tools = Tools(size)
        self.size: int = size
        self.score: float = 0.0

        # creation of the final map
        self.answer.initialize()
        
        # transform the grid to make a start map
        answer_game = self.answer.get_grid()
        self.game.initialize(answer_game)

    def draw(self, screen, font = None):
        self.game.draw(screen)
        self.tools.draw(screen, font)

    def get_click(self, pos):
        self.game.convert_box(pos)

    def verify(self):
        stats = self.game.get_statistics()

        if stats["number_none"] != 0:
            ##raise ValueError("There are still empty box !")
            print("There are still empty box !")

        if stats["number_white"] != stats["number_black"]:
            ##raise ValueError("There should be an even amount of white and black box")
            print("There should be an even amount of white and black box")
    
    def _compare(self):
        pass
        


class Hint(PyGameAbstract):
    '''
    '''

    def draw():
        pass

class HintType(Enum):
    '''
    '''
    EQUAL = 1
    INVERSE = -1
