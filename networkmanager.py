from flask import Flask
from flask import request
import os
import logging
from snakeduo import SnakeDuo
from snake import Snake, ControllableSnake as CSnake
from multiprocessing import Process, Lock, Manager, Queue, Pool

our_color = "#ff4e03"

class Game():
    def __init__(self, game_id):
        self.game_id = game_id
        self.snakes = {}
        self.teams = {}

def game_process(game_id, input_queue, output_queue):
    game = Game(game_id)
    while True:
        request_type, snake_id, request_data = input_queue.get()

        if request_type == "start":
            response = start_function(game, snake_id, request_data)
        elif request_type == "move":
            response = move_function(game, snake_id, request_data)
        elif request_type == "end":
            response, all_ended = end_function(game, snake_id, request_data)
            output_queue.put(all_ended)
        else:
            print("Invalid request type: ", request_type)
        
        output_queue.put(response)

def start_function(game, snake_id, request_data):
    team_id = 1 if snake_id == "1" or snake_id == "2" else 2

    if not team_id in game.teams:
        if team_id == 1:
            team = SnakeDuo("Team 1", our_color, CSnake("1", "Snake 1"), CSnake("2", "Snake 2"), save_replay=True)
        elif team_id == 2:
            team = SnakeDuo("Team 2", "#00FF00", CSnake("3", "Snake 1"), CSnake("4", "Snake 2"), save_replay=False)

        game.teams[team_id] = team
        game.snakes[team.snake1.id] = team.snake1
        game.snakes[team.snake2.id] = team.snake2

    return game.snakes[snake_id].net.on_start(request_data)

def end_function(game, snake_id, request_data):
    result = game.snakes[snake_id].net.on_end(request_data)
    teams = game.teams.values()

    all_teams_ended = True
    for team in teams:
        if not team.game_ended:
            all_teams_ended = False
            break

    return result, all_teams_ended

def move_function(game, snake_id, request_data):
    return game.snakes[snake_id].net.on_move(request_data)

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances: 
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class NetworkManager(metaclass=SingletonMeta):
    def __init__(self):
        self.app = Flask("Battlesnake")
        self.snake_map = {}
        self.snakes = []
        self.games = {}
        self.snake_ids = [1, 2, 3, 4]
        self.live_games = set()
        self.input_queues = {}
        self.output_queues = {}
        self.locks = {}
        self.processing_pool = Pool(processes=16)
        self.game_start_lock = Lock()
    
    def create_endpoints(self):

        @self.app.get("/<snake_id>/")
        def on_info(snake_id):
            if snake_id == "favicon.ico":
                return ""
            
            team_id = 1 if snake_id == "1" or snake_id == "2" else 2 
            color = our_color if team_id == 1 else "#00FF00"
            return {
                "apiversion": "1",
                "author": "Anton Forsman & Nils Odin",
                "color": color,
                "head": "tiger-king",
                "tail": "tiger-tail",
            }
        
        @self.app.post("/<snake_id>/start/")
        def on_start(snake_id):
            with self.game_start_lock:
                request_json = request.get_json()
                game_id = request_json["game"]["id"]

                if game_id not in self.live_games:
                    print("[INFO] Game started, " + game_id[:3])
                    self.live_games.add(game_id)
                    self.locks[game_id] = Lock()
                    self.input_queues[game_id] = Queue()
                    self.output_queues[game_id] = Queue()
                    Process(target=game_process, args=(game_id, self.input_queues[game_id], self.output_queues[game_id])).start()
            
                with self.locks[game_id]:
                    self.input_queues[game_id].put(("start", snake_id, request_json))
                    response = self.output_queues[game_id].get()
            
                return response

        
        @self.app.post("/<snake_id>/move/")
        def on_move(snake_id):
            request_json = request.get_json()
            game_id = request_json["game"]["id"]

            with self.locks[game_id]:
                self.input_queues[game_id].put(("move", snake_id, request_json))
                response = self.output_queues[game_id].get()

            return response

        
        @self.app.post("/<snake_id>/end/")
        def on_end(snake_id):
            request_json = request.get_json()
            game_id = request_json["game"]["id"]

            with self.locks[game_id]:
                self.input_queues[game_id].put(("end", snake_id, request_json))
                all_teams_ended = self.output_queues[game_id].get()
                response = self.output_queues[game_id].get()

            if all_teams_ended:
                del self.locks[game_id]
                del self.input_queues[game_id]
                del self.output_queues[game_id]
                self.live_games.remove(game_id)
                print("[INFO] Game ended, deleting game", game_id[:3])


            return response

        @self.app.after_request
        def identify_server(response):
            response.headers.set(
                "server", "Battlesnake"
            )
            return response
    
    def delete_game(self, game_id):
        del self.games[game_id]

    def start_server(self):
        #host = "0.0.0.0"
        #host = "10.10.20.13"
        host = "10.10.10.101"
        port = int(os.environ.get("PORT", "8000"))

        logging.getLogger("werkzeug").setLevel(logging.ERROR)

        self.create_endpoints()
        @self.app.route("/ping")
        def ping():
            return "pong"

        self.app.run(host=host, port=port, debug=True, threaded=True)
