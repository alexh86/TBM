# main.py
#
# This file will contain the main game loop
#
# Over-arcing functions include:
# -Initialize scene
# -Initialize game objects
# -Player input
# -AI processing
# -Update scene

import pygame
import os

# My imports
import game_functions as GF
from game_settings import Game_settings
from grid import Grid


def run_game():
    os.environ['SDL_VIDEO_WINDOW_POS'] = "{},{}".format(50, 50)
    pygame.init()

    # initialize game objects
    settings = Game_settings()
    screen = pygame.display.set_mode((settings.screenWidth, settings.screenHeight))
    grid = Grid(settings)

    pause_screen = GF.create_pause_screen(settings)

    pygame.display.set_caption('TBM')

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # draw list used to queue up draw events for udpate_screen()
    draw_list = []

    GF.spawn_units(grid)

    GF.init_screen(settings, screen, grid)
    while True:
        # check hardware events
        GF.check_events(grid, settings, draw_list)

        # animation events
        GF.check_custom_events(grid, settings, draw_list)

        # check mode, currently used for changing unit temp_facing
        GF.check_mode(grid, settings, draw_list)

        # update the screen
        GF.update_screen(settings, screen, grid, draw_list, clock, pause_screen)

        clock.tick(60)
        # print(clock.get_fps())

        draw_list = []
run_game()
