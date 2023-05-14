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


    def update_state(self, snake_info):
        self.health = snake_info["health"]
        self.length =snake_info["length"]
        self.body = snake_info["body"]
        self.head = snake_info["head"] 
        self.color = snake_info["customizations"]["color"]
    
    def kill(self):
        self.is_dead = True
        self.length = 0
        self.health = 0
        self.head = None
        self.body = None
    
    def get_distance_to(self, x, y):
        return abs(self.head["x"] - x) + abs(self.head["y"] - y)



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
        self.team.initialize_team(game_state)
        return

    # end is called when your Battlesnake finishes a game
    def end(self, game_state):
        self.team.end_team(self)
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

                safe_moves.append(move)
                continue

                # TODO: Two snakes could both see this cell as safe and move into it in the same turn, causing them to die
                # The code below here attempts to solve that but doesnt work for some reason!
                 
                # Find the 4 adjecent cells to "next_head_pos"
                adjecent_right = (next_head_pos[0]+1, next_head_pos[1])
                adjecent_left  = (next_head_pos[0]-1, next_head_pos[1])
                adjecent_up    = (next_head_pos[0], next_head_pos[1]+1)
                adjecent_down  = (next_head_pos[0], next_head_pos[1]-1)

                # check the adjecent cells for other snakes (if we are going up, we dont check if adjecent_bottom is safe since we come from there)
                if move == "up" and board.is_safe(*adjecent_right) and board.is_safe(*adjecent_left) and board.is_safe(*adjecent_up):
                    safe_moves.append(move)
                
                elif move == "down" and board.is_safe(*adjecent_right) and board.is_safe(*adjecent_left) and board.is_safe(*adjecent_down):
                    safe_moves.append(move)

                elif move == "left" and board.is_safe(*adjecent_left) and board.is_safe(*adjecent_up) and board.is_safe(*adjecent_down):
                    safe_moves.append(move)
        
                elif move == "right" and board.is_safe(*adjecent_right) and board.is_safe(*adjecent_up) and board.is_safe(*adjecent_down):
                    safe_moves.append(move)
        return safe_moves
    
    # finds the x,y-tuple where the closest food is located (manhattan distance)
    def get_closest_food_pos(self, board):
        # go through every cell and find all food (perhaps this should be precalculated in board for faster )
        closestFood = {"distance":math.inf, "cell":None}
        for row in board.cells:
            for cell in row:
                if cell.is_food():
                    cell_distance = abs(self.head["x"] - cell.x) + abs(self.head["y"] - cell.y)
                    if(cell_distance < closestFood["distance"]):
                        closestFood["cell"] = cell
                        closestFood["distance"] = cell_distance
        return closestFood


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