import os
import sys
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pygame

from src.ant import Ant
from src.colony import FOOD_PER_NEW_ANT
from src.menu import Menu
from src.world import World, MAX_HITS, MIN_SIZE, MAX_SIZE


def empty_map(w=100, h=100):
    return np.zeros((w, h), dtype=np.uint16), np.zeros((w, h), dtype=bool)


def make_world(colonies, food=None, obstacles=None, population=0, size=(100, 100)):
    empty_food, empty_obstacles = empty_map(*size)
    return World(size, colonies, empty_food if food is None else food,
                 empty_obstacles if obstacles is None else obstacles, population)


def key(k, ch=''):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch)


class FightTests(unittest.TestCase):
    def setUp(self):
        np.random.seed(0)

    def duel(self, with_food_b=False):
        world = make_world([(20, 20), (80, 80)])
        a = Ant(world.colonies[0], np.array([50.0, 50.0]))
        b = Ant(world.colonies[1], np.array([50.5, 50.0]))
        b.with_food = with_food_b
        world.colonies[0].ants = [a]
        world.colonies[1].ants = [b]
        for _ in range(500):
            world.step()
            if not world.colonies[0].ants or not world.colonies[1].ants:
                break
        return world, a, b

    def test_an_ant_dies_after_max_hits(self):
        world, a, b = self.duel()
        self.assertTrue(a.hits >= MAX_HITS or b.hits >= MAX_HITS)
        for ant in (a, b):
            self.assertEqual(ant in ant.colony.ants, ant.hits < MAX_HITS)

    def test_dead_ant_drops_its_food_where_it_died(self):
        for seed in range(30):
            np.random.seed(seed)
            world, a, b = self.duel(with_food_b=True)
            if b.hits >= MAX_HITS:
                self.assertEqual(world.food_total, 1)
                self.assertEqual(world.food[50, 50], 1)
                return
        self.fail('the ant carrying food never lost a fight')

    def test_ants_of_the_same_colony_do_not_fight(self):
        world = make_world([(20, 20)])
        a = Ant(world.colonies[0], np.array([50.0, 50.0]))
        b = Ant(world.colonies[0], np.array([50.5, 50.0]))
        world.colonies[0].ants = [a, b]
        for _ in range(100):
            world._combat()
        self.assertEqual((a.hits, b.hits), (0, 0))

    def test_far_ants_do_not_fight(self):
        world = make_world([(20, 20), (80, 80)])
        a = Ant(world.colonies[0], np.array([10.0, 10.0]))
        b = Ant(world.colonies[1], np.array([90.0, 90.0]))
        world.colonies[0].ants = [a]
        world.colonies[1].ants = [b]
        for _ in range(100):
            world._combat()
        self.assertEqual((a.hits, b.hits), (0, 0))


class ObstacleTests(unittest.TestCase):
    def test_ants_never_stand_on_obstacles_or_leave_the_world(self):
        np.random.seed(1)
        food, obstacles = empty_map(200, 200)
        obstacles[100:104, 0:150] = True
        food[170:175, 20:25] = 3
        world = make_world([(30, 100), (160, 100)], food, obstacles, population=25, size=(200, 200))
        for _ in range(1500):
            world.step()
            for c in world.colonies:
                for ant in c.ants:
                    self.assertFalse(world.is_blocked(ant.pos))

    def test_colony_area_is_cleared_of_obstacles(self):
        food, obstacles = empty_map()
        obstacles[:] = True
        world = make_world([(50, 50)], food, obstacles)
        self.assertFalse(world.obstacles[50, 50])
        self.assertFalse(world.is_blocked((50.0, 50.0)))

    def test_is_blocked(self):
        food, obstacles = empty_map()
        obstacles[10, 10] = True
        world = make_world([(50, 50)], food, obstacles)
        self.assertTrue(world.is_blocked((10.5, 10.5)))
        self.assertTrue(world.is_blocked((-0.1, 5)))
        self.assertTrue(world.is_blocked((100.0, 5)))
        self.assertFalse(world.is_blocked((99.9, 99.9)))


class FoodTests(unittest.TestCase):
    def test_picking_food_takes_one_unit(self):
        food, obstacles = empty_map()
        food[30, 30] = 2
        world = make_world([(50, 50)], food, obstacles)
        self.assertTrue(world.is_over_food((30.4, 30.9)))
        self.assertEqual((world.food[30, 30], world.food_total), (1, 1))
        self.assertTrue(world.is_over_food((30.0, 30.0)))
        self.assertFalse(world.is_over_food((30.0, 30.0)))
        self.assertEqual(world.food_total, 0)

    def test_food_cannot_be_added_on_an_obstacle(self):
        food, obstacles = empty_map()
        obstacles[30, 30] = True
        world = make_world([(50, 50)], food, obstacles)
        world.add_food((30, 30))
        self.assertEqual(world.food_total, 0)

    def test_colony_grows_with_delivered_food(self):
        world = make_world([(50, 50)], population=3)
        colony = world.colonies[0]
        for _ in range(FOOD_PER_NEW_ANT - 1):
            colony.deliver_food()
        self.assertEqual(len(colony.ants), 3)
        colony.deliver_food()
        self.assertEqual(len(colony.ants), 4)


class ColonyTests(unittest.TestCase):
    def test_normalize_zero_vector(self):
        world = make_world([(50, 50)], population=1)
        self.assertEqual(list(world.colonies[0].normalize((0, 0))), [0, 0])

    def test_no_nan_positions(self):
        np.random.seed(2)
        world = make_world([(30, 30), (70, 70)], population=10)
        for _ in range(500):
            world.step()
        for c in world.colonies:
            for ant in c.ants:
                self.assertFalse(np.isnan(ant.pos).any())


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.menu = Menu()

    def type_in(self, field, text):
        self.menu.on_mouse_down(self.menu.field_rects[field].center)
        for _ in range(6):
            self.menu.on_key(key(pygame.K_BACKSPACE))
        for ch in text:
            self.menu.on_key(key(ord(ch), ch))
        self.menu.on_key(key(pygame.K_RETURN, "\r"))

    def paint(self, tool, cell):
        self.menu.tool = tool
        self.menu.apply_tool(cell)

    def test_size_is_clamped(self):
        self.type_in('w', '9999')
        self.assertEqual(self.menu.width, MAX_SIZE)
        self.type_in('h', '5')
        self.assertEqual(self.menu.height, MIN_SIZE)
        self.assertEqual(self.menu.food.shape, (MAX_SIZE, MIN_SIZE))

    def test_resize_keeps_the_painted_map(self):
        self.menu.food[:] = 0
        self.menu.food[10, 10] = 7
        self.menu.obstacles[20, 20] = True
        self.type_in('w', '300')
        self.assertEqual(self.menu.food[10, 10], 7)
        self.assertTrue(self.menu.obstacles[20, 20])

    def test_colony_count_limits(self):
        self.assertEqual(self.menu.n_colonies, 1)
        for _ in range(10):
            self.menu.on_mouse_down(self.menu.plus_rect.center)
        self.assertEqual(self.menu.n_colonies, 4)
        for _ in range(10):
            self.menu.on_mouse_down(self.menu.minus_rect.center)
        self.assertEqual(self.menu.n_colonies, 1)

    def test_population_is_clamped_and_reaches_the_setup(self):
        self.type_in('p', '0')
        self.assertEqual(self.menu.population, 1)
        self.type_in('p', '999')
        self.assertEqual(self.menu.population, 200)
        self.type_in('p', '40')
        self.assertEqual(self.menu.start().population, 40)

    def test_paint_and_erase(self):
        m = self.menu
        m.food[:] = 0
        m.amount = 9
        m.brush = 1
        self.paint(1, (100, 100))
        self.assertEqual(m.food[100, 100], 9)
        self.paint(2, (100, 100))
        self.assertEqual(m.food[100, 100], 0)
        self.paint(3, (150, 150))
        self.assertTrue(m.obstacles[150, 150])
        self.paint(1, (150, 150))
        self.assertEqual(m.food[150, 150], 0)  # no food on obstacles
        self.paint(4, (150, 150))
        self.assertFalse(m.obstacles[150, 150])

    def test_obstacles_are_never_painted_over_a_colony(self):
        m = self.menu
        x, y = m.colony_pos(0)
        m.brush = 40
        self.paint(3, (x, y))
        self.assertFalse(m.obstacles[x, y])

    def test_setup_positions_are_inside_the_world(self):
        for _ in range(3):
            self.menu.on_mouse_down(self.menu.plus_rect.center)
        self.menu.colony_frac = [(0.0, 0.0), (1.0, 1.0), (0.5, 1.0), (1.0, 0.0)]
        setup = self.menu.start()
        self.assertEqual(len(setup.colonies), 4)
        for x, y in setup.colonies:
            self.assertTrue(0 <= x < setup.size[0] and 0 <= y < setup.size[1])

    def test_example_button_loads_a_playable_scenario(self):
        self.menu.on_mouse_down(self.menu.example_rect.center)
        self.assertIn('Ejemplo cargado', self.menu.message)
        setup = self.menu.start()
        self.assertEqual(len(setup.colonies), 3)
        self.assertGreater(int(setup.food.sum()), 0)
        self.assertGreater(int(setup.obstacles.sum()), 0)
        world = World(setup.size, setup.colonies, setup.food, setup.obstacles, setup.population)
        for _ in range(100):
            world.step()
            world.render()

    def test_scenario_round_trip(self):
        import tempfile
        self.menu.food[5, 5] = 9
        self.menu.obstacles[6, 6] = True
        self.menu.population = 33
        path = os.path.join(tempfile.mkdtemp(), 'escenario.npz')
        self.menu.save_scenario(path)
        other = Menu()
        other.load_scenario(path)
        self.assertEqual((other.width, other.height, other.population), (200, 200, 33))
        self.assertEqual(other.food[5, 5], 9)
        self.assertTrue(other.obstacles[6, 6])

    def test_missing_scenario_shows_a_message_instead_of_crashing(self):
        self.menu.message = ''
        try:
            self.menu.load_scenario('no_existe.npz')
        except OSError:
            pass
        import src.menu as menu_module
        original = menu_module.EXAMPLE_PATH
        menu_module.EXAMPLE_PATH = 'no_existe.npz'
        try:
            self.menu.load_example()
        finally:
            menu_module.EXAMPLE_PATH = original
        self.assertIn('No se pudo cargar', self.menu.message)

    def test_closing_the_menu_returns_none(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertIsNone(self.menu.run())


if __name__ == '__main__':
    unittest.main()
