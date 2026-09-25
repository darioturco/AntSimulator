import time
import pygame
from src.menu import Menu
from src.world import World

FAST_BUDGET = 0.03     # seconds of simulation per loop while Tab is held
FAST_REFRESH = 1.0     # seconds between redraws while fast-forwarding

def main():
    setup = Menu().run()
    if setup is None:
        pygame.quit()
        return

    world = World(setup.size, setup.colonies, setup.food, setup.obstacles, setup.population)
    clock = pygame.time.Clock()
    last_draw = 0.0

    running = True
    while running:
        # Handling events every frame is what lets the window close with the X
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        if pygame.key.get_pressed()[pygame.K_TAB]:
            # Fast forward: many steps per loop, and (almost) nothing is drawn
            world.fast_mode = True
            world.fast_forward(FAST_BUDGET)
            if time.perf_counter() - last_draw >= FAST_REFRESH:
                world.render()
                last_draw = time.perf_counter()
        else:
            world.fast_mode = False
            world.step()
            world.render()
            last_draw = time.perf_counter()
            clock.tick(40)

    pygame.quit()

if __name__ == '__main__':
    main()
