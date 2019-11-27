# Free Flow - Solver

A Python3 program that solves 2D puzzles (without bridges) of the popular mobile game Free Flow 
(you may read more on the game in the link - https://en.wikipedia.org/wiki/Flow_Free).


Requirements: pycosat, threading, numpy
In case that you don't have one of them (let's say pycosat) - pip install pycosat


How to run: Run the pyflowsolver.py program with 1 argument - a path to a puzzle text file which is located in the puzzles directory.
For example, from the project root directory run - ./pyflowsolver.py puzzles/regular_7x7_01.txt



What is going to happen: The program will solve the given puzzle 2 times using 2 manners-

1. Constraint Satisfaction Problem (CSP) - Based on Matt Zucker's solution (https://github.com/mzucker/flow_solver), 
it will generate clauses that composed of literals which formulate the following concepts (Reducing to SAT)-
- Every cell is assigned a single color
- The color of every endpoint cell is known and specified
- Every endpoint cell has exactly one neighbor which matches its color
- The flow through every non-endpoint cell matches exactly one of the six direction types
- The neighbors of a cell specified by its direction type must match its color
- The neighbors of a cell not specified by its direction type must not match its color
Then, the program converts the clauses to CNF (Conjunctive Normal Form) and the pycosat module finds a satisfying assigning to the literals.
Finally, regarding the assigned literals, the solution is extracted and displayed on the screen. 
For further reading - https://mzucker.github.io/2016/09/02/eating-sat-flavored-crow.html


2. Multiagent Parallel Distributed A* - In this manner, every agent is identified with a color and it has to find the optimal path 
from its source to its target (the shortest as possible) with respect to the other agents' flows (paths). Each agents is running on a 
different designated thread such that once an agent finds the total solution (a global goal state) -it notifies all the other agents as well 
as the Main Thread that then prints the solution to the screen. The solution is actually a matrix contains non-negative numbers such that
every number is associated with an agent (i.e a player/color) and a sequance of the same number represents the correspond agent's flow. The different
agents (which run on the different threads) communicate by a Shared-Resource: a kind of bulletin board - a data structure that stores for
every agent the states contain an optional complete flow of one or more of the other agents. Of course that the access to this Shared-Resource
is limited to at most one thread every time and there is no possibility for a deadlock, starvation or an unfair synchronization.
In order to efficiency calculate the solution, there is an implemantation of the concepts: Dead-end checks, Forced Moves, Stranded colors 
and stranded regions, Chokepoint detection and Fast-forwarding as mentioned in Matt Zucker's blog:
https://mzucker.github.io/2016/08/28/flow-solver.html



Enjoy!
Tom