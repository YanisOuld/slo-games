import pygame

from game import Binairo, BOXES_PER_ROW

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
clock = pygame.time.Clock()
running = True

font = pygame.font.SysFont(None, 15)

game = Binairo(BOXES_PER_ROW)


while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            game.get_click(pos)
    
    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    # RENDER YOUR GAME HERE
    game.draw(screen=screen, font=font)

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
