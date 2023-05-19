import math
import board

class SnakeNetworkManager():
    def __init__(self, snake):
        self.snake = snake
    
    def on_info(self):
        return self.snake.on_info()
    
    def on_start(self, game_state):
        self.snake.on_start(game_state)
        return "ok"
    
    def on_move(self, game_state):
        return self.snake.on_move(game_state)
    
    def on_end(self, game_state):
        self.snake.on_end(game_state)
        return "ok"

class Snake():
    def __init__(self, client_id):
        self.client_id = client_id 
        self.is_enemy = True 
        self.is_dead = False
        self.body = []
        self.head = None
        self.tail = None
    
    def place_on_board(self, board):
        self.board = board
        self.board.add_snake(self)


    def update_state(self, snake_info):
        self.health = snake_info["health"]
        self.length = snake_info["length"]

        self.body = [self.board.get_cell(cell["x"], cell["y"]) for cell in snake_info["body"]]
        self.tail = self.body[-1]
        self.head = self.board.get_cell(snake_info["head"]["x"], snake_info["head"]["y"])

        self.color = snake_info["customizations"]["color"]

        self.board.place_snake(self)
    
    def move(self, direction):
        if self.is_dead:
            return
        coordinate_offset = {
            "up": (0, 1),
            "down": (0, -1),
            "left": (-1, 0),
            "right": (1, 0)
        }[direction]
        self.head.is_snake_head = False
        # move head in direction
        new_head = self.board.get_cell(self.head.x + coordinate_offset[0], self.head.y + coordinate_offset[1])
        if new_head is None or new_head.is_occupied():
            self.kill()
            return
        self.body.insert(0, new_head)
        self.head = new_head 
        new_head.set_snake(self, True)
        if not self.head.is_food():
            self.body.pop()
            self.tail.clear_snake_info()
            self.tail = self.body[-1]

    
    def kill(self):
        if self.body is not None:
            for cell in self.body:
                cell.clear_snake_info()
        self.is_dead = True
        self.length = 0
        self.health = 0
        self.head = None
        self.body = None
        self.tail = None
    
    def get_distance_to(self, x, y):
        return abs(self.head.x - x) + abs(self.head.y - y)
    
    def get_head_cell(self, board):
        return board.get_cell(self.head["x"], self.head["y"])
    
    def get_moves_without_future_death(self, prediction_depth=10):
        moves_without_death = []
        for move in ["up", "down", "left", "right"]:
            if len(self.alternative_futures(move, max_depth=prediction_depth)) >= prediction_depth:
                moves_without_death.append(move)
        return moves_without_death


    
    # returns how many moves the snake can make before it dies
    def alternative_futures(self, direction, move_history = None, max_depth=10):
        if move_history is None:
            move_history = []

        depth = len(move_history)
        if depth > max_depth:
            return move_history
        new_snake = self.simulate_move(direction)
        if new_snake.is_dead:
            return move_history
        new_history = move_history + [new_snake.board]

        alternate_histories = []
        free_moves = new_snake.get_free_moves()
        for move in free_moves:
            alternate_history = new_snake.alternative_futures(move, new_history[:])
            if len(alternate_history) > max_depth:
                return alternate_history
            alternate_histories.append(alternate_history)

        if len(alternate_histories) == 0:
            return move_history + [new_snake.board]

        best_history = max(alternate_histories, key=lambda x: len(x))
        return best_history
    
    def get_free_moves(self):
        moves = []
        for move, offset in zip(["up", "down", "left", "right"], [(0, 1), (0, -1), (-1, 0), (1, 0)]):
            next_head_pos = (self.head.x + offset[0], self.head.y + offset[1])
            next_head_cell = self.board.get_cell(next_head_pos[0], next_head_pos[1])
            if next_head_cell is not None and not next_head_cell.is_occupied():
                moves.append(move)
        return moves
    
    def simulate_move(self, direction):
        new_board = self.board.copy()
        new_snake = new_board.get_snake(self.client_id)
        new_snake.move(direction)
        return new_snake


    
    def __eq__(self, other):
        return self.client_id == other.client_id
    
    def copy_to_board(self, board, new_snake=None):
        if new_snake is None:
            new_snake = Snake(self.client_id)

        new_snake.is_enemy = self.is_enemy
        new_snake.is_dead = self.is_dead
        new_snake.health = self.health
        new_snake.length = self.length
        if not new_snake.is_dead:
            new_snake.body = [board.get_cell(cell.x, cell.y) for cell in self.body]
            new_snake.tail = board.get_cell(self.tail.x, self.tail.y)
            new_snake.head = board.get_cell(self.head.x, self.head.y)
        new_snake.color = self.color
        new_snake.place_on_board(board)
        return new_snake

# A snake that is controlled by us
# The snake should not be copied
class ControllableSnake():
    def __init__(self, id, name):
        self.snake = None
        self.id = id
        self.name = name
        self.net = SnakeNetworkManager(self)
        self.is_enemy = False
        self.client_id = None

    # info is called when you create your Battlesnake on play.battlesnake.com
    # and controls your Battlesnake's appearance
    # TIP: If you open your Battlesnake URL in a browser you should see this data
    def on_info(self):
        return {
            "apiversion": "1",
            "author": "Anton Forsman & Nils Odin",
            "color": self.team.color,
            "head": "default",
            "tail": "default",
        }

    # start is called when your Battlesnake begins a game
    def on_start(self, game_state):
        self.client_id = game_state["you"]["id"]
        print("[INFO] Initialized snake " + str(self.id))
        self.team.initialize_team(game_state)
        return

    # end is called when your Battlesnake finishes a game
    def on_end(self, game_state):
        self.team.end_team(self, game_state)
        return
    
    # move is called on every turn and returns your next move
    # Valid moves are "up", "down", "left", or "right"
    # See https://docs.battlesnake.com/api/example-move for available data
    def on_move(self, game_state):
        self.team.update_state(game_state)
        self.team.calculate_moves()
        move = self.team.get_move(self)
        return {"move": move}
    
    def get_safe_moves(self, board):
        if self.snake.is_dead:
            return []

        safe_moves = []
        for move, offset in zip(["up", "down", "left", "right"], [(0, 1), (0, -1), (-1, 0), (1, 0)]):
            next_head_pos = (self.snake.head.x + offset[0], self.snake.head.y + offset[1])
            if board.b.is_safe(*next_head_pos):
                adjacent_cells = [
                    (next_head_pos[0]+1, next_head_pos[1]),
                    (next_head_pos[0]-1, next_head_pos[1]), 
                    (next_head_pos[0], next_head_pos[1]+1), 
                    (next_head_pos[0], next_head_pos[1]-1)
                ]
                adjacent_cells = [board.b.get_cell(*cell) for cell in adjacent_cells]
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
        if self.snake.is_dead:
            return closest_food
        for row in board.b.cells:
            for cell in row:
                if cell.is_food():
                    cell_distance = abs(self.snake.head.x - cell.x) + abs(self.snake.head.y - cell.y)
                    if(cell_distance < closest_food["distance"]):
                        closest_food["cell"] = cell
                        closest_food["distance"] = cell_distance
        return closest_food
    
    def get_direction_of_food(self, board):
        closest_food = self.get_closest_food_pos(board)["cell"]
        if closest_food is None:
            return None
        else:
            return board.b.get_direction_between_cells(self.snake.head, closest_food)

    def copy_to_board(self, board):
        new_snake = ControllableSnake(self.id, self.name)
        new_snake.net 
        new_snake = super().copy_to_board(board, new_snake=new_snake)
        return new_snake
