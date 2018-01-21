import pygame
import game_functions as GF


class Tile:
    """
    This class stores information for each tile on the grid.
    """
    def __init__(self):
        self.init_rect = [0, 0, 0, 0]
        self.rect = None

        self.active = False
        self.selected = False
        self.unit = None

    def finalize_rect(self):
        self.rect = pygame.Rect(self.init_rect[0] + 8, self.init_rect[1] + 8, self.init_rect[2] - 16, self.init_rect[3] - 16)
        self.top_left_angle = GF.angle_between_two_vectors(self.rect.center, self.rect.topleft)
        self.top_right_angle = GF.angle_between_two_vectors(self.rect.center, self.rect.topright)
        self.bottom_left_angle = GF.angle_between_two_vectors(self.rect.center, self.rect.bottomleft)
        self.bottom_right_angle = GF.angle_between_two_vectors(self.rect.center, self.rect.bottomright)

    def render_id(self, screen):
        if self.unit is not None:
            idFont = pygame.font.SysFont(self.unit.name_font, self.unit.name_size, bold=True)
            txtSurface = idFont.render(self.unit.name, 0, self.unit.name_fg, self.unit.bg)
            screen.blit(txtSurface, (self.rect[0] - (self.unit.name_size / 2) + (self.rect[2] / 2), self.rect[1] - (self.unit.name_size / 2) + (self.rect[3] / 2)))

    def draw_self(self, screen):
        if self.unit is not None:
            pygame.draw.rect(screen, self.unit.bg, self.rect, 0)

    def draw_facing(self, screen):
        if self.unit is not None:
            points = self.get_facing_pointlist(self.unit.facing)
            pygame.draw.polygon(screen, (255, 255, 255), points)

    def draw_temp_facing(self, screen):
        if self.unit is not None:
            points = self.get_facing_pointlist(self.unit.tempfacing)
            pygame.draw.polygon(screen, (0, 204, 153), points)

    def get_facing_pointlist(self, facing):
        """For drawing the triangle of the facing"""
        points = []
        if facing == 'N':
            points.append((self.rect.centerx, self.rect.centery - int(self.rect.height / 2) + 2))
            points.append((self.rect.centerx - int(self.rect.width / 4), self.rect.centery - int(self.rect.height / 4)))
            points.append((self.rect.centerx + int(self.rect.width / 4), self.rect.centery - int(self.rect.height / 4)))
        elif facing == 'E':
            points.append((self.rect.centerx + int(self.rect.width / 2) - 2, self.rect.centery))
            points.append((self.rect.centerx + int(self.rect.width / 4), self.rect.centery - int(self.rect.height / 4)))
            points.append((self.rect.centerx + int(self.rect.width / 4), self.rect.centery + int(self.rect.height / 4)))
        elif facing == 'S':
            points.append((self.rect.centerx, self.rect.centery + int(self.rect.height / 2) - 2))
            points.append((self.rect.centerx - int(self.rect.width / 4), self.rect.centery + int(self.rect.height / 4)))
            points.append((self.rect.centerx + int(self.rect.width / 4), self.rect.centery + int(self.rect.height / 4)))
        elif facing == 'W':
            points.append((self.rect.centerx - int(self.rect.width / 2) + 2, self.rect.centery))
            points.append((self.rect.centerx - int(self.rect.width / 4), self.rect.centery - int(self.rect.height / 4)))
            points.append((self.rect.centerx - int(self.rect.width / 4), self.rect.centery + int(self.rect.height / 4)))
        return points

    def reset_bg(self):
        if self.unit is not None:
            self.unit.bg = self.unit.init_bg

    def is_unit_bg_default(self):
        """Returns True if unit.bg is the default, returns False if the unit.bg != unit.init_bg"""
        if self.unit is not None:
            if self.unit.init_bg == self.unit.bg:
                return True
            else:
                return False
        return True

    def change_unit_bg(self, color):
        if self.unit is not None:
            self.unit.bg = color
