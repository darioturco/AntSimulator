import numpy as np
from src.ant import Ant

render_marks = True

class Colony(object):
    def __init__(self, world, pos, color, initial_population=20):
        self.world = world
        self.pos = pos
        self.color = color
        self.population = initial_population
        self.radius = 20
        self.no_food_marks = {}
        self.food_marks = {}
        self.fade_mark_time = 32

        # create population ants
        self.ants = [Ant(self, (np.array(self.pos) + np.random.normal(size=2) * self.radius)) for _ in range(self.population)]


    def step(self):
        for a in self.ants:
            a.step()

        for v in list(self.food_marks.keys()):
            self.food_marks[v] -= 1
            if self.food_marks[v] <= 0:
                del self.food_marks[v]

        for v in list(self.no_food_marks.keys()):
            self.no_food_marks[v] -= 1
            if self.no_food_marks[v] <= 0:
                del self.no_food_marks[v]




    def render(self, draw_function):
        # Render all ants
        for a in self.ants:
            a.render(self.color, draw_function)

        # Render all marks
        if render_marks:
            for m in self.no_food_marks:
                draw_function(self.clear_color(4), (m[0], m[1]), 1)

            for m in self.food_marks:
                #draw_function(self.clear_color(2), (m[0], m[1]), 1)
                draw_function((0, 100, 0), (m[0], m[1]), 1)

        # Render the colony
        draw_function(self.color, self.pos, self.radius)

    def clear_color(self, factor):
        return (self.color[0] // factor, self.color[1] // factor, self.color[2] // factor)

    def is_out_of_bounds(self, pos):
        return self.world.is_out_of_bounds(pos)

    def add_mark(self, with_food, pos):
        if with_food:
            self.food_marks[tuple(pos)] = self.fade_mark_time
        else:
            self.no_food_marks[tuple(pos)] = self.fade_mark_time

    def is_over_food(self, pos):
        return self.world.is_over_food(pos)

    def is_in_colony(self, pos):
        print(f'{self.pos} - {pos} -> {np.sum((self.pos - pos) ** 2)}')
        return np.sum((self.pos - pos) ** 2) < self.radius ** 2
