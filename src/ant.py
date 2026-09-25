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

        self.hits = 0               # hits received from enemy ants
        self.attacking = False      # set by the world when this ant is fighting this step

    def step(self):
        if self.attacking:
            # Busy fighting: no movement this step
            self.attacking = False
            return

        self.change_direction_count += 1
        if self.change_direction_count >= self.change_direction:
            self.change_direction_count = 0
            new_vel = self.road_direction()
            if np.linalg.norm(new_vel) > 0:
                self.vel = new_vel

        self.move(self.vel + self.vel_noise())

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

    def move(self, step):
        """Walk one step. Walls and obstacles are not crossed: the ant slides
        along them (bouncing the blocked component of its velocity) or, if it
        cannot move on either axis, turns around."""
        new_pos = self.pos + step
        if not self.colony.is_blocked(new_pos):
            self.pos = new_pos
            return

        x_pos = self.pos + np.array([step[0], 0.0])
        y_pos = self.pos + np.array([0.0, step[1]])
        if not self.colony.is_blocked(x_pos):
            self.pos = x_pos
            self.vel = np.array([self.vel[0], -self.vel[1]])
        elif not self.colony.is_blocked(y_pos):
            self.pos = y_pos
            self.vel = np.array([-self.vel[0], self.vel[1]])
        else:
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
        draw_function(color, self.pos)
