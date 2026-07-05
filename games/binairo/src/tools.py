import pygame
from .schemas import PyGameAbstract, Statistics
from .constants import BOX_SIZE, GREY_RGB, OFFSET_TEXT_X, OFFSET_TEXT_Y

class Tools(PyGameAbstract):
    def __init__(self, size):
        self.size = size
        self.statistics: Statistics = None

    def draw(self, screen, font):
        for i in range(self.size):
            x = i * BOX_SIZE
            y = (self.size) * BOX_SIZE
            pygame.draw.rect(
                screen, GREY_RGB, (x, y, BOX_SIZE, BOX_SIZE)
            )
            raw_text = self.create_statistic_text("x", i)
            text = font.render(raw_text, True, (0, 0, 0))
            screen.blit(text, (x + OFFSET_TEXT_X,y + OFFSET_TEXT_Y))
        
        for j in range(self.size):
            x = (self.size) * BOX_SIZE
            y = j * BOX_SIZE
            pygame.draw.rect(
                screen, GREY_RGB, (x, y, BOX_SIZE, BOX_SIZE)
            )
            raw_text = self.create_statistic_text("y", j)
            text = font.render(raw_text, True, (0, 0, 0))
            screen.blit(text, (x + OFFSET_TEXT_X, y + OFFSET_TEXT_Y))
        
    def set_statistics(self, stats: Statistics):
        self.statistics = stats
    
    def create_statistic_text(self, types, position) -> str:
            white, black, _ = self.statistics[types][position]
            total_color = int(self.size / 2)
            return f"{total_color - white }/{ total_color - black }"