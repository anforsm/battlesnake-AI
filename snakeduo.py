from board import Board, GeneralBoard as GBoard
from snake import Snake
import math
from collections import defaultdict
import random
import json
from tqdm import trange
import os
from datetime import datetime
from copy import copy
import numpy as np
import time

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

        self.move_logs = []

    
    def snakes_initialized(self):
        return self.snake1.client_id is not None and self.snake2.client_id is not None

    def initialize_team(self, game_state):
        if not self.snakes_initialized():
            return

        
        self.turn = -1
        self.board = Board(
            game_state["board"]["width"], 
            game_state["board"]["height"],
            our_snakes=self.snakes,
            all_snakes_json=game_state["board"]["snakes"]
        )

        self.board.save_replay = self.save_replay

        self.update_state(game_state, force=True)

    
    def update_state(self, game_state, force=False):
        if force or (game_state["turn"] > self.turn and self.snakes_initialized()):
            # print snake latency
            # print("Snake 1 latency: " + str(game_state["board"]["snakes"][0]["latency"]))
            # print("Snake 2 latency: " + str(game_state["board"]["snakes"][1]["latency"]))
            game_id = game_state["game"]["id"]
            path = "./game_states/"+datetime.now().strftime("%Y-%m-%d_%H")+" (" + game_id[:3] + ")"
            os.makedirs(path, exist_ok=True)
            json.dump(game_state, open(path + "/" + str(game_state["turn"])+".json", "w"))

            self.turn = game_state["turn"]
            #print("--------------Turn start" + str(self.turn) + "--------------")

            self.board.update_state(game_state["board"])

            for snake in self.snakes:
                for snake_info in game_state["board"]["snakes"]:
                    if snake_info["id"] == snake.client_id:
                        snake.made_move = False
                        snake.snake.update_state(snake_info)
                        break
            
            
    
    def set_snake_move(self, snake, move, reason=None):
        if move is not None:
            move_log = {
                "turn": self.turn,
                "snake": snake.name,
                "move": move,
                "reason": reason
            }
            self.move_logs.append(move_log)

            #predicted_safe_future = snake.snake.alternative_futures(move)
            #for future_state in predicted_safe_future:
            #    future_snake = future_state.get_snake(snake.client_id)
            #    snake.snake.board.get_cell(future_snake.head.x, future_snake.head.y).set_future(snake)


        if snake == self.snake1:
            self.snake1_move = move
        elif snake == self.snake2:
            self.snake2_move = move
    
    def get_snake_move(self, snake):
        if snake == self.snake1:
            return self.snake1_move
        elif snake == self.snake2:
            return self.snake2_move
    
    def get_other_snake(self, snake):
        if snake == self.snake1:
            return self.snake2
        elif snake == self.snake2:
            return self.snake1
    
    def calculate_move(self, snake):
        if snake.snake.is_dead:
            return None

        self.set_snake_move(snake, "up", reason="default")


        other_snake = self.get_other_snake(snake)
        moves_that_kill_teammate = []
        moves_that_kill_enemy = []
        t1_other_snake_die = time.time()
        #print("[INFO] This snake is " + str(snake.client_id))
        for move in ["up", "down", "left", "right"]:
            #print("[INFO] Checking move " + move)
            future_dead_snakes = snake.snake.other_snake_will_die_because_of_move(move)
            for dead_snake in future_dead_snakes:
                if dead_snake == other_snake.client_id:
                    moves_that_kill_teammate.append(move)
                else:
                    moves_that_kill_enemy.append(move)
        t2_other_snake_die = time.time()
        


        t1_future_move = time.time()
        moves_without_certain_future_death = snake.snake.get_moves_without_future_death()
        t2_future_move = time.time()

        t1_move_food = time.time()
        moves_in_direction_of_food, distance_to_closest_food = snake.get_direction_of_food(self.board)
        t2_move_food = time.time()

        t1_safe_move = time.time()
        completely_safe_immediate_moves = snake.get_safe_moves(self.board)
        t2_safe_move = time.time()



        t1_safish_move = time.time()
        could_be_safe_immediate_moves = snake.snake.get_free_moves()
        t2_safish_move = time.time()

        #moves_in_direction_of_food = []
        #could_be_safe_immediate_moves = []

        t1_death_timer = time.time()
        moves_with_death_counter = []
        moves_with_death_counter_map = {}
        for move in ["up", "down", "left", "right"]:
            death_timer = len(snake.snake.alternative_futures(move))
            moves_with_death_counter.append((move, death_timer))
            moves_with_death_counter_map[move] = death_timer
        t2_death_timer = time.time()
        
        t1_territory_increase = time.time()
        distance_to_closest_food_map = {}
        territory_size_increases = {}
        for move in ["up", "down", "left", "right"]:
            territory_size_increases[move] = snake.get_potential_territory_increase(move)
            distance_to_closest_food_map[move] = distance_to_closest_food + 1 * (
                1 if move in moves_in_direction_of_food else -1
            )
        t2_territory_increase = time.time()


        state_information = {
        }

        for move in ["up", "down", "left", "right"]:
            state_information[move] = {
                "increase_in_territory": territory_size_increases[move],
                "food_distance": distance_to_closest_food_map[move],
                "death_timer": moves_with_death_counter_map[move], 
            }


        info = {
            "moves_without_certain_future_death": moves_without_certain_future_death,
            "moves_in_direction_of_food": moves_in_direction_of_food,
            "completely_safe_immediate_moves": completely_safe_immediate_moves,
            "could_be_safe_immediate_moves": could_be_safe_immediate_moves,
            "moves_with_death_counter": moves_with_death_counter,
            "moves_that_kill_teammate": moves_that_kill_teammate,
            "moves_that_kill_enemy": moves_that_kill_enemy,
            "state_information": state_information,
            "times": {
                "other_snake_die": (t2_other_snake_die - t1_other_snake_die)*1000,
                "future_move": (t2_future_move - t1_future_move)*1000,
                "move_food": (t2_move_food - t1_move_food)*1000,
                "safe_move": (t2_safe_move - t1_safe_move)*1000,
                "safish_move": (t2_safish_move - t1_safish_move)*1000,
                "death_timer": (t2_death_timer - t1_death_timer)*1000,
                "territory_increase": (t2_territory_increase - t1_territory_increase)*1000,
            }
        }

        # main move order
        # go such that we do not have a chance of dying
        # go such that we have a chance of dying
        # go such that we will die, but in the most amount of turns
        # go such that we die

        # change order such that, if in one direction we know we will survive for one step but die
        # in the future, and the other direction we might die the next step, but survive the future
        # we should go in the direction where we might die in one step

        # other stuff to check for
        # - if our move makes it so that our teammate snake will die, dont do it
        # - if our move makes it so that a nearby enemy snake will die, do it
        # - TAKE INTO ACCOUNT OTHER SNAKES MOVE
        # - at first, try to prioritize a move that will extend our snake's territory
        # - if we are running out of food, ignore territory and just go for food
        # - if we are in the end game, try to circle a territory,
        #    while the other snake goes for a kill or trying to decrease enemy's territory


        # heuristic is a recursive list of tuples
        # the first element of the tuple is the name of the heuristic
        # the second element is the heuristic to be used if the first element is true
        # if a herustic is empty, we are done and can return a random move that follows the heuristic
        # the heuristic should be applied in order of the list
        # if the heuristic is exhausted, we are also done and can return a random move that follows the heuristic

        #heuristic = [
        #    ("no-immediate-death", [
        #        ("no-future-death", [
        #            ("save-teammate", [
        #                ("kill-enemy", [
        #                    ("towards-food", [])
        #                ]),
        #                ("towards-food", [])
        #            ]),
        #            ("kill-enemy", [
        #                ("towards-food", [])
        #            ]),
        #            ("towards-food", [])
        #        ]),
        #        ("least-future-death", [
        #            ("save-teammate", [
        #                ("kill-enemy", [])
        #            ]),
        #            ("kill-enemy", []),
        #            ("away-from-food", []),
        #        ]),
        #    ]),
        #    ("chance-of-immediate-death", [
        #        ("no-future-death", [
        #            ("save-teammate", [
        #                ("kill-enemy", []),
        #            ]),
        #        ]),
        #        ("least-future-death", [
        #            ("save-teammate", [
        #                ("kill-enemy", [])
        #            ]),
        #            ("away-from-food", []),
        #        ]),
        #    ]),
        #]

        standard_end_heuristic = [
            ("save-teammate", [
                ("kill-enemy", [
                    ("final-scoring", [])
                ]),
                ("final-scoring", [])
            ]),
            ("kill-enemy", [
                ("final-scoring", [])
            ]),
            ("final-scoring", [])
        ]

        about_to_die_heuristic = [
            ("save-teammate", [
                ("kill-enemy", [
                    ("away-from-food", [])
                ]),
                ("away-from-food", [])
            ]),
            ("kill-enemy", [
                ("away-from-food", [])
            ]),
            ("away-from-food", [])
        ]

        heuristic = [
            ("no-future-death", [
                ("no-immediate-death", standard_end_heuristic),
                ("chance-of-immediate-death", standard_end_heuristic),
            ]),
            ("least-future-death", [
                ("no-immediate-death",  about_to_die_heuristic),
                ("chance-of-immediate-death", about_to_die_heuristic),
            ]),
        ]


        # state information is a dictionary of information that is passed to the scoring function
        # for example
        # state_information = {
        #   "up": {
        #     "death_timer": 5,
        #     "food_distance": 10,
        #     "increase_in_territory": 5,
        #   },
        #   "down": {
        #   ...
        #   }



        def final_move_scoring_function(state_information):
            move_scores = {
                "up": 0,
                "down": 0,
                "left": 0,
                "right": 0,
            }

            for move in ["up", "down", "left", "right"]:
                # 1 is very close, 0 is very far
                # something is weird
                food_distance_fraction = state_information[move]["food_distance"] / (self.board.width + self.board.height)
                # health fraction
                # 1 is about to die, 0 is full health
                health_fraction = 1 - snake.snake.health / 100
                #print("move: " + move, "food_distance_fraction: " + str(food_distance_fraction), "health_fraction: " + str(health_fraction))


                food_weight = np.exp(3*health_fraction - 2) + food_distance_fraction 
                territory_weight = 1

                move_scores[move] = food_weight + territory_weight
            
            return move_scores





        #print("Turn " + str(self.turn) + " - " + snake.name)

        def find_move(heuristic, allowed_moves, heuristic_history=None):
            if heuristic_history is None:
                heuristic_history = []


            pre_allowed_moves = copy(allowed_moves)
            for heuristic_name, next_heuristic in heuristic:
                extra_data = {}
                allowed_moves = copy(pre_allowed_moves)
                #print("Checking heuristic: " + heuristic_name)
                if heuristic_name == "no-immediate-death":
                    allowed_moves = [move for move in allowed_moves if move in completely_safe_immediate_moves]
                elif heuristic_name == "chance-of-immediate-death":
                    allowed_moves = [move for move in allowed_moves if move in could_be_safe_immediate_moves]
                    #print("Checked could be safe moves", str(could_be_safe_immediate_moves), str(allowed_moves))
                elif heuristic_name == "no-future-death":
                    allowed_moves = [move for move in allowed_moves if move in moves_without_certain_future_death]
                elif heuristic_name == "least-future-death":
                    move_death_timer_dict = defaultdict(lambda: 0)
                    for move, death_timer in moves_with_death_counter:
                        move_death_timer_dict[move] = death_timer

                    death_timer_for_allowed_moves = [(move, move_death_timer_dict[move]) for move in allowed_moves]
                    if len(death_timer_for_allowed_moves) > 0:
                        best_death_timer = max(death_timer_for_allowed_moves, key=lambda x: x[1])[1]

                        if best_death_timer > 0:
                            allowed_moves = [move for move, death_timer in death_timer_for_allowed_moves if death_timer == best_death_timer]
                        else:
                            allowed_moves = []

                elif heuristic_name == "towards-food":
                    allowed_moves = [move for move in allowed_moves if move in moves_in_direction_of_food]
                elif heuristic_name == "away-from-food":
                    allowed_moves = [move for move in allowed_moves if move not in moves_in_direction_of_food]
                elif heuristic_name == "save-teammate":
                    allowed_moves = [move for move in allowed_moves if move not in moves_that_kill_teammate]
                elif heuristic_name == "kill-enemy":
                    allowed_moves = [move for move in allowed_moves if move in moves_that_kill_enemy]
                elif heuristic_name == "final-scoring":
                    move_scores = final_move_scoring_function(state_information)
                    allowed_move_scores = {move: move_scores[move] for move in allowed_moves}
                    max_score = max(allowed_move_scores.values())
                    allowed_moves = [move for move in allowed_moves if move_scores[move] == max_score]
                    extra_data["move_scores"] = move_scores
                    extra_data["best_move_score"] = max_score
                else:
                    raise Exception("Unknown heuristic name: {}".format(heuristic_name))
                
                if len(allowed_moves) == 0:
                    continue
                
                next_heuristic_history = heuristic_history + [heuristic_name]
                if len(next_heuristic) == 0:
                    self.set_snake_move(snake, random.choice(allowed_moves), reason={
                            "heuristics used": str(next_heuristic_history),
                            "info": info,
                            "extra_data": extra_data
                        })
                    return True
                
                find_move(next_heuristic, allowed_moves, next_heuristic_history)
                return True

            
            self.set_snake_move(snake, random.choice(pre_allowed_moves), reason={
                "heuristic used": str(heuristic_history),
                "info": info
                })
            return True 

        find_move(heuristic, ["up", "down", "left", "right"])

        snake.make_move()
        snake.made_move = True
        return







        if len(completely_safe_future_moves) > 0:

            # check if we can move in the direction of food
            for move in completely_safe_future_moves:
                if move in moves_in_direction_of_food:
                    self.set_snake_move(snake, move, reason="move in direction of food")
                    return
                
            # otherwise just move in a direction without future death
            self.set_snake_move(snake, moves_without_certain_future_death[0], reason="no food, moving in direction without future death")
            return

        # we have a death timer on ourselves

        # otherwise move in a completely safe direction, if possible
        if len(completely_safe_immediate_moves) > 0:
            self.set_snake_move(snake, completely_safe_immediate_moves[0], reason="we are about to die, moving in immediate safe direction")
            return
            
        # otherwise move in a direction that could be safe
        if len(could_be_safe_immediate_moves) > 0:
            self.set_snake_move(snake, could_be_safe_immediate_moves[0], reason="we are about to die, might have head on collision here")
            return
        
        # otherwise just move up
        self.set_snake_move(snake, "up", reason="we will die, RIP")
        return







        return
        safe_moves = snake.get_safe_moves(self.board)

        # if there are no safe moves, just go up
        if len(safe_moves) == 0:
            self.set_snake_move(snake, "up", reason="no safe or unsafe direction, going up, awaiting death")
            return
        
        new_safe_moves = []
        best_moves = []
        best_free_space = -1
        safe_move_infos = []
        #chosen_futures = None
        for safe_move in safe_moves:
            predicted_future = snake.snake.alternative_futures(safe_move)
            free_space = len(predicted_future)

            if free_space == 11:
                best_moves.append(safe_move)

            #if free_space > best_free_space:
                safe_move_infos.append({
                    "move": safe_move,
                    "free_space": free_space,
                    "predicted_future": [GBoard.get_direction_between_coords(predicted_future[i].get_snake(snake.client_id).head.x, predicted_future[i].get_snake(snake.client_id).head.y, predicted_future[i+1].get_snake(snake.client_id).head.x, predicted_future[i+1].get_snake(snake.client_id).head.y) for i in range(len(predicted_future)-1)],
                })
                best_free_space = free_space
                best_moves = [safe_move]

        safe_moves = best_moves
        



        direction_of_food = snake.get_direction_of_food(self.board)

        # if there is no food, just go in a random safe direction
        if direction_of_food is None:
            self.set_snake_move(snake, safe_moves[0], reason={
                "text": "no food, best direction with safe depth of " + str(best_free_space),
                "safe_move_infos": safe_move_infos
            })
            return
            
        # if there is food, go in the direction of the food if it is safe
        for direction in direction_of_food:
            if direction in safe_moves:
                self.set_snake_move(snake, direction, reason={
                    "text": "direction of food, best direction with safe depth of " + str(best_free_space),
                    "safe_move_infos": safe_move_infos
                })
                break
            
        # if there is no safe direction towards the food, 
        # just go in a random safe direction
        if self.get_snake_move(snake) is None:
            self.set_snake_move(snake, safe_moves[0], reason={
                "text": "cant go in direction of food, safe direction with safe depth of " + str(best_free_space),
                "safe_move_infos": safe_move_infos
            })
            return
        
        # if there is no safe direction
        # try to find an unsafe but available direction
        if self.get_snake_move(snake) is None:
            self.set_snake_move(snake, snake.snake.get_free_moves(self.board)[0], reason={
                "text": "no safe direction, found unsafe direction",
                "safe_move_infos": safe_move_infos
            })
            return
        
        # if there is no safe or unsafe direction
        # just go up to certain death
        if self.get_snake_move(snake) is None:
            self.set_snake_move(snake, "up", reason={
                "text": "no safe or unsafe direction, going up, awaiting death",
                "safe_move_infos": safe_move_infos
            })
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


        self.append_board_history()
    
    # This is the command that is sent to the server
    def get_move(self, snake):
        if snake == self.snake1:
            return self.snake1_move
        elif snake == self.snake2:
            return self.snake2_move
        else:
            return None
    
    def append_board_history(self):

        board_copy = self.board.b.copy()
        #for cell in self.board.b.all_cells:
            #print(cell.future)
        self.board_history.append(board_copy)
    
    def on_end(self, game_state):
        game_id = game_state["game"]["id"]
        if self.save_replay:

            path = "./move_logs/"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+" (" + game_id[:3] + ")"
            os.makedirs(path, exist_ok=True)
            json.dump(self.move_logs, open(path + "/move_logs.json", "w"), indent=4)


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


