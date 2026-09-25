import os
import numpy as np
import pygame
from src.world import (Setup, colony_radius, food_color, MIN_SIZE, MAX_SIZE, MAX_COLONIES, MIN_INITIAL_POPULATION, MAX_INITIAL_POPULATION, INITIAL_POPULATION,
                       COLORS, COLOR_NAMES, OBSTACLE_COLOR, FOOD_SHOWN_MAX)

WINDOW = (1060, 720)
EXAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples', 'ejemplo.npz')
MAP_RECT = pygame.Rect(370, 20, 670, 680)

BG = (24, 26, 30)
PANEL = (40, 43, 50)
TEXT = (230, 230, 230)
DIM = (150, 150, 160)
ACCENT = (70, 130, 220)
GREEN = (40, 150, 70)

TOOL_COLONY, TOOL_FOOD, TOOL_ERASE_FOOD, TOOL_OBSTACLE, TOOL_ERASE_OBSTACLE = range(5)
TOOL_NAMES = ['Colocar colonia', 'Pintar comida', 'Borrar comida', 'Pintar obstaculo', 'Borrar obstaculo']

# Colony positions as a fraction of the world, so they survive a resize
DEFAULT_COLONIES = [(0.6, 0.6), (0.85, 0.15), (0.15, 0.85), (0.85, 0.85)]


class Menu(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Ant Simulator - configuracion')
        self.screen = pygame.display.set_mode(WINDOW)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('segoeui,arial', 18)
        self.small = pygame.font.SysFont('segoeui,arial', 14)
        self.big = pygame.font.SysFont('segoeui,arial', 28, bold=True)

        self.width = 200
        self.height = 200
        self.texts = {'w': '200', 'h': '200', 'p': str(INITIAL_POPULATION)}
        self.population = INITIAL_POPULATION
        self.focus = None
        self.n_colonies = 1
        self.tool = TOOL_COLONY
        self.selected = 0
        self.brush = 8
        self.amount = 1
        self.colony_frac = list(DEFAULT_COLONIES)
        self.food = np.zeros((self.width, self.height), dtype=np.uint16)
        self.obstacles = np.zeros((self.width, self.height), dtype=bool)
        self.food[14:29, 6:21] = 1  # same food block the simulation always started with

        self.slider_drag = None
        self.painting = False
        self.last_cell = None
        self.map_dirty = True
        self.map_surface = None

        # Static layout of the left panel
        self.field_rects = {'w': pygame.Rect(200, 64, 130, 30), 'h': pygame.Rect(200, 104, 130, 30),
                            'p': pygame.Rect(200, 144, 130, 30)}
        self.minus_rect = pygame.Rect(200, 190, 30, 30)
        self.plus_rect = pygame.Rect(300, 190, 30, 30)
        self.tool_rects = [pygame.Rect(20, 250 + i * 34, 310, 30) for i in range(len(TOOL_NAMES))]
        self.colony_rects = [pygame.Rect(180 + i * 38, 426, 30, 28) for i in range(MAX_COLONIES)]
        self.sliders = {'brush': (pygame.Rect(20, 496, 310, 10), 1, 40),
                        'amount': (pygame.Rect(20, 548, 310, 10), 1, FOOD_SHOWN_MAX)}
        self.clear_rect = pygame.Rect(20, 585, 150, 36)
        self.example_rect = pygame.Rect(180, 585, 150, 36)
        self.message = ''
        self.start_rect = pygame.Rect(20, 632, 310, 50)

    # ---- World geometry ----

    def map_scale(self):
        return min(MAP_RECT.width / self.width, MAP_RECT.height / self.height)

    def map_origin(self):
        s = self.map_scale()
        return (MAP_RECT.x + (MAP_RECT.width - self.width * s) / 2,
                MAP_RECT.y + (MAP_RECT.height - self.height * s) / 2)

    def colony_pos(self, i):
        """Colony i in world cells, kept fully inside the world."""
        r = colony_radius(self.width, self.height)
        fx, fy = self.colony_frac[i]
        x = min(max(int(fx * self.width), r), self.width - 1 - r)
        y = min(max(int(fy * self.height), r), self.height - 1 - r)
        return (x, y)

    def mouse_to_cell(self, pos):
        """Cell under the mouse, or None if it is outside the minimap."""
        s = self.map_scale()
        ox, oy = self.map_origin()
        x, y = int((pos[0] - ox) / s), int((pos[1] - oy) / s)
        if 0 <= x < self.width and 0 <= y < self.height and (pos[0] - ox) >= 0 and (pos[1] - oy) >= 0:
            return (x, y)
        return None

    # ---- Editing the map ----

    def brush_cells(self):
        s = self.map_scale()
        return max(int(round(self.brush / s)), int(0.5 / s + 0.5))

    def paint_disc(self, arr, cx, cy, r, value, exclude=None):
        x0, x1 = max(0, cx - r), min(self.width, cx + r + 1)
        y0, y1 = max(0, cy - r), min(self.height, cy + r + 1)
        if x0 >= x1 or y0 >= y1:
            return
        xs = np.arange(x0, x1)[:, None] - cx
        ys = np.arange(y0, y1)[None, :] - cy
        mask = xs * xs + ys * ys <= r * r
        if exclude is not None:
            mask &= ~exclude[x0:x1, y0:y1]
        arr[x0:x1, y0:y1][mask] = value

    def clear_colony_zone(self, i):
        x, y = self.colony_pos(i)
        self.paint_disc(self.obstacles, x, y, colony_radius(self.width, self.height) + 1, False)

    def apply_tool(self, cell):
        r = self.brush_cells()
        cx, cy = cell
        if self.tool == TOOL_FOOD:
            self.paint_disc(self.food, cx, cy, r, self.amount, exclude=self.obstacles)
        elif self.tool == TOOL_ERASE_FOOD:
            self.paint_disc(self.food, cx, cy, r, 0)
        elif self.tool == TOOL_OBSTACLE:
            self.paint_disc(self.obstacles, cx, cy, r, True)
            self.paint_disc(self.food, cx, cy, r, 0)
            for i in range(self.n_colonies):
                self.clear_colony_zone(i)  # never wall in a colony
        elif self.tool == TOOL_ERASE_OBSTACLE:
            self.paint_disc(self.obstacles, cx, cy, r, False)
        self.map_dirty = True

    def paint_stroke(self, pos):
        cell = self.mouse_to_cell(pos)
        if cell is None:
            self.last_cell = None
            return
        if self.tool == TOOL_COLONY:
            s = self.map_scale()
            ox, oy = self.map_origin()
            self.colony_frac[self.selected] = (((pos[0] - ox) / s) / self.width, ((pos[1] - oy) / s) / self.height)
            self.clear_colony_zone(self.selected)
            self.map_dirty = True
            return

        # Fill the gap between two mouse events so fast strokes stay continuous
        if self.last_cell is not None:
            (x0, y0), (x1, y1) = self.last_cell, cell
            steps = max(abs(x1 - x0), abs(y1 - y0)) // max(1, self.brush_cells()) + 1
            for k in range(1, steps + 1):
                self.apply_tool((round(x0 + (x1 - x0) * k / steps), round(y0 + (y1 - y0) * k / steps)))
        else:
            self.apply_tool(cell)
        self.last_cell = cell

    def commit_field(self, key):
        if key == 'p':
            try:
                value = int(self.texts[key])
            except ValueError:
                value = self.population
            self.population = min(max(value, MIN_INITIAL_POPULATION), MAX_INITIAL_POPULATION)
            self.texts[key] = str(self.population)
            return

        try:
            value = int(self.texts[key])
        except ValueError:
            value = self.width if key == 'w' else self.height
        value = min(max(value, MIN_SIZE), MAX_SIZE)
        self.texts[key] = str(value)

        new_w = value if key == 'w' else self.width
        new_h = value if key == 'h' else self.height
        if (new_w, new_h) != (self.width, self.height):
            keep_w, keep_h = min(new_w, self.width), min(new_h, self.height)
            food = np.zeros((new_w, new_h), dtype=np.uint16)
            obstacles = np.zeros((new_w, new_h), dtype=bool)
            food[:keep_w, :keep_h] = self.food[:keep_w, :keep_h]
            obstacles[:keep_w, :keep_h] = self.obstacles[:keep_w, :keep_h]
            self.width, self.height = new_w, new_h
            self.food, self.obstacles = food, obstacles
            for i in range(self.n_colonies):
                self.clear_colony_zone(i)
            self.map_dirty = True

    # ---- Saving / loading a scenario ----

    def save_scenario(self, path):
        np.savez_compressed(path, size=[self.width, self.height], n_colonies=self.n_colonies,
                            colony_frac=np.array(self.colony_frac), population=self.population,
                            food=self.food, obstacles=self.obstacles)

    def load_scenario(self, path):
        with np.load(path) as data:
            width, height = (int(v) for v in data['size'])
            if not (MIN_SIZE <= width <= MAX_SIZE and MIN_SIZE <= height <= MAX_SIZE):
                raise ValueError('tamano fuera de rango')
            food = data['food'].astype(np.uint16)
            obstacles = data['obstacles'].astype(bool)
            if food.shape != (width, height) or obstacles.shape != (width, height):
                raise ValueError('mapa con tamano inconsistente')
            self.width, self.height = width, height
            self.food, self.obstacles = food, obstacles
            self.n_colonies = min(max(int(data['n_colonies']), 1), MAX_COLONIES)
            self.colony_frac = [tuple(float(v) for v in f) for f in data['colony_frac']]
            self.population = min(max(int(data['population']), MIN_INITIAL_POPULATION), MAX_INITIAL_POPULATION)
        self.texts = {'w': str(self.width), 'h': str(self.height), 'p': str(self.population)}
        self.selected = 0
        self.focus = None
        self.map_dirty = True

    def load_example(self):
        try:
            self.load_scenario(EXAMPLE_PATH)
            self.message = 'Ejemplo cargado: toca INICIAR'
        except (OSError, ValueError, KeyError) as e:
            self.message = 'No se pudo cargar el ejemplo (%s)' % e

    def set_focus(self, key):
        if self.focus is not None and self.focus != key:
            self.commit_field(self.focus)
        self.focus = key

    def set_slider(self, name, mouse_x):
        rect, lo, hi = self.sliders[name]
        frac = min(max((mouse_x - rect.x) / rect.width, 0), 1)
        setattr(self, name, lo + int(round(frac * (hi - lo))))

    # ---- Events ----

    def start(self):
        self.set_focus(None)
        positions = [self.colony_pos(i) for i in range(self.n_colonies)]
        for i in range(self.n_colonies):
            self.clear_colony_zone(i)
        return Setup((self.width, self.height), positions, self.food, self.obstacles, self.population)

    def on_mouse_down(self, pos):
        for key, rect in self.field_rects.items():
            if rect.collidepoint(pos):
                self.set_focus(key)
                return
        self.set_focus(None)

        if self.minus_rect.collidepoint(pos):
            self.n_colonies = max(1, self.n_colonies - 1)
            self.selected = min(self.selected, self.n_colonies - 1)
            self.map_dirty = True
        elif self.plus_rect.collidepoint(pos):
            self.n_colonies = min(MAX_COLONIES, self.n_colonies + 1)
            self.clear_colony_zone(self.n_colonies - 1)
            self.map_dirty = True
        elif self.example_rect.collidepoint(pos):
            self.load_example()
        elif self.clear_rect.collidepoint(pos):
            self.food[:] = 0
            self.obstacles[:] = False
            self.map_dirty = True
        elif self.start_rect.collidepoint(pos):
            return self.start()

        for i, rect in enumerate(self.tool_rects):
            if rect.collidepoint(pos):
                self.tool = i
        for i, rect in enumerate(self.colony_rects[:self.n_colonies]):
            if rect.collidepoint(pos):
                self.selected = i
                self.tool = TOOL_COLONY
        for name, (rect, _, _) in self.sliders.items():
            if rect.inflate(0, 20).collidepoint(pos):
                self.slider_drag = name
                self.set_slider(name, pos[0])

        if MAP_RECT.collidepoint(pos):
            self.painting = True
            self.last_cell = None
            self.paint_stroke(pos)
        return None

    def on_key(self, event):
        if self.focus is not None:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB, pygame.K_ESCAPE):
                self.commit_field(self.focus)
                self.focus = None
            elif event.key == pygame.K_BACKSPACE:
                self.texts[self.focus] = self.texts[self.focus][:-1]
            elif event.unicode.isdigit() and len(self.texts[self.focus]) < 4:
                self.texts[self.focus] += event.unicode
            return None

        if pygame.K_1 <= event.key <= pygame.K_5:
            self.tool = event.key - pygame.K_1
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self.start()
        return None

    def run(self):
        """Show the menu. Returns a Setup, or None if the window was closed."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.focus is None:
                    return None

                result = None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self.on_mouse_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.slider_drag = None
                    self.painting = False
                    self.last_cell = None
                elif event.type == pygame.MOUSEMOTION:
                    if self.slider_drag:
                        self.set_slider(self.slider_drag, event.pos[0])
                    elif self.painting:
                        self.paint_stroke(event.pos)
                elif event.type == pygame.KEYDOWN:
                    result = self.on_key(event)
                if result is not None:
                    return result

            self.draw()
            self.clock.tick(60)

    # ---- Drawing ----

    def label(self, text, pos, font=None, color=TEXT):
        self.screen.blit((font or self.font).render(text, True, color), pos)

    def build_map(self):
        s = self.map_scale()
        mw, mh = max(1, int(self.width * s)), max(1, int(self.height * s))
        xs = np.minimum((np.arange(mw) / s).astype(int), self.width - 1)
        ys = np.minimum((np.arange(mh) / s).astype(int), self.height - 1)
        food = self.food[np.ix_(xs, ys)].astype(np.int32)
        walls = self.obstacles[np.ix_(xs, ys)]
        img = np.zeros((mw, mh, 3), dtype=np.uint8)
        img[..., 1] = np.where(food > 0, 150 + np.minimum(food, FOOD_SHOWN_MAX) * 105 // FOOD_SHOWN_MAX, 0)
        img[walls] = OBSTACLE_COLOR
        return pygame.surfarray.make_surface(img)

    def draw(self):
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, PANEL, (10, 10, 340, 700), border_radius=8)
        self.label('Ant Simulator', (20, 18), self.big)

        # Size fields
        for key, name, lo, hi in (('w', 'Ancho', MIN_SIZE, MAX_SIZE), ('h', 'Alto', MIN_SIZE, MAX_SIZE),
                                  ('p', 'Hormigas', MIN_INITIAL_POPULATION, MAX_INITIAL_POPULATION)):
            rect = self.field_rects[key]
            self.label('%s (%d-%d)' % (name, lo, hi), (20, rect.y + 4))
            pygame.draw.rect(self.screen, (20, 22, 26), rect, border_radius=4)
            pygame.draw.rect(self.screen, ACCENT if self.focus == key else DIM, rect, 2, border_radius=4)
            caret = '|' if self.focus == key and pygame.time.get_ticks() // 500 % 2 == 0 else ''
            self.label(self.texts[key] + caret, (rect.x + 8, rect.y + 4))

        # Number of colonies
        self.label('Colonias (1-%d)' % MAX_COLONIES, (20, 194))
        for rect, sign in ((self.minus_rect, '-'), (self.plus_rect, '+')):
            pygame.draw.rect(self.screen, ACCENT, rect, border_radius=4)
            self.label(sign, (rect.x + 10, rect.y + 3))
        self.label(str(self.n_colonies), (256, 194))

        # Tools
        self.label('Herramienta (teclas 1-5)', (20, 226), color=DIM)
        for i, rect in enumerate(self.tool_rects):
            pygame.draw.rect(self.screen, ACCENT if self.tool == i else (60, 64, 74), rect, border_radius=4)
            self.label('%d  %s' % (i + 1, TOOL_NAMES[i]), (rect.x + 10, rect.y + 5))

        self.label('Colonia a colocar', (20, 430))
        for i, rect in enumerate(self.colony_rects[:self.n_colonies]):
            pygame.draw.rect(self.screen, COLORS[i], rect, border_radius=4)
            if self.selected == i:
                pygame.draw.rect(self.screen, TEXT, rect.inflate(6, 6), 3, border_radius=6)

        # Sliders
        for name, title, value in (('brush', 'Pincel (px del minimapa)', self.brush),
                                   ('amount', 'Cantidad de comida por celda', self.amount)):
            rect, lo, hi = self.sliders[name]
            self.label('%s: %d' % (title, value), (20, rect.y - 26))
            pygame.draw.rect(self.screen, (20, 22, 26), rect, border_radius=5)
            knob_x = rect.x + int((value - lo) / (hi - lo) * rect.width)
            pygame.draw.rect(self.screen, ACCENT, (rect.x, rect.y, knob_x - rect.x, rect.height), border_radius=5)
            pygame.draw.circle(self.screen, TEXT, (knob_x, rect.centery), 9)
        pygame.draw.rect(self.screen, food_color(self.amount), (300, 520, 30, 16), border_radius=3)

        # Buttons
        pygame.draw.rect(self.screen, (90, 60, 60), self.clear_rect, border_radius=6)
        self.label('Limpiar mapa', (self.clear_rect.x + 26, self.clear_rect.y + 6))
        pygame.draw.rect(self.screen, (60, 90, 130), self.example_rect, border_radius=6)
        self.label('Cargar ejemplo', (self.example_rect.x + 18, self.example_rect.y + 6))
        pygame.draw.rect(self.screen, GREEN, self.start_rect, border_radius=8)
        self.label('INICIAR', (self.start_rect.x + 115, self.start_rect.y + 11), self.font)
        self.label(self.message or 'Enter: iniciar   Esc: salir', (20, 690), self.small, DIM)

        self.draw_map()
        pygame.display.flip()

    def draw_map(self):
        if self.map_dirty or self.map_surface is None:
            self.map_surface = self.build_map()
            self.map_dirty = False

        s = self.map_scale()
        ox, oy = self.map_origin()
        pygame.draw.rect(self.screen, PANEL, MAP_RECT.inflate(10, 10), border_radius=6)
        self.screen.blit(self.map_surface, (ox, oy))
        pygame.draw.rect(self.screen, DIM, (ox - 1, oy - 1, self.map_surface.get_width() + 2, self.map_surface.get_height() + 2), 1)

        radius = colony_radius(self.width, self.height)
        for i in range(self.n_colonies):
            x, y = self.colony_pos(i)
            center = (int(ox + (x + 0.5) * s), int(oy + (y + 0.5) * s))
            pygame.draw.circle(self.screen, COLORS[i], center, max(3, int(radius * s)))
            if self.selected == i:
                pygame.draw.circle(self.screen, TEXT, center, max(3, int(radius * s)) + 3, 2)

        self.label('Minimapa %dx%d' % (self.width, self.height), (MAP_RECT.x, 2), self.small, DIM)
