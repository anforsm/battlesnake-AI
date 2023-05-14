from snake import Snake, ControllableSnake
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
        return self.snake == None and not self.food and not self.hazard
    
    def is_food(self):
        return self.food == True
    
    def is_safe(self):
        return self.snake == None and not self.hazard
    
    def clear(self):
        self.set_food(False)
        self.set_hazard(False)
        self.set_snake(None)
        self.set_color(None)
        self.set_closest_snakes(None, None)
    
    def copy(self):
        new_cell = Cell(self.x, self.y)
        new_cell.set_food(self.food)
        new_cell.set_hazard(self.hazard)
        new_cell.set_snake(self.snake, self.is_snake_head)
        new_cell.color = self.color
        new_cell.closest_snakes = self.closest_snakes
        new_cell.closest_snake_distance = self.closest_snake_distance
        return new_cell





class Board:
    def __init__(self, width, height, our_snakes, all_snakes):
        self.width = width
        self.height = height
        self.snakes = []
        self.snake_map = {}

        self.create_cells()
        self.our_snakes = our_snakes
        self.create_snakes(all_snakes)

        self.save_replay = False
    
    # Check if a given cell is safe to move into
    def is_safe(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.cells[x][y].is_safe() 
    
    # Draw all cells
    def create_cells(self):
        self.cells = []
        for x in range(self.width):
            self.cells.append([])
            for y in range(self.height):
                self.cells[x].append(Cell(x, y))
    
    def clear_cells(self):
        for x in range(self.width):
            for y in range(self.height):
                self.cells[x][y].clear()
    
    def create_snakes(self, snakes):
        for snake in snakes:
            if isinstance(snake, Snake):
                if snake.client_id in [s.client_id for s in self.our_snakes]:
                    snake_obj = [s for s in self.our_snakes if s.client_id == snake.client_id][0]
                    snake_id = snake.client_id
                else:
                    snake_obj = snake
                    snake_id = snake.client_id
            else:
                snake_id = snake["id"]
                if snake_id in [s.client_id for s in self.our_snakes]:
                    snake_obj = [s for s in self.our_snakes if s.client_id == snake_id][0]
                else:
                    snake_obj = Snake()
                    snake_obj.client_id = snake_id

            self.snakes.append(snake_obj)
            self.snake_map[snake_id] = snake_obj 
    
    def update_snake_position(self, snake_state):
        for body_part in snake_state["body"]:
            snake_id = snake_state["id"]
            snake = self.snake_map[snake_id]

            is_head = body_part == snake_state["head"]
            self.cells[body_part["x"]][body_part["y"]].set_snake(snake, is_head)

    
    def update_state(self, board_state):
        self.clear_cells()
        for food in board_state["food"]:
            self.cells[food["x"]][food["y"]].set_food(True)
        
        for hazard in board_state["hazards"]:
            self.cells[hazard["x"]][hazard["y"]].set_hazard(True)
        
        updated_snakes = []
        for snake in board_state["snakes"]:
            self.update_snake_position(snake)
            snake_id = snake["id"]
            self.snake_map[snake_id].update_state(snake)
            updated_snakes.append(snake_id)
        
        for snake in self.snakes:
            if snake.client_id not in updated_snakes:
                snake.kill()
        
        self.calculate_closest_snake()
    
    def calculate_closest_snake(self):
        for col in self.cells:
            for cell in col:
                closest_snakes, closest_distance = self.get_closest_snake(cell.x, cell.y)
                cell.set_closest_snakes(closest_snakes, closest_distance)

    
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
    
    def save_to_img(self, turn, res):
        from PIL import Image, ImageDraw

        if res == "high":
            cell_size = 50
        elif res == "medium":
            cell_size = 25
        else:
            cell_size = 10

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
        
        # flip image to match coordinate system
        #img = img.transpose(Image.FLIP_TOP_BOTTOM) 

        img.save(f'./board/board_{turn}.png')
    
    def create_gif(self):
        import imageio
        images = []
        files = os.listdir("board")
        files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        for filename in files:
            images.append(imageio.imread("board/"+filename))
        imageio.mimsave('board.gif', images)
    
    def copy(self):
        new_board = Board(self.width, self.height, self.our_snakes, self.snakes)
        for x in range(self.width):
            for y in range(self.height):
                new_board.cells[x][y] = self.cells[x][y].copy()
        return new_board


