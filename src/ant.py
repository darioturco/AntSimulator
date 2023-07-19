import numpy as np

class Ant(object):
    def __init__(self, colony, pos):
        self.colony = colony
        self.pos = pos
        self.with_food = False
        self.vel = np.random.normal(size=2)
        self.freedom = np.random.random() / 10
        self.drop_mark = 10 + np.random.randint(-5, 5)
        self.drop_mark_count = 0

    def step(self):
        self.pos += self.vel + self.vel_noise() + self.road_direction()

        if self.colony.is_out_of_bounds(self.pos):
            self.pos -= 2 * self.vel
            self.vel = -self.vel

        self.drop_mark_count += 1
        if self.drop_mark_count >= self.drop_mark:
            self.drop_mark_count = 0
            self.colony.add_mark(self.with_food, self.pos)

        if self.with_food:
            # Check if the ant is in the colony
            if self.colony.is_in_colony(self.pos):
                self.with_food = False
                self.vel = -self.vel
        else:
            if self.colony.is_over_food(self.pos):
                self.with_food = True
                self.vel = -self.vel

    def vel_noise(self):
        return np.random.normal(size=2) / 2

    def road_direction(self):
        ### Completar
        return np.zeros(2)

    def render(self, color, draw_function):
        draw_function(color, self.pos, 1)
