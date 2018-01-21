import pygame
import sys
import math
import time
import numpy as np
from unit import Unit
from animation_event import Animation_event


def check_events(grid, settings, draw_list):
    # listen for pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYUP:
            check_key_up(event, settings, draw_list, grid)
        elif event.type == pygame.MOUSEBUTTONDOWN and settings.cmode != 'paused':
            mouseX, mouseY = pygame.mouse.get_pos()
            check_mouse_down(mouseX, mouseY, grid, settings, event.button, draw_list)


def check_custom_events(grid, settings, draw_list):
    # TODO - what if i want to use this for something other than animations?
    remove_entries = []
    cTime = time.time()
    for event_id in grid.timers.keys():
        # is it time to update?
        if cTime >= grid.timers[event_id].last_update + grid.timers[event_id].interval:
            # do next animation frame
            tile = grid.timers[event_id].obj
            if tile is not None:
                if tile.is_unit_bg_default():
                    tile.change_unit_bg((255, 0, 0))
                else:
                    tile.reset_bg()
            print(time.strftime('%H:%M:%S') + ' - update event, at event_id = ' + str(event_id) + ' ts: ' + str(time.time()))
            # update last_update
            grid.timers[event_id].last_update = cTime

            # check if past end_time
            if cTime >= grid.timers[event_id].end_time:
                # kill the event: reset the tile color, remove grid.timers entry
                if tile is not None:
                    tile.reset_bg()
                print(time.strftime('%H:%M:%S') + ' - kill event, at event_id = ' + str(event_id) + ' ts: ' + str(time.time()))
                remove_entries.append(event_id)

            # add frame to draw list
            draw_list.append({'draw tile': tile})
            if grid.selected_tile == tile:
                draw_list.append({'draw select': tile})
    for rem_entry in remove_entries:
        del grid.timers[rem_entry]


def check_mode(grid, settings, draw_list):
    if settings.cmode == 'change facing':
        if grid.selected_tile is not None:
            if grid.selected_tile.unit is not None:
                current_mouse_pos = pygame.mouse.get_pos()
                if current_mouse_pos != settings.previous_mouse_pos:
                    # this will check only when mouse moves
                    newfacing = get_temp_facing(grid.selected_tile)
                    if newfacing != grid.selected_tile.unit.tempfacing:
                        grid.selected_tile.unit.tempfacing = newfacing
                        draw_list.append({'update temp facing': grid.selected_tile})
    elif settings.cmode == 'ai turn':
        # Do AI things, takes an action for one unit at a time
        if time.time() >= grid.next_ai_action:
            move_ai_unit(grid, settings, draw_list)
            check_turn_change(grid, settings, draw_list)


def move_ai_unit(grid, settings, draw_list):
    # TODO - right now the order in which units are selected to be moved are completely sequential,
    #        eventually this will cause units that are high in the list and blocked by other units to not be able
    #        to move.  This can be solved by moving the units on the outside first.
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            tile = grid.tiles[x][y]
            unit = grid.tiles[x][y].unit
            if unit is not None:
                if unit.team == settings.cturn and unit.can_move:
                    # TODO - if can_move = True but no viable move can be found: pass turn
                    # found AI unit that can move
                    # select unit
                    select_tile(tile, grid, draw_list)

                    # move unit
                    # check for viable move, continue if none found
                    directions = find_viable_moves(grid, tile)  # directions = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
                    print('Directions unit can move = ' + str(directions))

                    closest_enemy = find_closest_enemy_unit(grid, tile)
                    print('Closest enemy unit = (' + str(closest_enemy[0]) + ', ' + str(closest_enemy[1]) + ')')

                    # pass turn
                    pass_turn(tile, draw_list, grid, settings)
                    # set time for next ai turn
                    grid.next_ai_action = time.time() + settings.ai_turn_delay
                    return
    # This will happen if no unit available for moving is found
    grid.next_ai_action = None


def find_viable_moves(grid, tile):
    """Returns a dictionary of headings and number of spaces the unit can move that aren't obstructed"""
    directions = {'N': 0, 'E': 0, 'S': 0, 'W': 0}
    # gets the number of spaces tile.unit can move in each direction
    if tile is not None:
        if tile.unit is not None:
            k = list(directions.keys())
            s = k.index(tile.unit.facing)  # 0->3
            for i in range(1, len(k) + 1):  # 1->4
                if s + i >= len(k):
                    ki = (s + i) - len(k)
                else:
                    ki = s + i
                # the order here matters, assigns: right, back, left, forward after it finds forward facing
                directions[k[ki]] = [tile.unit.move_right, tile.unit.move_backward, tile.unit.move_left, tile.unit.move_forward][i - 1]
    # check to see if unit is able to move the numnber of spaces available in each direction
    # modify directions to reflect how many spaces unit can move in each direction, ie: set directions['N'] = 0 if unable to move North
    tile_x, tile_y = get_tile_position(grid, tile)
    for heading in directions.keys():  # N, E, S, W
        num_moves = directions[heading]
        for i in range(num_moves):  # 0 -> number of moves
            # num_moves - i = directions[heading] -> 0
            dest_x, dest_y = get_destination_xy_from_heading(grid, tile_x, tile_y, num_moves - i, heading)
            if is_move_blocked(grid, tile_x, tile_y, dest_x, dest_y):
                # subtract 1 and try again
                directions[heading] = directions[heading] - 1
            else:
                # can move
                break

    return directions


def get_destination_xy_from_heading(grid, tile_x, tile_y, moves, heading):
    """:returns: x, y coordinates based on the heading and number of moves"""
    x, y = (tile_x, tile_y)
    if heading == 'N':
        if y - moves >= 0:
            y = y - moves
    elif heading == 'E':
        if x + moves <= len(grid.tiles):
            x = x + moves
    elif heading == 'S':
        if y + moves <= len(grid.tiles[x]):
            y = y + moves
    elif heading == 'W':
        if x - moves >= 0:
            x = x - moves
    return x, y


def find_closest_enemy_unit(grid, start_tile):
    # TODO - doesn't factor in current rotation and move speeds
    closest_unit_pos = None
    my_unit_pos = get_tile_position(grid, start_tile)
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            tile = grid.tiles[x][y]
            unit = tile.unit
            if unit is not None:
                if unit.team != start_tile.unit.team:
                    # check distance
                    d = math.sqrt((x - my_unit_pos[0])**2 + (y - my_unit_pos[1])**2)
                    if closest_unit_pos is not None:
                        if math.sqrt((closest_unit_pos[0] - my_unit_pos[0]) ** 2 + (closest_unit_pos[1] - my_unit_pos[1]) ** 2) > d:
                            # new closest
                            closest_unit_pos = (x, y)
                    else:
                        closest_unit_pos = (x, y)
    return closest_unit_pos


def check_key_up(event, settings, draw_list, grid):
    # check KEYUP events
    if event.key == pygame.K_ESCAPE:
        if settings.cmode == 'paused':
            settings.cmode = ''
            draw_list.append({'draw all': 0})
        else:
            sys.exit()
    elif event.key == pygame.K_f:
        settings.show_fps = not settings.show_fps
        draw_list.append({'clear fps': 0})
    elif event.key == pygame.K_r and settings.cmode != 'paused':
        if settings.cmode == '':
            if grid.selected_tile is not None:
                if grid.selected_tile.unit is not None:
                    # TODO - change when AI is implemented
                    if grid.selected_tile.unit.team == settings.cturn and grid.selected_tile.unit.can_rotate:
                        cancel_tile_animation(grid, grid.selected_tile, draw_list)
                        settings.cmode = 'change facing'
                        settings.previous_mouse_pos = pygame.mouse.get_pos()
                        grid.selected_tile.unit.tempfacing = get_temp_facing(grid.selected_tile)
                        draw_list.append({'draw temp facing': grid.selected_tile})
                    else:
                        blink_selected_tile(grid, settings)
        elif settings.cmode == 'change facing':
            settings.cmode = ''
            if grid.selected_tile is not None:
                if grid.selected_tile.unit is not None:
                    # cancel change facing
                    grid.selected_tile.unit.tempfacing = ''
                    draw_list.append({'clear temp facing': grid.selected_tile})
    elif event.key == pygame.K_SPACE and settings.cmode != 'paused':
        if grid.selected_tile is not None:
            if grid.selected_tile.unit is not None:
                if grid.selected_tile.unit.team == settings.cturn:
                    # pass turn
                    pass_turn(grid.selected_tile, draw_list, grid, settings)
                else:
                    blink_selected_tile(grid, settings)


def get_temp_facing(tile):
    mouse_pos = pygame.mouse.get_pos()
    mouse_angle = angle_between_two_vectors(tile.rect.center, mouse_pos)
    # print('mouse angle = ' + str(mouse_angle))
    if tile.top_right_angle <= mouse_angle <= tile.top_left_angle:
        return 'N'
    elif tile.top_left_angle < mouse_angle <= tile.bottom_left_angle:
        return 'W'
    elif tile.bottom_left_angle < mouse_angle <= tile.bottom_right_angle:
        return 'S'
    else:
        return 'E'


def check_mouse_down(mouseX, mouseY, grid, settings, button, draw_list):
    """handles the MOUSEDOWN event"""
    if settings.cmode == '':
        if grid.rect.collidepoint(mouseX, mouseY):
            # click was in the grid
            if button == 1:
                left_click_in_grid(grid, mouseX, mouseY, draw_list)
            elif button == 3:
                right_click_in_grid(grid, settings, mouseX, mouseY, draw_list)
        else:
            # click was not in the grid
            if button == 1:
                left_click_out_of_grid(mouseX, mouseY, draw_list, grid, settings)
    elif settings.cmode == 'change facing':
        if button == 1:
            # click to confirm change facing
            left_click_change_facing(grid, settings, draw_list)


def left_click_change_facing(grid, settings, draw_list):
    if grid.selected_tile is not None:
        if grid.selected_tile.unit is not None:
            if grid.selected_tile.unit.tempfacing != grid.selected_tile.unit.facing:
                oldfacing = grid.selected_tile.unit.facing
                grid.selected_tile.unit.facing = grid.selected_tile.unit.tempfacing
                grid.selected_tile.unit.tempfacing = ''
                draw_list.append({'clear temp facing': grid.selected_tile})
                settings.cmode = ''
                # After changing facing need to clear/redraw move hints
                draw_list.append({'update move hints': {'tile': grid.selected_tile, 'oldfacing': oldfacing}})
            else:
                draw_list.append({'clear temp facing': grid.selected_tile})
                settings.cmode = ''
            grid.selected_tile.unit.update_actions(can_rotate=False)
            check_turn_change(grid, settings, draw_list)


def left_click_out_of_grid(mouseX, mouseY, draw_list, grid, settings):
    """checks for clicks on buttons outside of the grid"""
    # check unit buttons
    if grid.selected_tile is not None:
        if grid.selected_tile.unit is not None:
            # TODO - change when AI is implemented
            if grid.selected_tile.unit.team == settings.cturn:
                for i in range(min(len(grid.selected_tile.unit.abilities), len(settings.unit_buttons))):
                    if settings.unit_buttons[i].collidepoint(mouseX, mouseY):
                        print('\'' + grid.selected_tile.unit.name + '\' ability button clicked, \'' + grid.selected_tile.unit.abilities[i] + '\'')
                        if i == 0:
                            # unit ability 1
                            grid.selected_tile.unit.update_actions(can_action=False)
                            # using clear temp facing because it does exactly what is needed, should probably rename
                            draw_list.append({'clear temp facing': grid.selected_tile})
                            check_turn_change(grid, settings, draw_list)
                        elif i == 1:
                            # unit ability 2
                            grid.selected_tile.unit.update_actions(can_action=False)
                            # using clear temp facing because it does exactly what is needed, should probably rename
                            draw_list.append({'clear temp facing': grid.selected_tile})
                            check_turn_change(grid, settings, draw_list)
                        elif i == 2:
                            # unit ability 3
                            grid.selected_tile.unit.update_actions(can_action=False)
                            # using clear temp facing because it does exactly what is needed, should probably rename
                            draw_list.append({'clear temp facing': grid.selected_tile})
                            check_turn_change(grid, settings, draw_list)
                        if i == 3:
                            # unit ability 4
                            pass_turn(grid.selected_tile, draw_list, grid, settings)
                        return

    # check in-game menu buttons
    for i in range(min(len(settings.menu_buttons), len(settings.menu_button_options))):
        if settings.menu_buttons[i].collidepoint(mouseX, mouseY):
            print('\'' + settings.menu_button_options[i] + '\' button clicked')
            if i == 3:
                sys.exit()
            elif i == 2:
                settings.cmode = 'paused'
                # TODO - need to cancel more than just the selected_tiles animations
                cancel_tile_animation(grid, grid.selected_tile, draw_list)
                draw_list.append({'draw pause screen': 0})
            return


def pass_turn(tile, draw_list, grid, settings):
    if tile is not None:
        if tile.unit is not None:
            # pass turn
            tile.unit.update_actions(can_rotate=False, can_action=False, can_move=False)
            # using clear temp facing because it does exactly what is needed, should probably rename
            draw_list.append({'pass turn': tile})
            check_turn_change(grid, settings, draw_list)


def right_click_in_grid(grid, settings, mouseX, mouseY, draw_list):
    """Handles right click in grid"""
    if grid.selected_tile is not None:
        if grid.selected_tile.unit is not None:
            # TODO - change when AI is implemented
            if grid.selected_tile.unit.team == settings.cturn:
                # something is selected
                # loop through all tiles and find the one that was clicked on
                for x in range(len(grid.tiles)):
                    for y in range(len(grid.tiles[x])):
                        if grid.tiles[x][y].rect.collidepoint(mouseX, mouseY):
                            clickedTile = grid.tiles[x][y]
                            if not is_valid_move(grid, x, y):
                                # invalid move
                                blink_selected_tile(grid, settings)
                            elif clickedTile.active:
                                # unit already on clicked tile
                                # TODO - this is where logic for unit interaction will go, ie: attacking.  Will also need range check
                                blink_selected_tile(grid, settings)
                            else:
                                # check if the unit can move
                                if grid.selected_tile.unit.can_move:
                                    # move unit
                                    # check event list to see if the selected_tile has an animation in progress
                                    cancel_tile_animation(grid, grid.selected_tile, draw_list)

                                    draw_list.append({'prep move': {'tile': grid.selected_tile, 'unit': grid.selected_tile.unit}})
                                    # set the clicked tile to the selected_tile's unit
                                    clickedTile.unit = grid.selected_tile.unit
                                    clickedTile.active = True
                                    clickedTile.selected = True
                                    # clear previous tile's unit
                                    grid.selected_tile.unit = None
                                    grid.selected_tile.active = False
                                    grid.selected_tile.selected = False
                                    grid.selected_tile = clickedTile

                                    grid.selected_tile.unit.update_actions(can_move=False)

                                    draw_list.append({'finalize move': grid.selected_tile})

                                    check_turn_change(grid, settings, draw_list)
                                else:
                                    # unit cannot move
                                    blink_selected_tile(grid, settings)
                            # WARNING - This function returns once this point is reached
                            return
                # mouse click did not happen on a tile, probably clicked on a dividing line.
                # This will only execute if the previous code did not return
                # invalid move
                blink_selected_tile(grid, settings)
            else:
                # tile selected is not on current turn's team
                blink_selected_tile(grid, settings)
    else:
        # nothing is selected
        pass


def cancel_tile_animation(grid, tile, draw_list):
    # check event list to see if the selected_tile has an animation in progress
    inlist = check_timers_for_tile(grid, tile)
    if inlist is not None:
        grid.timers[inlist].obj.reset_bg()
        # queue redraw up
        draw_list.append({'draw tile': tile})
        # check to see if tile was selected
        if grid.selected_tile == tile:
            draw_list.append({'draw select': tile})

        # remove the event from grid.timers
        del grid.timers[inlist]
        print(time.strftime('%H:%M:%S') + ' - Deleted event, event_id = ' + str(inlist))


def blink_selected_tile(grid, settings):
    """Checks grid.timers to see if selected tile has an event in the list
        If True: refreshes the existing event's start_time.
        Else: creates a new event."""
    # check event list to see if the selected_tile already has an animation in progress
    inlist = check_timers_for_tile(grid, grid.selected_tile)
    if inlist is not None:
        # refresh the end time of the animation
        grid.timers[inlist].end_time = time.time() + settings.invalid_move_blink_time
        print(time.strftime('%H:%M:%S') + ' - Refreshed event, event_id = ' + str(inlist))
    else:
        # Create new animation event
        new_event_id = 0
        while new_event_id < grid.MAX_TIMERS:
            if new_event_id not in grid.timers.keys():
                break
            new_event_id += 1
        # TODO - can add a new entry in the class for different types of events.
        grid.timers[new_event_id] = Animation_event(new_event_id, grid.selected_tile, 0.1, time.time() + settings.invalid_move_blink_time)
        print(time.strftime('%H:%M:%S') + ' - New event, created at event_id = ' + str(new_event_id) + ' ts: ' + str(time.time()))


def check_timers_for_tile(grid, tile):
    """Returns eventID if selected_tile is in grid.timer list"""
    if tile is not None:
        for k, v in grid.timers.items():
            if v.obj == tile:
                return k
    return None


def left_click_in_grid(grid, mouseX, mouseY, draw_list):
    """Handles left click on grid"""
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            # check if mouse click on tile
            # This checks every tile for collision, expensive?
            if grid.tiles[x][y].rect.collidepoint(mouseX, mouseY):
                clicked_tile = grid.tiles[x][y]
                if clicked_tile.active:
                    # no need to select the tile if it is already selected
                    if clicked_tile is not grid.selected_tile:
                        select_tile(clicked_tile, grid, draw_list)
                    if clicked_tile.unit is not None:
                        print('can_rotate: ' + str(clicked_tile.unit.can_rotate) + ' can_move: ' + str(clicked_tile.unit.can_move) + ' can_action: ' + str(clicked_tile.unit.can_action))
                else:
                    deselect_tile(grid, draw_list)
                return
    # mouse1 did not click on any tile, probably clicked on a dividing line.
    # This will only execute if the previous code did not return
    deselect_tile(grid, draw_list)


def angle_between_two_vectors(origin, point):
    p1 = [0, 0]  # origin
    p2 = [point[0] - origin[0], point[1] - origin[1]]
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    return np.rad2deg((ang1 - ang2) % (2 * np.pi))


def is_valid_move(grid, destination_x, destination_y):
    """Checks if grid.selected_tile can move to x, y
        This function only checks against x and y coords
        :returns: False - if invalid; True - if valid"""
    if grid.selected_tile:
        current_x, current_y = get_tile_position(grid, grid.selected_tile)
        # This check is to make sure we aren't moving diagonally
        if current_x == destination_x or current_y == destination_y:
            if not is_move_blocked(grid, current_x, current_y, destination_x, destination_y):
                unit = grid.selected_tile.unit

                north_moves, east_moves, south_moves, west_moves = get_unit_directional_moves(unit)
                if north_moves is None or east_moves is None or south_moves is None or west_moves is None:
                    return False

                if destination_x <= current_x + east_moves:
                    if destination_x >= current_x - west_moves:
                        if destination_y >= current_y - north_moves:
                            if destination_y <= current_y + south_moves:
                                return True
    return False


def is_move_blocked(grid, startX, startY, destX, destY):
    """Checks the path between (startX, startY) and (destX, destY) to make sure no tile is active
    :returns: True if move is blocked
    :returns: False if move is unimpeded"""
    moveX = destX - startX
    moveY = destY - startY
    if abs(moveX) > 0:
        stepX = int(moveX / abs(moveX))
        for x in range(startX + stepX, destX + stepX, stepX):
            if x < 0 or x > len(grid.tiles) - 1:
                return True
            if grid.tiles[x][startY].active:
                return True
        return False
    elif abs(moveY) > 0:
        stepY = int(moveY / abs(moveY))
        for y in range(startY + stepY, destY + stepY, stepY):
            if y < 0 or y > len(grid.tiles[startX]) - 1:
                return True
            if grid.tiles[startX][y].active:
                return True
        return False
    return True


def deselect_tile(grid, draw_list):
    if grid.selected_tile:
        # clear the tile, movement hints, and unit buttons
        # redraw tile
        draw_list.append({'deselect tile': {'tile': grid.selected_tile, 'unit': grid.selected_tile.unit}})
        grid.selected_tile.selected = False
        grid.selected_tile = None


def select_tile(tile, grid, draw_list):
    # de-select other tile if it exists
    deselect_tile(grid, draw_list)

    # select tile
    tile.selected = True
    grid.selected_tile = tile

    draw_list.append({'draw tile': grid.selected_tile})  # TODO - bandaid for drawing move hints
    # draw the selection box, movement hints, and unit buttons
    draw_list.append({'select tile': grid.selected_tile})


def init_screen(settings, screen, grid):
    """draw the initial screen"""
    screen.fill(settings.screenBG)
    draw_grid(settings, screen, grid)
    draw_tiles(settings, screen, grid)
    draw_menu_buttons(settings, screen)
    draw_turn_text(screen, settings)


def update_screen(settings, screen, grid, draw_list, clock, pause_screen):
    """Goes through each entry in the draw_list and performs the appropriate draw action"""

    if settings.show_fps:
        draw_fps(screen, settings, clock)

    for entry in draw_list:
        for k, v in entry.items():
            if v is not None:
                # Note: v.unit may be = None
                if k == 'select tile':
                    draw_selection_box(screen, v.rect)
                    draw_move_hints(grid, screen, v, settings)
                    draw_unit_buttons(v, screen, settings)
                elif k == 'deselect tile':
                    # v = {'tile': tile, 'unit': unit}
                    tile = v['tile']
                    unit = v['unit']
                    # clear tile
                    clear_tile(screen, tile, settings)
                    # clear unit move hints
                    clear_move_hints(grid, screen, tile, unit, settings)
                    # clear unit buttons
                    clear_unit_buttons(screen, settings)
                    # re-draw tile
                    draw_tile(screen, tile)
                elif k == 'pass turn':
                    # clear unit move hints
                    clear_move_hints(grid, screen, v, v.unit, settings)
                    draw_tile(screen, v)
                    draw_selection_box(screen, v.rect)
                elif k == 'prep move':
                    # v = {'tile': tile, 'unit': unit}
                    tile = v['tile']
                    unit = v['unit']
                    # clear tile
                    clear_tile(screen, tile, settings)
                    # clear unit move hints
                    clear_move_hints(grid, screen, tile, unit, settings)
                elif k == 'finalize move':
                    draw_tile(screen, v)
                    draw_selection_box(screen, v.rect)
                    draw_move_hints(grid, screen, v, settings)
                    # draw_unit_buttons(v, screen, settings)
                elif k == 'clear tile':
                    clear_tile(screen, v, settings)
                elif k == 'draw tile':
                    draw_tile(screen, v)
                elif k == 'draw select':
                    draw_selection_box(screen, v.rect)
                elif k == 'clear fps':
                    clear_fps(screen, settings)
                elif k == 'draw temp facing':
                    draw_temp_facing(screen, v)
                elif k == 'update temp facing':
                    # clear_tile(screen, v, settings)
                    draw_tile(screen, v)
                    draw_selection_box(screen, v.rect)
                    draw_temp_facing(screen, v)
                elif k == 'clear temp facing':
                    draw_tile(screen, v)
                    draw_selection_box(screen, v.rect)
                elif k == 'update move hints':
                    # v = {'tile': tile, 'oldfacing': facing}
                    tile = v['tile']
                    oldfacing = v['oldfacing']
                    clear_old_facing_move_hints(grid, screen, tile, oldfacing, settings)
                    draw_move_hints(grid, screen, tile, settings)
                elif k == 'draw pause screen':
                    draw_pause_screen(pause_screen, screen, settings)
                elif k == 'draw all':
                    redraw_screen(grid, screen, settings)
                elif k == 'draw turn text':
                    draw_turn_text(screen, settings)
                elif k == 'clear turn text':
                    clear_turn_text(screen, settings)

    pygame.display.flip()


def redraw_screen(grid, screen, settings):
    print('re-draw screen')
    init_screen(settings, screen, grid)
    if grid.selected_tile is not None:
        draw_selection_box(screen, grid.selected_tile.rect)
        draw_move_hints(grid, screen, grid.selected_tile, settings)
        draw_unit_buttons(grid.selected_tile, screen, settings)


def draw_pause_screen(pause_screen, screen, settings):
    print('draw pause screen')
    screen.blit(pause_screen, (5, 5))
    idFont = pygame.font.SysFont(settings.menu_font, 50, bold=True)
    txtSurface = idFont.render('Paused', 0, settings.menu_font_fg)
    screen.blit(txtSurface, (pause_screen.get_rect().centerx - txtSurface.get_rect().width / 2,
                             pause_screen.get_rect().centery - txtSurface.get_rect().height / 2))


def draw_temp_facing(screen, tile):
    tile.draw_temp_facing(screen)


def draw_menu_buttons(settings, screen):
    for i in range(min(len(settings.menu_buttons), len(settings.menu_button_options))):
        button_rect = settings.menu_buttons[i]
        s = pygame.Surface((button_rect.width, button_rect.height))
        s.set_alpha(255)
        s.fill((0, 0, 255))

        idFont = pygame.font.SysFont(settings.menu_font, settings.menu_font_size, bold=False)
        txtSurface = idFont.render(settings.menu_button_options[i], 0, settings.menu_font_fg, (0, 0, 255))
        s.blit(txtSurface, (s.get_rect().centerx - txtSurface.get_rect().width / 2,
                            s.get_rect().centery - txtSurface.get_rect().height / 2))

        screen.blit(s, (button_rect.x, button_rect.y))


def draw_fps(screen, settings, clock):
    s = pygame.Surface((50, 30))
    s.set_alpha(128)
    s.fill(settings.screenBG)
    fpsTxt = str(round(clock.get_fps(), 2))
    fpsFont = pygame.font.SysFont('Arial', 20, bold=False)
    txtSurface = fpsFont.render(fpsTxt, 0, (0, 255, 0), settings.screenBG)
    s.blit(txtSurface, (0, 0))
    screen.blit(s, (0, 0))


def clear_fps(screen, settings):
    s = pygame.Surface((50, 30))
    s.fill(settings.screenBG)
    screen.blit(s, (0, 0))


def draw_turn_text(screen, settings):
    s = pygame.Surface((200, 50))
    s.fill(settings.screenBG)
    turnTxt = 'Team ' + str(settings.cturn) + '\'s Turn'
    turnFont = pygame.font.SysFont('Arial', 30, bold=True)
    color = (0, 255, 0) if settings.cturn == 1 else (255, 0, 0)
    txtSurface = turnFont.render(turnTxt, 0, color, settings.screenBG)
    s.blit(txtSurface, (int((s.get_rect().width - txtSurface.get_rect().width)/2), int((s.get_rect().height - txtSurface.get_rect().height)/2)))
    screen.blit(s, (int(settings.screenWidth/2) - int(s.get_rect().width/2),
                    int(settings.screenHeight - int(s.get_rect().height * 1.5))))


def clear_turn_text(screen, settings):
    s = pygame.Surface((200, 50))
    s.fill(settings.screenBG)
    screen.blit(s, (int(settings.screenWidth / 2) - int(s.get_rect().width / 2),
                    int(settings.screenHeight - int(s.get_rect().height * 1.5))))


def draw_unit_buttons(tile, screen, settings):
    if tile.unit is not None:
        for i in range(min(len(tile.unit.abilities), len(settings.unit_buttons))):
            button_rect = settings.unit_buttons[i]
            s = pygame.Surface((button_rect.width, button_rect.height))
            s.set_alpha(255)
            s.fill((0, 0, 255))

            idFont = pygame.font.SysFont(tile.unit.name_font, tile.unit.name_size, bold=False)
            # txtSurface = idFont.render(tile.unit.name + ' ' + tile.unit.abilities[i], 0, tile.unit.name_fg, (0, 0, 255))
            txtSurface = idFont.render(tile.unit.abilities[i], 0, tile.unit.name_fg, (0, 0, 255))
            s.blit(txtSurface, (s.get_rect().centerx - txtSurface.get_rect().width/2, s.get_rect().centery - txtSurface.get_rect().height/2))

            screen.blit(s, (button_rect.x, button_rect.y))


def clear_unit_buttons(screen, settings):
    for i in range(len(settings.unit_buttons)):
        button_rect = settings.unit_buttons[i]
        s = pygame.Surface((button_rect.width, button_rect.height))
        s.fill((0, 0, 0))
        screen.blit(s, (button_rect.x, button_rect.y))


def get_unit_directional_moves(unit):
    """Returns units directional movements in a list (N,E,S,W)"""
    if unit is not None:
        if unit.facing == 'N':
            west_moves = unit.move_left
            east_moves = unit.move_right
            north_moves = unit.move_forward
            south_moves = unit.move_backward
        elif unit.facing == 'E':
            west_moves = unit.move_backward
            east_moves = unit.move_forward
            north_moves = unit.move_left
            south_moves = unit.move_right
        elif unit.facing == 'S':
            west_moves = unit.move_right
            east_moves = unit.move_left
            north_moves = unit.move_backward
            south_moves = unit.move_forward
        elif unit.facing == 'W':
            west_moves = unit.move_forward
            east_moves = unit.move_backward
            north_moves = unit.move_right
            south_moves = unit.move_left
        else:
            return None
        return north_moves, east_moves, south_moves, west_moves
    return None


def get_old_facing_directional_moves(unit, facing):
    """Returns units directional movements in a list (N,E,S,W)"""
    if unit is not None:
        if facing == 'N':
            west_moves = unit.move_left
            east_moves = unit.move_right
            north_moves = unit.move_forward
            south_moves = unit.move_backward
        elif facing == 'E':
            west_moves = unit.move_backward
            east_moves = unit.move_forward
            north_moves = unit.move_left
            south_moves = unit.move_right
        elif facing == 'S':
            west_moves = unit.move_right
            east_moves = unit.move_left
            north_moves = unit.move_backward
            south_moves = unit.move_forward
        elif facing == 'W':
            west_moves = unit.move_forward
            east_moves = unit.move_backward
            north_moves = unit.move_right
            south_moves = unit.move_left
        else:
            return None
        return north_moves, east_moves, south_moves, west_moves
    return None


def draw_move_hints(grid, screen, tile, settings):
    """Draws the possible movement hints for the selected unit."""
    if tile is not None:
        north_moves, east_moves, south_moves, west_moves = get_unit_directional_moves(tile.unit)
        if north_moves is None or east_moves is None or south_moves is None or west_moves is None or tile.unit.can_move is False:
            return
        # West x=-1, y=0
        draw_directional_hint(screen, grid, tile, west_moves, -1, 0, settings.move_hint_color)
        # East x=+1, y=0
        draw_directional_hint(screen, grid, tile, east_moves, 1, 0, settings.move_hint_color)
        # North x=0, y=-1
        draw_directional_hint(screen, grid, tile, north_moves, 0, -1, settings.move_hint_color)
        # South x=-0, y=+1
        draw_directional_hint(screen, grid, tile, south_moves, 0, 1, settings.move_hint_color)


def clear_move_hints(grid, screen, tile, unit, settings):
    """Clears the already drawn unit movement hints"""
    if tile is not None:
        hint_color = (0, 0, 0)
        north_moves, east_moves, south_moves, west_moves = get_unit_directional_moves(unit)
        if north_moves is None or east_moves is None or south_moves is None or west_moves is None:
            return
        # West x=-1, y=0
        draw_directional_hint(screen, grid, tile, west_moves, -1, 0, hint_color)
        # East x=+1, y=0
        draw_directional_hint(screen, grid, tile, east_moves, 1, 0, hint_color)
        # North x=0, y=-1
        draw_directional_hint(screen, grid, tile, north_moves, 0, -1, hint_color)
        # South x=-0, y=+1
        draw_directional_hint(screen, grid, tile, south_moves, 0, 1, hint_color)


def clear_old_facing_move_hints(grid, screen, tile, oldfacing, settings):
    """Clears the old facing movement hints of the tile"""
    if tile is not None:
        hint_color = (0, 0, 0)
        north_moves, east_moves, south_moves, west_moves = get_old_facing_directional_moves(tile.unit, oldfacing)
        if north_moves is None or east_moves is None or south_moves is None or west_moves is None:
            return
        # West x=-1, y=0
        draw_directional_hint(screen, grid, tile, west_moves, -1, 0, hint_color)
        # East x=+1, y=0
        draw_directional_hint(screen, grid, tile, east_moves, 1, 0, hint_color)
        # North x=0, y=-1
        draw_directional_hint(screen, grid, tile, north_moves, 0, -1, hint_color)
        # South x=-0, y=+1
        draw_directional_hint(screen, grid, tile, south_moves, 0, 1, hint_color)


def draw_directional_hint(screen, grid, tile, total_moves, xinc, yinc, hint_color):
    x, y = get_tile_position(grid, tile)
    #print(time.strftime('%MM:%SS') + ' ddh : current tile pos = (' + str(x) + ', ' + str(y) + ')')
    for i in range(1, total_moves + 1):
        # checks to make sure the next step is within the bounds of the array
        if (x + (i * xinc) >= len(grid.tiles)) or (x + (i * xinc) < 0):
            return
        if (y + (i * yinc) >= len(grid.tiles[x + (i * xinc)])) or (y + (i * yinc) < 0):
            return

        if not grid.tiles[x + (i * xinc)][y + (i * yinc)].active or grid.tiles[x + (i * xinc)][y + (i * yinc)] == grid.selected_tile:
            width = grid.tiles[x + (i * xinc)][y + (i * yinc)].rect[2]
            height = grid.tiles[x + (i * xinc)][y + (i * yinc)].rect[3]
            nX = grid.tiles[x + (i * xinc)][y + (i * yinc)].rect[0]
            nY = grid.tiles[x + (i * xinc)][y + (i * yinc)].rect[1]
            #print(time.strftime('%MM:%SS') + ' ddh : draw at tile = (' + str(x + (i * xinc)) + ', ' + str(y + (i * yinc)) + ')')
            pygame.draw.rect(screen, hint_color, (nX, nY, width, height), 0)
        else:
            return


def get_tile_position(grid, tile):
    """returns the (x, y) position of the tile"""
    # TODO - should probably just save this in the tile class
    if tile is not None:
        for x in range(len(grid.tiles)):
            for y in range(len(grid.tiles[x])):
                if grid.tiles[x][y] == tile:
                    return x, y
    return None


def draw_grid(settings, screen, grid):
    # draw horizontal lines
    for y in range(0, settings.rows + 1):
        yPos = settings.bufferTop + settings.tileHeight * y
        pygame.draw.line(screen,
                         (255, 0, 0),
                         (settings.bufferLeft, yPos),
                         (settings.screenWidth - settings.bufferRight, yPos),
                         5)

    # draw vertical lines
    for x in range(0, settings.columns + 1):
        xPos = settings.bufferLeft + settings.tileWidth * x
        pygame.draw.line(screen,
                         (255, 0, 0),
                         (xPos, settings.bufferTop),
                         (xPos, settings.screenHeight - settings.bufferBot),
                         5)

    # temp bounding box
    pygame.draw.rect(screen,
                     (0, 255, 0),
                     grid.rect,
                     1)


def draw_tiles(settings, screen, grid):
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            if grid.tiles[x][y].active:
                draw_tile(screen, grid.tiles[x][y])


def draw_tile(screen, tile):
    # draw tile
    tile.draw_self(screen)
    # draw identifier
    tile.render_id(screen)
    # draw facing indicator
    tile.draw_facing(screen)


def clear_tile(screen, tile, settings):
    # draw blank tile
    pygame.draw.rect(screen, settings.screenBG, (tile.rect[0] - 5, tile.rect[1] - 5, tile.rect[2] + 10, tile.rect[3] + 10), 0)


def draw_selection_box(screen, rect):
    # draw 4 dashed lines from the given rect
    # rect = (x, y, width, height)
    # TODO - Only need to store 4 points
    lines = []
    # 0 - top-left -> top-right
    lines.append([(rect[0], rect[1]), (rect[0] + rect[2], rect[1])])
    # 1 - top-right -> bottom-right
    lines.append([lines[0][1], (rect[0] + rect[2], rect[1] + rect[3])])
    # 2 - bottom-right -> bottom-left
    lines.append([lines[1][1], (rect[0], rect[1] + rect[3])])
    # 2 - bottom-left -> top-left
    lines.append([lines[2][1], lines[0][0]])

    for i in range(len(lines)):
        # lines[i] = [(x1, y1), (x2, y2)]
        segmentLength = 10
        blankLength = 5

        totalDistance = math.sqrt((lines[i][1][0] - lines[i][0][0])**2 + (lines[i][1][1] - lines[i][0][1])**2)
        start = lines[i][0]
        end = lines[i][1]

        distance = totalDistance
        while distance > 0:
            if distance >= 10:
                # draw 10
                ratio = segmentLength / distance
                segmentEnd = (round(((1 - ratio) * start[0]) + (ratio * end[0])), round(((1 - ratio) * start[1]) + (ratio * end[1])))
                pygame.draw.line(screen, (0, 255, 0), start, segmentEnd, 3)
                distance -= 10

                if distance >= 5:
                    # skip 5, set start to 5 past the last segment
                    blankRatio = blankLength / distance
                    start = (round(((1 - blankRatio) * segmentEnd[0]) + (blankRatio * end[0])), round(((1 - blankRatio) * segmentEnd[1]) + (blankRatio * end[1])))
                    distance -= 5
            else:
                # TODO - draw partial line
                break


def spawn_units(grid):
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            if x < 1:
                grid.tiles[x][y].active = True
                # TODO - name assignment + unit creation
                name = chr(65 + x) + chr(65 + y)
                team = 1
                newUnit = Unit(name, team)
                grid.tiles[x][y].unit = newUnit
            elif x == 15 and (y == 4 or y == 5):
                grid.tiles[x][y].active = True
                # TODO - name assignment + unit creation
                name = chr(65 + x) + chr(65 + y)
                team = 2
                newUnit = Unit(name, team)
                grid.tiles[x][y].unit = newUnit


def create_pause_screen(settings):
    pause_screen = pygame.Surface((settings.screenWidth-10, settings.screenHeight-10))
    pause_screen.set_alpha(128)
    pause_screen.fill((166, 166, 166))
    return pause_screen


def check_turn_change(grid, settings, draw_list):
    if check_all_units_action_status(grid, settings):
        if settings.cturn == 2:
            settings.cturn = 1
            settings.cmode = ''
        else:
            settings.cturn = 2
            settings.cmode = 'ai turn'
            grid.next_ai_action = time.time() + settings.ai_turn_delay
        grid.reset_team_action_status()
        draw_list.append({'draw turn text': 0})
        # redraw next teams units, so their name color changes
        add_team_to_draw_list(grid, draw_list, settings.cturn)


def add_team_to_draw_list(grid, draw_list, team):
    """This function adds the given team to the draw_list"""
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            tile = grid.tiles[x][y]
            if tile.unit is not None:
                if tile.unit.team == team:
                    # draw
                    draw_list.append({'draw tile': tile})
                    if tile.selected:
                        # draw selection
                        draw_list.append({'draw select': tile})


def check_all_units_action_status(grid, settings):
    """Checks all units active in the grid
        :returns True if no units on team cturn can move/action/rotate
        :returns False if any unit on team cturn can move/action/rotate"""
    for x in range(len(grid.tiles)):
        for y in range(len(grid.tiles[x])):
            if grid.tiles[x][y].active:
                unit = grid.tiles[x][y].unit
                if unit is not None:
                    if unit.team == settings.cturn:
                        if unit.can_move or unit.can_action or unit.can_rotate:
                            return False
    return True
