import time
import numpy as np
from src.world import World
from src.colony import Colony

if __name__ == '__main__':
    #blue = (0, 0, 255)
    #colony = Colony((100, 100), blue, initial_population=10)

    world_size = (200, 200)
    initial_population = 25
    world = World(world_size, 1, initial_population, {(i+14, j+6) for i in range(15) for j in range(15)})

    for t in range(10000):
        world.step()
        world.render()
        time.sleep(0.025)
