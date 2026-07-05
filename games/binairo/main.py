import pygame

from src.game import Binairo
from src.constants import FONT_SIZE, SCREEN_SIZE_X, SCREEN_SIZE_Y

pygame.init()
screen = pygame.display.set_mode((SCREEN_SIZE_X, SCREEN_SIZE_Y))
clock = pygame.time.Clock()
running = True

font = pygame.font.SysFont(None, FONT_SIZE)

binairo = Binairo()

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            binairo.deal_click(pos)
    
    screen.fill("black")

    binairo.draw(screen=screen, font=font)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
