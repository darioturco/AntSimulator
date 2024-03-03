import math
import numpy as np

class Ant(object):
    def __init__(self, colony, pos,  vel=None):
        self.colony = colony
        self.pos = pos
        if vel is None:
            vel = np.random.normal(size=2)
        self.vel = vel

        self.with_food = False
        self.freedom = np.random.random() / 10
        self.drop_mark = 10 + np.random.randint(-5, 5)
        self.drop_mark_count = 0
        self.change_direction = 8
        self.change_direction_count = 0

    def step(self):
        self.change_direction_count += 1
        if self.change_direction_count >= self.change_direction:
            self.change_direction_count = 0
            new_vel = self.road_direction()
            if np.linalg.norm(new_vel) > 0:
                self.vel = new_vel

        self.pos += self.vel + self.vel_noise()

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
        if self.with_food:
            return np.random.normal(size=2) / 2
        else:
            return np.random.normal(size=2)

    def road_direction(self):
        if self.with_food:
            return self.colony.get_colony_direction(self.pos)
        else:
            return self.colony.get_food_direction(self.pos)

    def render(self, color, draw_function):
        draw_function(color, self.pos, 1)
