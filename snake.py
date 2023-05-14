import math
import board

class SnakeNetworkManager():
    def __init__(self, snake):
        self.snake = snake
    
    def on_info(self):
        return self.snake.info()
    
    def on_start(self, game_state):
        self.snake.start(game_state)
        return "ok"
    
    def on_move(self, game_state):
        return self.snake.move(game_state)
    
    def on_end(self, game_state):
        self.snake.end(game_state)
        return "ok"

class Snake():
    def __init__(self):
        self.client_id = None
        self.is_enemy = True 
        self.is_dead = False
    
    def place_on_board(self, board):
        self.board = board
        self.board.add_snake(self)


    def update_state(self, snake_info):
        self.health = snake_info["health"]
        self.length = snake_info["length"]

        self.body = [self.board.get_cell(cell["x"], cell["y"]) for cell in snake_info["body"]]
        self.tail = snake_info["body"][-1]
        self.head = self.board.get_cell(snake_info["head"]["x"], snake_info["head"]["y"])

        self.color = snake_info["customizations"]["color"]
    
    def kill(self):
        self.is_dead = True
        self.length = 0
        self.health = 0
        self.head = None
        self.body = None
    
    def get_distance_to(self, x, y):
        return abs(self.head["x"] - x) + abs(self.head["y"] - y)
    
    def get_head_cell(self, board):
        return board.get_cell(self.head["x"], self.head["y"])
    
    def __eq__(self, other):
        return self.client_id == other.client_id
    
    def copy_to_board(self, board):
        new_snake = Snake()
        new_snake.client_id = self.client_id
        new_snake.is_enemy = self.is_enemy
        new_snake.is_dead = self.is_dead
        new_snake.health = self.health
        new_snake.length = self.length
        new_snake.body = [board.get_cell(cell["x"], cell["y"]) for cell in self.body]
        new_snake.tail = board.get_cell(self.tail["x"], self.tail["y"])
        new_snake.head = board.get_cell(self.head["x"], self.head["y"])
        new_snake.color = self.color
        board.add_snake(new_snake)
        return new_snake




class ControllableSnake(Snake):
    def __init__(self, id, name):
        super().__init__()
        self.id = id
        self.name = name
        self.net = SnakeNetworkManager(self)
        self.is_enemy = False

    # info is called when you create your Battlesnake on play.battlesnake.com
    # and controls your Battlesnake's appearance
    # TIP: If you open your Battlesnake URL in a browser you should see this data
    def info(self):
        return {
            "apiversion": "1",
            "author": "Anton Forsman & Nils Odin",
            "color": self.team.color,
            "head": "default",
            "tail": "default",
        }
      
    # start is called when your Battlesnake begins a game
    def start(self, game_state):
        self.client_id = game_state["you"]["id"]
        print("[INFO] Initialized snake " + str(self.id))
        self.team.initialize_team(game_state)
        return

    # end is called when your Battlesnake finishes a game
    def end(self, game_state):
        self.team.end_team(self, game_state)
        return
    
    # move is called on every turn and returns your next move
    # Valid moves are "up", "down", "left", or "right"
    # See https://docs.battlesnake.com/api/example-move for available data
    def move(self, game_state):
        self.team.update_state(game_state)
        self.team.calculate_move()
        move = self.team.get_move(self)
        return {"move": move}
    
    def get_safe_moves(self, board):
        if self.is_dead:
            return []

        safe_moves = []
        for move, offset in zip(["up", "down", "left", "right"], [(0, 1), (0, -1), (-1, 0), (1, 0)]):
            next_head_pos = (self.head["x"] + offset[0], self.head["y"] + offset[1])
            if board.is_safe(*next_head_pos):
                adjacent_cells = [
                    (next_head_pos[0]+1, next_head_pos[1]),
                    (next_head_pos[0]-1, next_head_pos[1]), 
                    (next_head_pos[0], next_head_pos[1]+1), 
                    (next_head_pos[0], next_head_pos[1]-1)
                ]
                adjacent_cells = [board.get_cell(*cell) for cell in adjacent_cells]
                adjacent_cells = [cell for cell in adjacent_cells if cell is not None]

                adjacent_cell_has_enemy_snake = False
                # check any of the adjacent cells for other snakes
                for cell in adjacent_cells:
                    if cell.is_snake_head and cell.snake != self:
                        adjacent_cell_has_enemy_snake = True
                        break

                if not adjacent_cell_has_enemy_snake:
                    safe_moves.append(move)

        return safe_moves
    
    # finds the x,y-tuple where the closest food is located (manhattan distance)
    def get_closest_food_pos(self, board):
        # go through every cell and find all food (perhaps this should be precalculated in board for faster )
        closest_food = {"distance":math.inf, "cell":None}
        for row in board.cells:
            for cell in row:
                if cell.is_food():
                    cell_distance = abs(self.head["x"] - cell.x) + abs(self.head["y"] - cell.y)
                    if(cell_distance < closest_food["distance"]):
                        closest_food["cell"] = cell
                        closest_food["distance"] = cell_distance
        return closest_food
    
    def get_direction_of_food(self, board):
        closest_food = self.get_closest_food_pos(board)["cell"]
        if closest_food is None:
            return None
        else:
            return board.get_direction_between_cells(self.get_head_cell(board), closest_food)


    # TODO: 
    # 1. Make a copy of the current game state
    # 2. Calculate future gamestates with minimax and the heuristic
    # 3. 

    # TODO: 
    # Minimax is for 1v1 games, how can we adapt it for 2v2 snakes?
    # How can we make the 

    # The start of the minmax move finder
    def choose_move(self, game_state, depth):
        current_state = game_state
        temp_board = board.Board(self.team.board.width, self.team.board.height, self.team, self.team.snakes)
        temp_snake = Snake()
        best_move = None
        best_value = -math.inf

        for move in self.get_safe_moves:
            
            pass
            

    # An attempt at implementing minimax 
    def minimax(self, board, game_state, depth):
        # Base case 
        if depth == 0:
            return self.minimax_heuristic(self, board, game_state)
        
        # We are finding a maximum value move for our snake
        if not self.is_enemy:
            best_value = -math.inf
            for move in self.get_safe_moves:
                # TODO
                pass

            # TODO
            pass

        # Else, we are finding a minimum value move for our enemy snake
        else:
            # TODO
            pass

        

    # The heuristic function that decides if the move is "good" or "bad" for the snake,
    # used by the minimax algorithm
    def minimax_heuristic(self, board, game_state):
        
        return None