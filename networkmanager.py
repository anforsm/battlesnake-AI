from flask import Flask
from flask import request
import os
import logging
from snakeduo import SnakeDuo
from snake import Snake, ControllableSnake as CSnake

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
    
    def create_game(self, game_id):
        if game_id not in self.games:
            print(f"[INFO] Game {game_id[:3]} created")
            self.games[game_id] = {
                "snakes": {},
                "teams": {}
            }
    
    def create_team(self, game_id, team_id):
        if team_id in self.games[game_id]["teams"]:
            return

        if team_id == 1:
            team = SnakeDuo("Team 1", "#FF0000", CSnake("1", "Snake 1"), CSnake("2", "Snake 2"), save_replay=True)
        elif team_id == 2:
            team = SnakeDuo("Team 2", "#00FF00", CSnake("3", "Snake 1"), CSnake("4", "Snake 2"), save_replay=False)

        self.games[game_id]["teams"][team_id] = team
        self.games[game_id]["snakes"][team.snake1.id] = team.snake1
        self.games[game_id]["snakes"][team.snake2.id] = team.snake2

    
    def get_snake(self, game_id, snake_id):
        return self.games[game_id]["snakes"][snake_id]

    def set_snakes(self, snakes):
        self.snakes = snakes
        for snake in self.snakes:
            self.snake_map[str(snake.id)] = snake
        return self
    
    def create_endpoints(self):

        @self.app.get("/<snake_id>/")
        def on_info(snake_id):
            if snake_id == "favicon.ico":
                return ""
            
            team_id = 1 if snake_id == "1" or snake_id == "2" else 2 
            color = "#FF0000" if team_id == 1 else "#00FF00"
            return {
                "apiversion": "1",
                "author": "Anton Forsman & Nils Odin",
                "color": color,
                "head": "default",
                "tail": "default",
            }
        
        @self.app.post("/<snake_id>/start/")
        def on_start(snake_id):
            request_json = request.get_json()
            game_id = request_json["game"]["id"]
            team_id = 1 if snake_id == "1" or snake_id == "2" else 2 
            self.create_game(game_id)
            self.create_team(game_id, team_id)

            return self.get_snake(game_id, snake_id).net.on_start(request_json)
        
        @self.app.post("/<snake_id>/move/")
        def on_move(snake_id):
            request_json = request.get_json()
            game_id = request_json["game"]["id"]
            return self.get_snake(game_id, snake_id).net.on_move(request_json)
        
        @self.app.post("/<snake_id>/end/")
        def on_end(snake_id):
            request_json = request.get_json()
            game_id = request_json["game"]["id"]
            game_end_res = self.get_snake(game_id, snake_id).net.on_end(request_json)
            teams = self.games[game_id]["teams"].values()
            all_teams_ended = True
            for team in teams:
                if not team.game_ended:
                    all_teams_ended = False
                    break

            if all_teams_ended:
                print(f"[INFO] Deleted game {game_id[:3]} from database")
                self.delete_game(game_id)
            return game_end_res

            
        @self.app.after_request
        def identify_server(response):
            response.headers.set(
                "server", "Battlesnake"
            )
            return response
    
    def delete_game(self, game_id):
        del self.games[game_id]

    def start_server(self):
        host = "0.0.0.0"
        port = int(os.environ.get("PORT", "8000"))

        logging.getLogger("werkzeug").setLevel(logging.ERROR)

        self.create_endpoints()
        @self.app.route("/ping")
        def ping():
            return "pong"

        self.app.run(host=host, port=port, debug=True)

network = NetworkManager()

