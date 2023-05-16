from IPython.display import display_png
from snake import Snake, ControllableSnake
from PIL import Image, ImageDraw
import itertools
import os


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.set_food(False)
        self.set_hazard(False)
        self.set_snake(None, False)
        self.color = None
        self.closest_snakes = None
        self.closest_snake_distance = None
    
    def set_food(self, food):
        self.food = food 
    
    def set_hazard(self, hazard):
        self.hazard = hazard
    
    def set_snake(self, snake, is_snake_head=False):
        self.snake = snake
        self.is_snake_head = is_snake_head

    def set_color(self, color):
        self.color = color
    
    def set_closest_snakes(self, snakes, distance):
        self.closest_snakes = snakes
        self.closest_snake_distance = distance
    
    def is_empty(self):
        return self.snake is None and not self.food and not self.hazard
    
    def is_food(self):
        return self.food == True
    
    def is_safe(self):
        return self.snake is None and not self.hazard
    
    def is_occupied(self):
        return self.snake is not None
    
    def clear_snake_info(self):
        self.set_snake(None)
        self.is_snake_head = False
        self.set_closest_snakes(None, None)
        return self
    
    def clear(self):
        self.set_food(False)
        self.set_hazard(False)
        self.set_snake(None)
        self.set_color(None)
        self.set_closest_snakes(None, None)
        return self
    
    def copy(self):
        new_cell = Cell(self.x, self.y)
        new_cell.set_food(self.food)
        new_cell.set_hazard(self.hazard)
        new_cell.set_snake(self.snake, self.is_snake_head)
        new_cell.color = self.color
        new_cell.closest_snakes = self.closest_snakes
        new_cell.closest_snake_distance = self.closest_snake_distance
        return new_cell
    
    def __repr__(self):
        return f"Cell({self.x}, {self.y})"
    
# A board that is completely separated from snake teams and the API
class GeneralBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.snakes = []
        self.snake_map = {}

        self.create_cells()
        self.save_replay = False
    
    def clear_cells(self):
        for x in range(self.width):
            for y in range(self.height):
                self.cells[x][y].clear()
    
    def is_safe(self, x, y):
        if not self.is_valid_cell(x, y):
            return False
        return self.cells[x][y].is_safe()

    def get_direction_between_cells(self, cell1, cell2):
        directions = []
        if cell1.x < cell2.x:
            directions.append("right")
        elif cell1.x > cell2.x:
            directions.append("left")
        if cell1.y < cell2.y:
            directions.append("up")
        elif cell1.y > cell2.y:
            directions.append("down")
        return directions
    
    def get_cell(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        return self.cells[x][y]
    
    def is_valid_cell(self, x, y):
        return x >= 0 and x < self.width and y >= 0 and y < self.height
    
    def create_cells(self):
        self.cells = []
        self.all_cells = []
        for x in range(self.width):
            self.cells.append([])
            for y in range(self.height):
                self.cells[x].append(Cell(x, y))
                self.all_cells.append(self.cells[x][y])
    
    # adds a snake to the board
    # and places it on the correct cells
    def add_snake(self, snake):
        self.snakes.append(snake)
        self.snake_map[snake.client_id] = snake
        self.place_snake(snake)
    
    # places a snake on the correct cells
    def place_snake(self, snake):
        self.clear_snake(snake)
        if snake.is_dead:
            return
        for cell in snake.body:
            cell.set_snake(snake)
            if snake.head == cell:
                cell.is_snake_head = True
    
    # unpplaces a snakes from the board
    def clear_snake(self, snake):
        for cell in self.all_cells:
            if cell.snake and cell.snake == snake:
                cell.clear_snake_info()

    # places all a board's snakes on the correct cells
    def place_snakes(self):
        for snake in self.snakes:
            self.place_snake(snake)
            
    
    # returns a list of boards that result from all possible moves
    def get_possible_subboards(self):
        possible_subboards = []
        # generate all permutations of snake moves
        directions = ["up", "down", "left", "right"]
        snakes_to_move = [snake for snake in self.snakes if not snake.is_dead]
        permutations = itertools.product(directions, repeat=len(snakes_to_move))
        for permutation in permutations:
            new_board = self.copy()
            for i in range(len(permutation)):
                new_snake = new_board.get_snake(snakes_to_move[i].client_id)
                new_board.move_snake(new_snake, permutation[i])
            possible_subboards.append(new_board)
        return possible_subboards

    # returns a list of closest snakes to a coordinate, and the distance
    def get_closest_snake(self, x, y):
        closest_snakes = [] 
        closest_distance = 999999999
        for snake in self.snakes:
            if snake.is_dead:
                continue

            distance = snake.get_distance_to(x, y)
            if distance == closest_distance:
                closest_snakes.append(snake)
            if distance < closest_distance:
                closest_snakes = [snake]
                closest_distance = distance
        return closest_snakes, closest_distance

    # sets the closest snake to each cell
    def calculate_closest_snake(self):
        for col in self.cells:
            for cell in col:
                closest_snakes, closest_distance = self.get_closest_snake(cell.x, cell.y)
                cell.set_closest_snakes(closest_snakes, closest_distance)
    
    def get_snake(self, client_id):
        for snake in self.snakes:
            if snake.client_id == client_id:
                return snake
        return None
    
    def move_snake(self, snake, direction):
        snake.move(direction)
        self.place_snakes()
    
    def copy(self, new_board=None):
        if new_board is None:
            new_board = GeneralBoard(self.width, self.height)

        new_board.cells = [[cell.copy().clear_snake_info() for cell in row] for row in self.cells]
        new_board.all_cells = [cell.copy().clear_snake_info() for cell in self.all_cells]
        new_board.snakes = []
        new_board.snake_map = {}
        for snake in self.snakes:
            snake.copy_to_board(new_board)
        return new_board
    
    def convert_to_image(self, cell_size=25):
        img = Image.new('RGB', (self.width*cell_size, self.height*cell_size), color = 'white')
        draw = ImageDraw.Draw(img)

        # draw grid
        for x in range(self.width):
            for y in range(self.height):
                draw.rectangle((x*cell_size, y*cell_size, x*cell_size+cell_size, y*cell_size+cell_size), fill='white', outline='black')
        
        # draw optional colors
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].color:
                    draw.rectangle((x*cell_size, y*cell_size, x*cell_size+cell_size, y*cell_size+cell_size), fill=self.cells[x][y].color, outline='black')
        
        for x in range(self.width):
            for y in range(self.height):
                # fill in color of closest snake, but slightly lighter
                if self.cells[x][y].closest_snakes is not None and len(self.cells[x][y].closest_snakes) > 0:
                    snakes_are_all_same_team = True
                    team = self.cells[x][y].closest_snakes[0].is_enemy
                    for snake in self.cells[x][y].closest_snakes:
                        if not snake.is_enemy == team:
                            snakes_are_all_same_team = False
                            break

                    if snakes_are_all_same_team: 
                        shade = 0.7
                        color = self.cells[x][y].closest_snakes[0].color
                        color = color.lstrip('#')
                        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                        new_rgb = tuple([int((255 - rgb[i]) * shade + rgb[i]) for i in range(3)])
                        new_color = '#%02x%02x%02x' % new_rgb
                        draw.rectangle((x*cell_size, y*cell_size, x*cell_size+cell_size, y*cell_size+cell_size), fill=new_color, outline='black')

                # # write closest snake distance to cell
                # if self.cells[x][y].closest_snake_distance is not None:
                #     draw.text((x*cell_size+0.1*cell_size, y*cell_size+0.1*cell_size), str(self.cells[x][y].closest_snake_distance), fill='black')
                

        
        # draw food, small green circle
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].food:
                    draw.ellipse((x*cell_size+0.2*cell_size, y*cell_size+0.2*cell_size, x*cell_size+0.8*cell_size, y*cell_size+0.8*cell_size), fill='green', outline='green')
        
        # draw hazards, small red circle
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].hazard:
                    draw.ellipse((x*cell_size+0.2*cell_size, y*cell_size+0.2*cell_size, x*cell_size+0.8*cell_size, y*cell_size+0.8*cell_size), fill='red', outline='red')

        # draw snakes, according to their color, in squares slightly smaller than grid size
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].snake:
                    snake = self.cells[x][y].snake
                    color = snake.color
                    if self.cells[x][y].is_snake_head:
                        draw.rectangle((x*cell_size+0.1*cell_size, y*cell_size+0.1*cell_size, x*cell_size+0.9*cell_size, y*cell_size+0.9*cell_size), fill=color, outline=color)
                    else:
                        draw.rectangle((x*cell_size+0.2*cell_size, y*cell_size+0.2*cell_size, x*cell_size+0.8*cell_size, y*cell_size+0.8*cell_size), fill=color, outline=color)

        return img

    
    def _repr_png_(self):
        return display_png(self.convert_to_image(cell_size=25))

    def save_to_img(self, path, turn, res):

        if res == "high":
            cell_size = 50
        elif res == "medium":
            cell_size = 25
        else:
            cell_size = 10
        
        img = self.convert_to_image(cell_size=cell_size)

        img.save(f'./{path}/board_{turn}.png')

    def create_gif(self, path):
        import imageio
        images = []
        files = os.listdir(path)
        files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        for filename in files:
            images.append(imageio.imread(path+"/"+filename))
        # enable infinte loop
        imageio.mimsave(path+"/" + '_board.gif', images, loop=0)


# A board that is aware of its own snake team, and can update based on API data
# this board should not be copied
class Board():
    def __init__(self, width, height, our_snakes, all_snakes_json):
        self.b = GeneralBoard(width, height)

        self.our_snakes = our_snakes
        self.our_snakes_map = {}
        for snake in our_snakes:
            snake_id = snake.client_id
            self.our_snakes_map[snake_id] = snake

        self.create_snakes(all_snakes_json)
    
    # creates snakes and places them on board
    def create_snakes(self, snakes_json):
        for snake_json in snakes_json:
            snake_id = snake_json["id"]

            snake_obj = Snake(snake_id)
            snake_obj.place_on_board(self.b)
            snake_obj.update_state(snake_json)

            if snake_id in self.our_snakes_map:
                self.our_snakes_map[snake_id].snake = snake_obj

    
    def set_snake_position(self, snake_state):
        snake_id = snake_state["id"]
        snake = self.b.snake_map[snake_id]

        for body_part in snake_state["body"]:

            is_head = body_part == snake_state["head"]
            self.b.cells[body_part["x"]][body_part["y"]].set_snake(snake, is_head)

    
    def update_state(self, board_state):
        self.b.clear_cells()
        for food in board_state["food"]:
            self.b.cells[food["x"]][food["y"]].set_food(True)
        
        for hazard in board_state["hazards"]:
            self.b.cells[hazard["x"]][hazard["y"]].set_hazard(True)
        
        updated_snakes = []
        for snake in board_state["snakes"]:
            self.set_snake_position(snake)
            updated_snakes.append(snake["id"])
            snake_obj = self.b.snake_map[snake["id"]]
            snake_obj.update_state(snake)
        
        for snake in self.b.snakes:
            if snake.client_id not in updated_snakes:
                snake.kill()
        
        self.b.calculate_closest_snake()
    
    def copy(self):
        new_board = Board(self.width, self.height, self.our_snakes, [])
        new_board.our_snakes = self.our_snakes
        new_board = super().copy(new_board=new_board)
        return new_board


