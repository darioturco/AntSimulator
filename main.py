import pygame
from src.menu import Menu
from src.world import World

def main():
    setup = Menu().run()
    if setup is None:
        pygame.quit()
        return

    world = World(setup.size, setup.colonies, setup.food, setup.obstacles)
    clock = pygame.time.Clock()

    running = True
    while running:
        # Handling events every frame is what lets the window close with the X
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        world.step()
        world.render()
        clock.tick(40)

    pygame.quit()

if __name__ == '__main__':
    main()
