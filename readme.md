# Ant Simulator #

This project is a Python project that simulates the behavior of ants in a 2D space. In this simulation, ants navigate through the environment, searching for food and following a specific algorithm for pathfinding. The Ant pathfinding algorithms are often inspired by the foraging behavior of real ants, particularly their ability to find the shortest path between their nest and a food source. In this project I use a simplified version of the _Ant Colony Optimization (ACO) algorithm_ (pheromone marks that fade over time, without per-path probabilities). Here's a simplified explanation of how an ACO-based ant pathfinding algorithm work:

1. Initialization: Place a number of virtual ants in the environment. Each ant is positioned randomly. Assign a pheromone level to each edge (connection between two points) in the environment.

1. Movement: Ants move through the environment from their current position to neighboring positions. The probability of an ant choosing a particular path is influenced by both the pheromone level on the path and the distance to the destination. Ants prefer paths with higher pheromone levels.

1. Pheromone Update: After all ants have completed their movements, update the pheromone levels on each edge. Increase the pheromone level on the paths taken by the ants. This represents the idea that successful paths are reinforced with pheromones.

1. Evaporation: Simulate the evaporation of pheromones over time to prevent the system from converging to a suboptimal solution. Reduce the pheromone level on all edges.

1. Iteration: Repeat the movement, pheromone update, and evaporation steps for a certain number of iterations or until a termination condition is met.

1. Path Selection: After a sufficient number of iterations, the paths with higher pheromone levels are more likely to be selected by the ants, representing the shortest paths.

## Installation ##

In order to install the project and run it localy on your machine, you can follow this simple steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/ant-simulator.git
   ```

1. Navigate to the project directory:
    ```bash
    cd ant-simulator
    ```

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage ##

Finaly, to use the project just run the command:

```bash
    python ./main.py
```

Tests (they run without opening any window):

```bash
    python -m unittest discover -s tests
```

A menu opens first, where you set up the simulation:

- **Width / height** of the world (50 to 2500 cells each).
- **Ants per colony** at the start (1 to 200; 25 by default).
- **Number of colonies** (1 to 4: blue, red, yellow and white; 1 by default).
- **Colony position**: choose *Colocar colonia*, pick the colony and click on the minimap.
- **Food**: paint it or erase it on the minimap. The slider sets how much food each painted cell holds.
- **Obstacles**: paint or erase gray cells. Ants cannot walk through them (nor place a colony under them).
- **Pincel** slider sets the brush size. Keys 1-5 select the tool, Enter starts, Esc quits.

Then a pygame window opens with the simulation (scaled to fit your screen if the world is big). Each colony has its own ants and its own pheromone marks: they wander randomly leaving marks, find the food, carry it back to their colony and the others follow the marks. The title of the window shows the ants alive per colony and the food left. Close it with the window's X or Esc.

### Growth ###

Every 5 units of food an ant brings home, the colony gets a new ant (up to 300 per colony). Food is not regenerated, so the map you paint is all the food there is.

### Fights ###

When two ants of different colonies get within 2 cells of each other they stop and fight: each step, each one hits the other with probability 0.5. An ant that receives 10 hits dies, and if it was carrying food it drops it where it died (another ant can pick it up).
