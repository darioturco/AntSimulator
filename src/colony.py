import numpy as np
from src.ant import Ant
from src.marks import MarkField

render_marks = True

FOOD_PER_NEW_ANT = 5    # every this many food units delivered, the colony gets a new ant
MAX_POPULATION = 300
PRUNE_EVERY = 50        # expired marks are ignored at once and dropped from memory this often

class Colony(object):
    def __init__(self, world, pos, color, radius=20, initial_population=20, name=''):
        self.world = world
        self.pos = pos
        self.color = color
        self.name = name
        self.population = initial_population
        self.radius = radius
        self.no_food_marks = MarkField()
        self.food_marks = MarkField()
        self.food_fade_mark_time = 500
        self.colony_fade_mark_time = 500
        self.food_delivered = 0

        # create ants population (around the colony, never inside an obstacle)
        limit = np.array(world.size) - 1e-3
        self.ants = []
        for _ in range(self.population):
            p = np.clip(np.array(self.pos) + np.random.normal(size=2) * self.radius, 0, limit)
            if world.is_blocked(p):
                p = np.array(self.pos, dtype=float)
            self.ants.append(Ant(self, p))

    def deliver_food(self):
        """An ant brought food home: every FOOD_PER_NEW_ANT units the colony grows."""
        self.food_delivered += 1
        if self.food_delivered % FOOD_PER_NEW_ANT == 0 and len(self.ants) < MAX_POPULATION:
            self.ants.append(Ant(self, np.array(self.pos, dtype=float)))

    def step(self):
        for a in self.ants:
            a.step()

        if self.world.steps % PRUNE_EVERY == 0:
            self.food_marks.prune(self.world.steps)
            self.no_food_marks.prune(self.world.steps)

    def render(self, draw_circle, plot_points):
        # Render the colony
        draw_circle(self.color, self.pos, self.radius)

        # Render all marks
        now = self.world.steps
        if render_marks:
            plot_points(self.clear_color(4), self.no_food_marks.positions(now))
            plot_points(self.clear_color(2), self.food_marks.positions(now))

        # Render all ants
        if self.ants:
            plot_points(self.color, np.array([a.pos for a in self.ants]))

    def clear_color(self, factor):
        return (self.color[0] // factor, self.color[1] // factor, self.color[2] // factor)

    def is_blocked(self, pos):
        return self.world.is_blocked(pos)

    def add_mark(self, with_food, pos):
        x, y = int(pos[0]), int(pos[1])
        if with_food:
            self.food_marks.add(x, y, self.world.steps + self.food_fade_mark_time)
        else:
            self.no_food_marks.add(x, y, self.world.steps + self.colony_fade_mark_time)

    def is_over_food(self, pos):
        return self.world.is_over_food(pos)

    def is_in_colony(self, pos):
        return np.sum((self.pos - pos) ** 2) < self.radius ** 2

    def get_food_direction(self, pos):
        best = self.food_marks.oldest_offset(int(pos[0]), int(pos[1]), 10, self.world.steps)
        return np.zeros(2) if best is None else self.normalize(best)

    def get_colony_direction(self, pos):
        if np.sum((self.pos - pos) ** 2) < (self.radius ** 2) * 100:
            return self.normalize((self.pos[0] - pos[0], self.pos[1] - pos[1]))

        best = self.no_food_marks.oldest_offset(int(pos[0]), int(pos[1]), 50, self.world.steps)
        return np.zeros(2) if best is None else self.normalize(best)

    def normalize(self, direction):
        norm = np.sqrt(direction[0] ** 2 + direction[1] ** 2)
        if norm == 0:
            return np.zeros(2)
        return np.array([direction[0] / norm, direction[1] / norm])
