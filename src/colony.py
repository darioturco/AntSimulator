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
        self.food_fade_mark_time = 500
        self.colony_fade_mark_time = 500

        # create ants population
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
        # Render the colony
        draw_function(self.color, self.pos, self.radius)

        # Render all marks
        if render_marks:
            for m in self.no_food_marks:
                draw_function(self.clear_color(4), (m[0], m[1]), 1)

            for m in self.food_marks:
                #draw_function(self.clear_color(2), (m[0], m[1]), 1)
                draw_function((0, 100, 0), (m[0], m[1]), 1)

        # Render all ants
        for a in self.ants:
            a.render(self.color, draw_function)



    def clear_color(self, factor):
        return (self.color[0] // factor, self.color[1] // factor, self.color[2] // factor)

    def is_out_of_bounds(self, pos):
        return self.world.is_out_of_bounds(pos)

    def add_mark(self, with_food, pos):
        pos = pos.astype('int')
        if with_food:
            self.food_marks[tuple(pos)] = self.food_fade_mark_time
        else:
            self.no_food_marks[tuple(pos)] = self.colony_fade_mark_time

    def is_over_food(self, pos):
        return self.world.is_over_food(pos)

    def is_in_colony(self, pos):
        return np.sum((self.pos - pos) ** 2) < self.radius ** 2

    def get_food_direction(self, pos):
        pos = pos.astype('int')
        min = self.food_fade_mark_time + 1
        argmin = None
        r = 10
        for i in range(-r, r):
            for j in range(-r, r):
                aux_pos = (pos[0]+i, pos[1]+j)
                if (aux_pos in self.food_marks) and (self.food_marks[aux_pos] < min):
                    min = self.food_marks[aux_pos]
                    argmin = (i, j)

        return np.zeros(2) if argmin is None else self.normalize(argmin)

    def get_colony_direction(self, pos):
        if np.sum((self.pos - pos) ** 2) < (self.radius ** 2) * 100:
            return self.normalize((self.pos[0] - pos[0], self.pos[1] - pos[1]))

        #return np.zeros(2) ### Borrar

        pos = pos.astype('int')
        min = self.colony_fade_mark_time + 1
        argmin = None
        r = 50
        for i in range(-r, r):
            for j in range(-r, r):
                aux_pos = (pos[0]+i, pos[1]+j)
                if (aux_pos in self.no_food_marks) and (self.no_food_marks[aux_pos] < min):
                    min = self.no_food_marks[aux_pos]
                    argmin = (i, j)

        return np.zeros(2) if argmin is None else self.normalize(argmin)


    def normalize(self, direction):
        norm = np.sqrt(direction[0] ** 2 + direction[1] ** 2)
        return np.array([direction[0] / norm, direction[1] / norm])
