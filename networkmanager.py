from flask import Flask
from flask import request
import os
import logging

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
            return self.snake_map[snake_id].net.on_info()
        
        @self.app.post("/<snake_id>/start/")
        def on_start(snake_id):
            return self.snake_map[snake_id].net.on_start(request.get_json())
        
        @self.app.post("/<snake_id>/move/")
        def on_move(snake_id):
            print("[INFO] got request for move")
            return self.snake_map[snake_id].net.on_move(request.get_json())
        
        @self.app.post("/<snake_id>/end/")
        def on_end(snake_id):
            return self.snake_map[snake_id].net.on_end(request.get_json())

            
        @self.app.after_request
        def identify_server(response):
            response.headers.set(
                "server", "battlesnake/github/starter-snake-python"
            )
            return response
    
    def start_server(self):
        host = "0.0.0.0"
        port = int(os.environ.get("PORT", "8000"))

        logging.getLogger("werkzeug").setLevel(logging.ERROR)

        self.create_endpoints()
        @self.app.route("/ping")
        def ping():
            return "pong"
        
        # log every request
        @self.app.after_request
        def log_request(response):
            print("[INFO] got request")
            return response

        self.app.run(host=host, port=port, debug=True)

network = NetworkManager()

