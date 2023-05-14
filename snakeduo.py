from board import Board
from snake import Snake
import math
import json
from tqdm import trange
import os

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

    
    def snakes_initialized(self):
        return self.snake1.client_id != None and self.snake2.client_id != None

    def initialize_team(self, game_state):
        if not self.snakes_initialized():
            return
        
        self.turn = game_state["turn"]
        self.board = Board(
            game_state["board"]["width"], 
            game_state["board"]["height"],
            our_snakes=self.snakes,
            all_snakes=game_state["board"]["snakes"]
        )

        self.board.update_state(game_state["board"])
        self.board.save_replay = self.save_replay
        self.append_board_history()


    
    def update_state(self, game_state):
        if game_state["turn"] > self.turn and self.snakes_initialized():
            json.dump(game_state, open("game_states/"+str(game_state["turn"])+".json", "w"))

            self.turn = game_state["turn"]

            self.board.update_state(game_state["board"])

            for snake in self.snakes:
                for snake_info in game_state["board"]["snakes"]:
                    if snake_info["id"] == snake.client_id:
                        snake.update_state(snake_info)
                        break
            
            self.append_board_history()
    
    # This is where the move for each snake is calculated
    def calculate_move(self):
        if self.calculated_turn == self.turn:
            return
        self.calculated_turn = self.turn

        # Below here we try to calculate where to go next! 
        # Each snake tries to find the closest cell with food and move towards it while avoiding direct hits
        if len(self.snake1.get_safe_moves(self.board)) > 0:
            # Find closest food position and safe moves
            closest_food = self.snake1.get_closest_food_pos(self.board)["cell"]
            safe_moves = self.snake1.get_safe_moves(self.board)
            
            # Find the direction to go towards to reach the closest food (snake 1)
            top_priority = -math.inf
            self.snake1_move = safe_moves[0]    # this will be overwritten by a safe move towards food
            if(closest_food.x >= self.snake1.head["x"] and "right" in safe_moves):
                prio = abs(self.snake1.head["x"] - closest_food.x)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake1_move = "right"
            if(closest_food.x <= self.snake1.head["x"] and "left" in safe_moves):
                prio = abs(self.snake1.head["x"] - closest_food.x)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake1_move = "left"
            if(closest_food.y >= self.snake1.head["y"] and "up" in safe_moves):
                prio = abs(self.snake1.head["y"] - closest_food.y)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake1_move = "up"
            if(closest_food.y <= self.snake1.head["y"] and "down" in safe_moves):
                prio = abs(self.snake1.head["y"] - closest_food.y)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake1_move = "down"   
        else:
            self.snake1_move = "up"     # no safe direction exists so who cares where we go
        
        if len(self.snake2.get_safe_moves(self.board)) > 0:
            # Find closest food position and safe moves
            closest_food = self.snake2.get_closest_food_pos(self.board)["cell"]
            safe_moves = self.snake2.get_safe_moves(self.board)

            # Find the direction to go towards to reach the closest food (snake 1)
            top_priority = -math.inf
            self.snake2_move = safe_moves[0]    # this will be overwritten by a safe move towards food
            if(closest_food.x >= self.snake2.head["x"] and "right" in safe_moves):
                prio = abs(self.snake2.head["x"] - closest_food.x)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake2_move = "right"
            if(closest_food.x <= self.snake2.head["x"] and "left" in safe_moves):
                prio = abs(self.snake2.head["x"] - closest_food.x)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake2_move = "left"
            if(closest_food.y >= self.snake2.head["y"] and "up" in safe_moves):
                prio = abs(self.snake2.head["y"] - closest_food.y)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake2_move = "up"
            if(closest_food.y <= self.snake2.head["y"] and "down" in safe_moves):
                prio = abs(self.snake2.head["y"] - closest_food.y)
                if(prio > top_priority):
                    top_priority = prio
                    self.snake2_move = "down"
        else:
            self.snake2_move = "up"     # no safe direction exists so who cares where we go
            
    
    # This is the command that is sent to the server
    def get_move(self, snake):
        if snake == self.snake1:
            return self.snake1_move
        elif snake == self.snake2:
            return self.snake2_move
        else:
            return None
    
    def append_board_history(self):
        self.board_history.append(self.board.copy())
    
    def on_end(self):
        if self.save_replay:
            # delete everything in board directory
            for filename in os.listdir("board"):
                os.remove("board/"+filename)

            for i in trange(len(self.board_history), desc="Saving replay"):
                self.board_history[i].save_to_img(i, res="high")
            

            self.board_history[-1].create_gif()
        
    
    def end_team(self, snake):
        if snake == self.snake1:
            self.snake1_has_ended = True

        if snake == self.snake2:
            self.snake2_has_ended = True

        if self.snake1_has_ended and self.snake2_has_ended:
            self.on_end()


