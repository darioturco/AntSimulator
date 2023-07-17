import pygame
from src.colony import Colony

red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
colors = [red, green, blue, white]
pos = [(100, 100), (300, 100), (100, 300), (300, 300)]

class World(object):
    def __init__(self, size, colonies, initial_population, food):
        self.food = food
        self.size = size

        # Init pygame
        pygame.init()
        pygame.display.set_caption('Ants')
        self.window = pygame.display.set_mode(size)
        self.colonies = [Colony(self, pos[c], colors[c], initial_population) for c in range(colonies)]



    def step(self):
        for c in self.colonies:
            c.step()

    def draw_cicle(self, color, pos, radius):
        pygame.draw.circle(self.window, color, pos, radius)

    def draw_point(self, color, pos):
        self.window.fill(color, (pos, (1, 1)))

    def render(self):
        # Clear display
        self.window.fill((0,0,0))

        # Render the food
        for f in self.food:
            self.draw_point(green, f)



        # Render all colonies
        for c in self.colonies:
            c.render(self.draw_cicle)

        pygame.display.update()

    def is_out_of_bounds(self, pos):
        return (pos[0] < 0) or (pos[0] > self.size[0]) or \
                (pos[1] < 0) or (pos[1] > self.size[1])

    def is_over_food(self, pos):
        pos = tuple(pos.astype('int'))
        if pos in self.food:
            self.food.remove(pos)
            return True

        return False
