from tile import Tile
import pygame


class Grid:
    """
    This class stores information about the tiles on the grid
    """
    def __init__(self, settings):
        self.settings = settings

        self.rect = pygame.Rect(self.settings.bufferLeft,
                                self.settings.bufferTop,
                                self.settings.screenWidth - self.settings.bufferLeft - self.settings.bufferRight + 1,
                                self.settings.screenHeight - self.settings.bufferBot - self.settings.bufferTop + 1)
        self.tiles = []
        self.selected_tile = None
        self.init_tiles()
        self.init_rect()

        # k = eventID, v = animation_event class
        self.timers = {}
        self.MAX_TIMERS = 100

        self.next_ai_action = None

    def init_tiles(self):
        for x in range(self.settings.columns):
            row = []
            for y in range(self.settings.rows):
                newTile = Tile()
                row.append(newTile)
            self.tiles.append(row)

    def init_rect(self):
        # horizontal lines
        for y in range(0, self.settings.rows + 1):
            yPos = self.settings.bufferTop + self.settings.tileHeight * y
            # save the y position of the tile
            for x in range(self.settings.columns):
                # want to skip the last iteration
                if y < self.settings.rows:
                    self.tiles[x][y].init_rect[1] = yPos
                # update height for previous tile
                if y > 0:
                    self.tiles[x][y-1].init_rect[3] = yPos - self.tiles[x][y-1].init_rect[1]

        # vertical lines
        for x in range(0, self.settings.columns + 1):
            xPos = self.settings.bufferLeft + self.settings.tileWidth * x
            # save the x position of the tile
            for y in range(self.settings.rows):
                # want to skip the last iteration
                if x < self.settings.columns:
                    self.tiles[x][y].init_rect[0] = xPos

                # update width for previous tile
                if x > 0:
                    self.tiles[x-1][y].init_rect[2] = xPos - self.tiles[x-1][y].init_rect[0]

        # finalize rect
        for x in range(self.settings.columns):
            for y in range(self.settings.rows):
                self.tiles[x][y].finalize_rect()

    def reset_team_action_status(self):
        """Reset current team's actions"""
        for x in range(len(self.tiles)):
            for y in range(len(self.tiles[x])):
                if self.tiles[x][y].active:
                    unit = self.tiles[x][y].unit
                    if unit is not None:
                        if unit.team == self.settings.cturn:
                            unit.name_fg = (0, 255, 0) if unit.team == 1 else (255, 255, 255)
                            unit.can_move = True
                            unit.can_action = True
                            unit.can_rotate = True




