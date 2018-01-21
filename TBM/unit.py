class Unit:
    """
    This class contains information for the unit on a tile
    """
    def __init__(self, name, team):
        self.name = name

        # visual elements
        self.name_font = 'Arial'
        self.name_size = 20
        self.name_fg = (0, 255, 0) if team == 1 else (255, 255, 255)
        self.init_bg = (37, 51, 206) if team == 1 else (206, 37, 76)
        self.bg = self.init_bg

        # movement properties
        self.move_left = 1
        self.move_right = 1
        self.move_forward = 2
        self.move_backward = 1
        # N, E, S, W
        self.facing = 'E' if team == 1 else 'W'
        self.tempfacing = self.facing

        # actions available
        self.can_move = True
        self.can_action = True
        self.can_rotate = True

        # team properties
        self.team = team

        # abilities
        self.abilities = ['Ability 1', 'Ability 2', 'Ability 3', 'Pass Turn']

    def update_actions(self, can_move=None, can_action=None, can_rotate=None):
        if can_move is not None:
            self.can_move = can_move
        if can_action is not None:
            self.can_action = can_action
        if can_rotate is not None:
            self.can_rotate = can_rotate
        if not self.can_action and not self.can_move and not self.can_rotate:
            self.name_fg = (225, 50, 100)



