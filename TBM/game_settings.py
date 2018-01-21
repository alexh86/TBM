from pygame import Rect


class Game_settings:
    def __init__(self):
        # screen settings
        self.screenWidth = 1600
        self.screenHeight = 900

        self.bufferTop = 50
        self.bufferLeft = 50
        self.bufferRight = 50
        self.bufferBot = 100
        self.rows = 9
        self.columns = 16

        # buttons settings
        self.button_buffer = 5
        self.button_height = int((self.bufferBot / 2) - (self.button_buffer * 2))
        self.button_width = int(self.screenWidth / 14)

        # unit buttons
        self.unit_buttons = [Rect(self.screenWidth - self.bufferRight - self.button_width - self.button_buffer,
                                  self.screenHeight - self.bufferBot + self.button_buffer,
                                  self.button_width,
                                  self.button_height)]
        self.unit_buttons.append(Rect(self.unit_buttons[0][0],
                                      self.unit_buttons[0][1] + self.button_height + self.button_buffer,
                                      self.button_width,
                                      self.button_height))
        self.unit_buttons.append(Rect(self.unit_buttons[0][0] - self.button_width - self.button_buffer,
                                      self.unit_buttons[0][1],
                                      self.button_width,
                                      self.button_height))
        self.unit_buttons.append(Rect(self.unit_buttons[2][0],
                                      self.unit_buttons[1][1],
                                      self.button_width,
                                      self.button_height))
        # menu buttons
        self.menu_buttons = [Rect(self.bufferLeft + self.button_buffer,
                                  self.screenHeight - self.bufferBot + self.button_buffer,
                                  self.button_width,
                                  self.button_height)]
        self.menu_buttons.append(Rect(self.menu_buttons[0][0],
                                      self.menu_buttons[0][1] + self.button_height + self.button_buffer,
                                      self.button_width,
                                      self.button_height))
        self.menu_buttons.append(Rect(self.menu_buttons[0][0] + self.button_width + self.button_buffer,
                                      self.menu_buttons[0][1],
                                      self.button_width,
                                      self.button_height))
        self.menu_buttons.append(Rect(self.menu_buttons[2][0],
                                      self.menu_buttons[1][1],
                                      self.button_width,
                                      self.button_height))
        self.menu_button_options = ['Main Menu', 'Settings', 'Help', 'Exit']
        self.menu_font = 'Arial'
        self.menu_font_size = 20
        self.menu_font_fg = (255, 255, 255)

        # tile settings
        self.invalid_move_blink_time = 1
        self.move_hint_color = (56, 206, 37)

        # screen background color
        self.screenBG = (0, 0, 0)

        # fps display
        self.show_fps = True

        # current mode
        # change facing,
        self.cmode = ''

        # current team's turn
        self.cturn = 1

        # ai settings
        self.ai_turn_delay = 1

        # mouse position
        self.previous_mouse_pos = None

        # initialize dynamic settings
        self.initialize_settings()

    def initialize_settings(self):
        self.tileHeight = int((self.screenHeight - self.bufferTop - self.bufferBot) / self.rows)
        if self.tileHeight * self.rows < self.screenHeight:
            remainder = self.screenHeight - self.bufferTop - self.bufferBot - (self.tileHeight * self.rows)
            # add left over to the padding
            self.bufferTop += int(remainder / 2)
            self.bufferBot += remainder - int(remainder / 2)

        self.tileWidth = int((self.screenWidth - self.bufferLeft - self.bufferRight) / self.columns)
        if self.tileWidth * self.columns < self.screenWidth:
            remainder = self.screenWidth - self.bufferLeft - self.bufferRight - (self.tileWidth * self.columns)
            # add left over to the padding
            self.bufferLeft += int(remainder / 2)
            self.bufferRight += remainder - int(remainder / 2)
