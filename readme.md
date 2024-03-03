# Ant Simulator #

This project is a Python project that simulates the behavior of ants in a 2D space. In this simulation, ants navigate through the environment, searching for food and following a specific algorithm for pathfinding. The Ant pathfinding algorithms are often inspired by the foraging behavior of real ants, particularly their ability to find the shortest path between their nest and a food source. In this project I use the common algorithm called _Ant Colony Optimization (ACO) algorithm_. Here's a simplified explanation of how an ACO-based ant pathfinding algorithm work:

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

That will open a pygame window with the simulation. In that simulation you'll have a red colony and a block of food(green). The some ants are going to walk in random directions leaving pheromones that can be seen with a transparent color. After some this the ants will find the food and then they are going to eat all the food.