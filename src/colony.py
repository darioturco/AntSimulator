import numpy as np
from src.ant import Ant

render_marks = True

class Colony(object):
    def __init__(self, world, pos, color, radius=20, initial_population=20, name=''):
        self.world = world
        self.pos = pos
        self.color = color
        self.name = name
        self.population = initial_population
        self.radius = radius
        self.no_food_marks = {}
        self.food_marks = {}
        self.food_fade_mark_time = 500
        self.colony_fade_mark_time = 500

        # create ants population (around the colony, never inside an obstacle)
        limit = np.array(world.size) - 1e-3
        self.ants = []
        for _ in range(self.population):
            p = np.clip(np.array(self.pos) + np.random.normal(size=2) * self.radius, 0, limit)
            if world.is_blocked(p):
                p = np.array(self.pos, dtype=float)
            self.ants.append(Ant(self, p))

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

    def render(self, draw_circle, draw_small):
        # Render the colony
        draw_circle(self.color, self.pos, self.radius)

        # Render all marks
        if render_marks:
            for m in self.no_food_marks:
                draw_small(self.clear_color(4), m)

            for m in self.food_marks:
                draw_small(self.clear_color(2), m)

        # Render all ants
        for a in self.ants:
            a.render(self.color, draw_small)

    def clear_color(self, factor):
        return (self.color[0] // factor, self.color[1] // factor, self.color[2] // factor)

    def is_blocked(self, pos):
        return self.world.is_blocked(pos)

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

    def oldest_mark_offset(self, marks, pos, r):
        """Offset to the mark closest to expiring within a (2r x 2r) window, or None."""
        px, py = int(pos[0]), int(pos[1])
        best = None
        best_time = float('inf')
        for (mx, my), time_left in marks.items():
            dx, dy = mx - px, my - py
            if -r <= dx < r and -r <= dy < r and time_left < best_time:
                best_time = time_left
                best = (dx, dy)

        return best

    def get_food_direction(self, pos):
        best = self.oldest_mark_offset(self.food_marks, pos, 10)
        return np.zeros(2) if best is None else self.normalize(best)

    def get_colony_direction(self, pos):
        if np.sum((self.pos - pos) ** 2) < (self.radius ** 2) * 100:
            return self.normalize((self.pos[0] - pos[0], self.pos[1] - pos[1]))

        best = self.oldest_mark_offset(self.no_food_marks, pos, 50)
        return np.zeros(2) if best is None else self.normalize(best)

    def normalize(self, direction):
        norm = np.sqrt(direction[0] ** 2 + direction[1] ** 2)
        if norm == 0:
            return np.zeros(2)
        return np.array([direction[0] / norm, direction[1] / norm])
