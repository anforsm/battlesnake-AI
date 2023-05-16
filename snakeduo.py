from board import Board
from snake import Snake
import math
import json
from tqdm import trange
import os
from datetime import datetime

class SnakeDuo():
    def __init__(self, name, color, snake1, snake2, save_replay=False):
        self.name = name
        self.color = color
        self.save_replay = save_replay

        self.snake1 = snake1
        self.snake2 = snake2

        snake1.team = self
        snake2.team = self

        self.snakes = [snake1, snake2]

        self.turn = -1
        self.calculated_turn = -1

        self.board = None

        self.board_history = []

        self.snake1_has_ended = False
        self.snake2_has_ended = False

        self.game_ended = False

        self.snake1_move = "up"
        self.snake2_move = "up"

    
    def snakes_initialized(self):
        return self.snake1.client_id is not None and self.snake2.client_id is not None

    def initialize_team(self, game_state):
        if not self.snakes_initialized():
            return

        print("[INFO] Initialized snake team")
        
        self.turn = -1
        self.board = Board(
            game_state["board"]["width"], 
            game_state["board"]["height"],
            our_snakes=self.snakes,
            all_snakes_json=game_state["board"]["snakes"]
        )

        print(self.snake1.snake.client_id)

        #self.board.update_state(game_state["board"])
        self.board.save_replay = self.save_replay

        #self.append_board_history()
        self.update_state(game_state, force=True)

    
    def update_state(self, game_state, force=False):
        if force or (game_state["turn"] > self.turn and self.snakes_initialized()):
            json.dump(game_state, open("game_states/"+str(game_state["turn"])+".json", "w"))

            self.turn = game_state["turn"]

            self.board.update_state(game_state["board"])

            for snake in self.snakes:
                for snake_info in game_state["board"]["snakes"]:
                    if snake_info["id"] == snake.client_id:
                        snake.snake.update_state(snake_info)
                        break
            
            print("[INFO] Updated state for snake team")
            self.append_board_history()
    
    def set_snake_move(self, snake, move):
        if snake == self.snake1:
            self.snake1_move = move
        elif snake == self.snake2:
            self.snake2_move = move
    
    def get_snake_move(self, snake):
        if snake == self.snake1:
            return self.snake1_move
        elif snake == self.snake2:
            return self.snake2_move
    
    def calculate_move(self, snake):
        safe_moves = snake.get_safe_moves(self.board)

        # if there are no safe moves, just go up
        if len(safe_moves) == 0:
            self.set_snake_move(snake, "up")
            return

        direction_of_food = snake.get_direction_of_food(self.board)

        # if there is no food, just go in a random safe direction
        if direction_of_food is None:
            self.set_snake_move(snake, safe_moves[0])
            return
            
        # if there is food, go in the direction of the food if it is safe
        for direction in direction_of_food:
            if direction in safe_moves:
                self.set_snake_move(snake, direction)
                break
            
        # if there is no safe direction towards the food, 
        # just go in a random safe direction
        if self.get_snake_move(snake) is None:
            self.set_snake_move(snake, safe_moves[0])
            return
        
        # if there is no safe direction
        # just go in a random direction
        if self.get_snake_move(snake) is None:
            self.set_snake_move(snake, "up")
            return

    
    # This is where the move for each snake is calculated
    def calculate_moves(self):
        if self.calculated_turn == self.turn:
            return
        self.calculated_turn = self.turn


        for snake in self.snakes:
            self.set_snake_move(snake, None)

        for snake in self.snakes:
            self.calculate_move(snake)
    
    # This is the command that is sent to the server
    def get_move(self, snake):
        if snake == self.snake1:
            return self.snake1_move
        elif snake == self.snake2:
            return self.snake2_move
        else:
            return None
    
    def append_board_history(self):
        self.board_history.append(self.board.b.copy())
    
    def on_end(self, game_state):
        game_id = game_state["game"]["id"]
        if self.save_replay:
            # create folder for game
            path = "./replays/"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+" (" + game_id[:3] + ")"
            os.makedirs(path, exist_ok=True)

            for i in trange(len(self.board_history), desc="Saving replay"):
                self.board_history[i].save_to_img(path, i, res="high")
            

            self.board_history[-1].create_gif(path)
        
        self.game_ended = True
        
    
    def end_team(self, snake, game_state):
        if snake == self.snake1:
            self.snake1_has_ended = True

        if snake == self.snake2:
            self.snake2_has_ended = True

        if self.snake1_has_ended and self.snake2_has_ended:
            self.on_end(game_state)


