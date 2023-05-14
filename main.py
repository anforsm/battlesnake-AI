# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import random
import typing

from networkmanager import network
from snakeduo import SnakeDuo
from snake import Snake, ControllableSnake as CSnake

game_width = 11
game_height = 11





# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # TODO: Step 1 - Prevent your Battlesnake from moving out of bounds
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    if my_head['x'] == 0:
        is_move_safe['left'] = False
    elif my_head['x'] == board_width - 1:
        is_move_safe['right'] = False

    if my_head['y'] == 0:
        is_move_safe['down'] = False
    elif my_head['y'] == board_height - 1:
        is_move_safe['up'] = False

    # TODO: Step 2 - Prevent your Battlesnake from colliding with itself
    my_body = game_state['you']['body']
    
    for body_part in my_body:
        if body_part['x'] == my_head['x'] + 1 and body_part['y'] == my_head['y']:
            is_move_safe['right'] = False
        elif body_part['x'] == my_head['x'] - 1 and body_part['y'] == my_head['y']:
            is_move_safe['left'] = False
        elif body_part['x'] == my_head['x'] and body_part['y'] == my_head['y'] + 1:
            is_move_safe['up'] = False
        elif body_part['x'] == my_head['x'] and body_part['y'] == my_head['y'] - 1:
            is_move_safe['down'] = False



    # TODO: Step 3 - Prevent your Battlesnake from colliding with other Battlesnakes
    # opponents = game_state['board']['snakes']

    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        return {"move": "down"}

    # Choose a random move from the safe ones
    next_move = random.choice(safe_moves)

    # TODO: Step 4 - Move towards food instead of random, to regain health and survive longer
    food = game_state['board']['food']
    food_x = food[0]['x']
    food_y = food[0]['y']

    if food_x > my_head['x'] and is_move_safe['right']:
        next_move = 'right'
    elif food_x < my_head['x'] and is_move_safe['left']:
        next_move = 'left'
    elif food_y > my_head['y'] and is_move_safe['up']:
        next_move = 'up'
    elif food_y < my_head['y'] and is_move_safe['down']:
        next_move = 'down'


    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    #duo1 = SnakeDuo("Team 1", "#FF0000", CSnake("1", "Snake 1"), CSnake("2", "Snake 2"), save_replay=False)

    #duo2 = SnakeDuo("Team 2", "#00FF00", CSnake("3", "Snake 3"), CSnake("4", "Snake 4"), save_replay=False)

    #snakes = duo1.snakes# + duo2.snakes

    #network.set_snakes(snakes)
    network.start_server()
