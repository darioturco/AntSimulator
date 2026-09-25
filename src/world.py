import time
import numpy as np
import pygame
from collections import namedtuple
from src.colony import Colony

MIN_SIZE = 50
MAX_SIZE = 2500
MAX_COLONIES = 4
MIN_INITIAL_POPULATION = 1
MAX_INITIAL_POPULATION = 200
INITIAL_POPULATION = 25

# Colonies, in order: blue, red, yellow, white
COLORS = [(40, 120, 255), (255, 0, 0), (255, 220, 0), (255, 255, 255)]
COLOR_NAMES = ['azul', 'rojo', 'amarillo', 'blanco']
OBSTACLE_COLOR = (128, 128, 128)
FOOD_SHOWN_MAX = 50

# Combat
ATTACK_RANGE = 2.0
ATTACK_PROBABILITY = 0.5
MAX_HITS = 10

# What the menu hands over to the world
Setup = namedtuple('Setup', ['size', 'colonies', 'food', 'obstacles', 'population'])


def colony_radius(width, height):
    return max(3, min(20, min(width, height) // 8))


def food_color(amount):
    """Brighter green the more food a cell holds."""
    if amount <= 0:
        return (0, 0, 0)
    return (0, 150 + min(amount, FOOD_SHOWN_MAX) * 105 // FOOD_SHOWN_MAX, 0)


class World(object):
    def __init__(self, size, colony_positions, food, obstacles, initial_population=INITIAL_POPULATION):
        self.size = size
        self.width, self.height = size
        self.food = food.copy()
        self.obstacles = obstacles.copy()
        self.food_total = int(self.food.sum())
        self.steps = 0
        self.fast_mode = False  # only changes the window title

        radius = colony_radius(*size)
        self.colonies = []
        for i, p in enumerate(colony_positions):
            self.clear_obstacles(p, radius)
            self.colonies.append(Colony(self, p, COLORS[i], radius, initial_population, COLOR_NAMES[i]))

        # Init pygame: the window shows the world scaled to fit the screen
        pygame.init()
        pygame.display.set_caption('Ants')
        desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
        fit = min(desktop_w * 0.9 / self.width, desktop_h * 0.85 / self.height)
        self.scale = min(fit, max(1.0, 500 / max(self.width, self.height)))
        self.window_size = (max(1, round(self.width * self.scale)), max(1, round(self.height * self.scale)))
        self.window = pygame.display.set_mode(self.window_size)
        size = max(1, min(3, round(self.scale)))  # ants and marks: a small blob of 1-3 pixels
        self.blob = [(dx, dy) for dx in range(-size, size + 1) for dy in range(-size, size + 1) if dx * dx + dy * dy <= size * size]

        self.background = self._build_background()
        self.scaled_background = None
        self.background_dirty = True
        self.frames_since_scale = 0

    # ---- Background layer (obstacles + food), one pixel per world cell ----

    def _build_background(self):
        rgb = np.zeros((self.width, self.height, 3), dtype=np.uint8)
        shown = np.minimum(self.food, FOOD_SHOWN_MAX).astype(np.int32)
        rgb[..., 1] = np.where(self.food > 0, 150 + shown * 105 // FOOD_SHOWN_MAX, 0)
        rgb[self.obstacles] = OBSTACLE_COLOR
        return pygame.surfarray.make_surface(rgb).convert()

    def _refresh_cell(self, x, y):
        self.background.set_at((x, y), food_color(int(self.food[x, y])))
        self.background_dirty = True

    def clear_obstacles(self, pos, radius):
        x0, x1 = max(0, pos[0] - radius), min(self.width, pos[0] + radius + 1)
        y0, y1 = max(0, pos[1] - radius), min(self.height, pos[1] + radius + 1)
        xs = np.arange(x0, x1)[:, None] - pos[0]
        ys = np.arange(y0, y1)[None, :] - pos[1]
        self.obstacles[x0:x1, y0:y1][xs * xs + ys * ys <= radius * radius] = False

    # ---- Queries used by the ants ----

    def is_blocked(self, pos):
        """True if pos is outside the world or on an obstacle."""
        if pos[0] < 0 or pos[1] < 0 or pos[0] >= self.width or pos[1] >= self.height:
            return True
        return bool(self.obstacles[int(pos[0]), int(pos[1])])

    def is_over_food(self, pos):
        x, y = int(pos[0]), int(pos[1])
        if self.food[x, y] > 0:
            self.food[x, y] -= 1
            self.food_total -= 1
            self._refresh_cell(x, y)
            return True

        return False

    def add_food(self, pos, amount=1):
        x, y = int(pos[0]), int(pos[1])
        if self.is_blocked((x, y)):
            return
        self.food[x, y] += amount
        self.food_total += amount
        self._refresh_cell(x, y)

    # ---- Simulation ----

    def step(self):
        self._combat()
        for c in self.colonies:
            c.step()

        self.steps += 1
        if self.steps % 20 == 0:
            self._update_caption()

    def fast_forward(self, budget):
        """Advance the simulation without drawing anything for `budget` seconds.
        Returns how many steps were done (at least one)."""
        start = time.perf_counter()
        done = 0
        while True:
            self.step()
            done += 1
            if time.perf_counter() - start >= budget:
                return done

    def _combat(self):
        """Ants of different colonies within ATTACK_RANGE stop and trade blows: each
        one hits the other with probability ATTACK_PROBABILITY per step. After
        MAX_HITS hits an ant dies and drops the food it was carrying."""
        colonies = [c for c in self.colonies if c.ants]
        if len(colonies) < 2:
            return
        ants = [a for c in colonies for a in c.ants]
        candidates = self._ants_near_an_enemy(colonies, ants)
        if not candidates:
            return

        # Only ants with an enemy close by are worth checking (enemies are candidates too)
        cell = ATTACK_RANGE
        grid = {}
        for a in candidates:
            grid.setdefault((int(a.pos[0] // cell), int(a.pos[1] // cell)), []).append(a)

        hit = False
        for a in candidates:
            gx, gy = int(a.pos[0] // cell), int(a.pos[1] // cell)
            enemy = None
            for i in (gx - 1, gx, gx + 1):
                for j in (gy - 1, gy, gy + 1):
                    for b in grid.get((i, j), ()):
                        if b.colony is not a.colony and np.sum((a.pos - b.pos) ** 2) <= ATTACK_RANGE ** 2:
                            enemy = b
                            break
                    if enemy is not None:
                        break
                if enemy is not None:
                    break

            if enemy is not None:
                a.attacking = True  # fighting: does not move this step
                if np.random.random() < ATTACK_PROBABILITY:
                    enemy.hits += 1
                    hit = True

        if hit:
            for c in self.colonies:
                for a in c.ants:
                    if a.hits >= MAX_HITS and a.with_food:
                        self.add_food(a.pos, 1)
                c.ants = [a for a in c.ants if a.hits < MAX_HITS]

    def _ants_near_an_enemy(self, colonies, ants):
        """Ants (in the original order) that have an ant of another colony in their
        3x3 block of ATTACK_RANGE-sized cells. Done with numpy so the (many) ants
        that are alone cost almost nothing."""
        pos = np.array([a.pos for a in ants])
        colony_bit = np.repeat(1 << np.arange(len(colonies), dtype=np.int64), [len(c.ants) for c in colonies])
        span = 1 << 20
        cx = (pos[:, 0] // ATTACK_RANGE).astype(np.int64) + 1
        cy = (pos[:, 1] // ATTACK_RANGE).astype(np.int64) + 1
        key = cx * span + cy

        order = np.argsort(key, kind='stable')
        cells, first = np.unique(key[order], return_index=True)
        colonies_in_cell = np.bitwise_or.reduceat(colony_bit[order], first)

        nearby = np.zeros(len(ants), dtype=np.int64)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                wanted = key + dx * span + dy
                where = np.minimum(np.searchsorted(cells, wanted), len(cells) - 1)
                nearby |= np.where(cells[where] == wanted, colonies_in_cell[where], 0)

        return [ants[i] for i in np.nonzero(nearby & ~colony_bit)[0]]

    def _update_caption(self):
        parts = ['%s: %d' % (c.name, len(c.ants)) for c in self.colonies]
        title = 'Ants - ' + ' | '.join(parts) + ' | comida: %d' % self.food_total
        title += ' | AVANCE RAPIDO' if self.fast_mode else ' | mantener Tab: avance rapido'
        pygame.display.set_caption(title)

    # ---- Rendering ----

    def _screen_pos(self, pos):
        return (int(pos[0] * self.scale), int(pos[1] * self.scale))

    def draw_circle(self, color, pos, radius):
        pygame.draw.circle(self.window, color, self._screen_pos(pos), max(1, round(radius * self.scale)))

    def plot_points(self, color, points):
        """Ants and pheromone marks: all the points of one colour at once, written
        straight into the window's pixels (one call per point is far too slow)."""
        if len(points) == 0:
            return
        px = (points[:, 0] * self.scale).astype(int)
        py = (points[:, 1] * self.scale).astype(int)
        width, height = self.window_size
        pixels = pygame.surfarray.pixels3d(self.window)
        for dx, dy in self.blob:
            x, y = px + dx, py + dy
            inside = (x >= 0) & (x < width) & (y >= 0) & (y < height)
            pixels[x[inside], y[inside]] = color
        del pixels  # release the surface lock before drawing anything else

    def render(self):
        # Downscaled worlds are expensive to rescale, so do it at most every few frames
        self.frames_since_scale += 1
        if self.background_dirty and (self.scaled_background is None or self.scale >= 1 or self.frames_since_scale >= 8):
            if self.scale >= 1:
                self.scaled_background = pygame.transform.scale(self.background, self.window_size)
            else:
                self.scaled_background = pygame.transform.smoothscale(self.background, self.window_size)
            self.background_dirty = False
            self.frames_since_scale = 0

        self.window.blit(self.scaled_background, (0, 0))
        for c in self.colonies:
            c.render(self.draw_circle, self.plot_points)

        pygame.display.update()
