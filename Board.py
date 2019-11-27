import numpy as np
from threading import Lock



global goal_state
goal_state = None

global update_global_goal_mutex
update_global_goal_mutex = Lock()

ROW = 0
COL = 1
FREE = -1
EMPTY = 0
##############################################################
# ---------------------The State class----------------------
##############################################################

class State:
    """
    Represents a State in our problem and contains the following attributes:
        - size: The board contains size(length)X size(width)squares.
        - board: The correspond 2D array to the board state (numpy matrix).
        - players: A dictionary mapping the given colors chars to represent the players by numbers.
        - finished: A dictionary indicates which players completed their flows.
        - g value and h value: Are required for performing A* search.
        - targets and sources: Stores the end points and the initial points respectively.
        - head and player: Identified with the agent that executes his flow on this State. The head is a 2D index
          represents the last cell of the player's flow. The player is a non-negative number which is associated with
          the correspond agent.
        - regions map and dependencies: Are required for performing Connected-component Labeling.

    """


    def __init__(self, size, boardStringRepresentation, colorsAndPlayers):
        """
        Constructor. Initializes the State attributes.
        :param size: The sizes of the board (size X size).
        :param boardStringRepresentation: A String representation for a puzzle.
        :param colorsAndPlayers: Maps chars that represent the agents to their correspond numbers.
        """
        self.size = size
        self.players = colorsAndPlayers
        self.board = []
        self.g_value = 0 # The agent didn't perform any move.
        self.h_value = (size * size) - (2 * len(self.players)) # Represents all the empty cells in the board.
        self.sources = {}
        self.targets = {}
        # Converts from String representation of the problem to a numeric one.
        self.convertToNpFormat(boardStringRepresentation)
        self.finished = {}
        # There is no agent that completed his flow yet.
        for player_num in range(len(self.players)):
            self.finished[player_num] = False
        self.num_of_finished_agents = 0
        # Will be initialized in set_head
        self.head = None
        self.player = (size * size) + 1
        # Are calculated according to a call for the Connected-component Labeling function.
        self.regions_map = None
        self.curr_empty_tiles = 0



    def set_head(self, row, col):
        """
        Sets the head of the player's flow. The player's number will be determined accordingly.
        :param row: The given row index.
        :param col:  The given column index.
        """
        self.head = (row, col)
        self.player = self.board[row][col]
        # self.curr_empty_tiles = self.how_many_empty_tiles()
        # manhattan_dist = self.manhattan_distance_heur(row, col, self.targets[self.player][ROW],self.targets[self.player][COL])
        # self.h_value = self.curr_empty_tiles + manhattan_dist - 1


    def convertToNpFormat (self, boardStringRepresentation):
        """
        Converts the String representation of the problem to a numeric representation.
        :param boardStringRepresentation: A String representation of a board.
        """
        # Loop iterates the rows of the board (outer loop).
        for outer_index in range(self.size):
            rowString = boardStringRepresentation[outer_index]
            numbersList = []

            inner_index = -1
            # Loop for iterating every String represents a row in the game board (inner loop)
            for ch in rowString:
                inner_index = inner_index + 1
                if (ch == '.'): # symbolizes an empty square
                    numbersList.append(-1)
                else: # The square is an edge point of an agent.
                    numbersList.append(self.players[ch])
                    if (self.players[ch] in self.sources):
                        self.targets[self.players[ch]] = (outer_index, inner_index)
                    else:
                        self.sources[self.players[ch]] = (outer_index, inner_index)

            self.board.append(np.array(numbersList)) # Concatenating the current row to the accumulated board.
        self.determining_targets_and_sources()


    def determining_targets_and_sources(self):
        """
        A method finds the closer endpoint (source/target) to an edge of the game board. In case that the target is
        closer to an edge, a swap will be performed.
        """
        for agent_num in range (len(self.players)):
            # calculates the distances from the edges (regarding vertical and horizontal aspects)
            min_vertical_source_dist = min(self.sources[agent_num][ROW], self.size - (self.sources[agent_num][ROW] + 1))
            min_horizontal_source_dist = min (self.sources[agent_num][COL], self.size - (self.sources[agent_num][COL] + 1))

            min_vertical_target_dist = min(self.targets[agent_num][ROW], self.size - (self.targets[agent_num][ROW] + 1))
            min_horizontal_target_dist = min (self.targets[agent_num][COL], self.size - (self.targets[agent_num][COL] + 1))

            # Now find the shortest distance from the source to an edge and the shortest distance from the target to an edge
            min_source_dist = min (min_vertical_source_dist, min_horizontal_source_dist)
            min_target_dist = min (min_vertical_target_dist, min_horizontal_target_dist)

            # Checks who is closer to an edge: if the target is closer we'll execute a swap between them.
            if (min_target_dist < min_source_dist):
                container = self.sources[agent_num]
                self.sources[agent_num] = self.targets[agent_num]
                self.targets[agent_num] = container




    ##############################################################
    # ------------------------Validations-------------------------
    ##############################################################

    def check_move_valid(self, row, col):
        """
        Checks whether it is valid for the player to perform a move at index [row][col].
        :param row: The given row index.
        :param col:  The given column index.
        :return: True is the square is empty and has a neighbour of the current player, False otherwise.
        """
        # Case of invalid input
        if (row >= self.size or row < 0 or col >= self.size or col < 0):
            # print ("illegal (row, col) for move")
            return False;
        # There is no neighbour of the current player
        elif(self.check_for_player_flow_neighbour(row, col) == False):
            return False;
        # Case of an occupied cell
        elif (self.board[row][col] != -1 ):
            # print("square is not empty")
            return False

        return True


    def check_for_player_flow_neighbour(self, row, col):
        """
        Checks whether the player's flow is located in an adjacent square to the square [row][col]
        :param row: The given row index.
        :param col:  The given column index.
        :return: True IFF there is an adjacent square of the player's flow.
        """
        left_neighbour, right_neighbour, up_neighbour, down_neighbour = False, False, False, False
        # Checks the down neighbour
        if ((row + 1) < self.size):
            if (self.board[row + 1][col] == self.player):
                down_neighbour = True

        # Checks the up neighbour
        if ((row - 1) >= 0):
            if (self.board[row - 1][col] == self.player):
                up_neighbour = True

        # Checks the right neighbour
        if ((col + 1) < self.size):
            if (self.board[row][col + 1] == self.player):
                right_neighbour = True

        # Checks the left neighbour
        if ((col - 1) >= 0):
            if (self.board[row][col - 1] == self.player):
                left_neighbour = True

        if (up_neighbour == False and down_neighbour == False and left_neighbour == False and right_neighbour == False):
            return False
        else:
            return True

    def update_finished_agents(self):
        """
        Updates the counter of agents that already have completed their flow in the current State.
        """
        for agent in self.finished:
            if (self.finished[agent] == True):
                self.num_of_finished_agents += 1

    def is_agent_goal_state(self, agent_num):
        """
        Checks whether the current board of the State is a goal State for the agent correspond to agent_num.
        :param agent_num: The number of the agent to check for.
        :return: True IFF the correspond agent is the player and he completed his flow.
        """
        # Validates that agent_num is the number of the player
        if (self.player == agent_num):
            row, col = self.head
            if (self.targets[agent_num][0] == row and  (self.targets[agent_num][1] == col +1 or self.targets[agent_num][1] == col -1)):
                return True
            if (self.targets[agent_num][1] == col and  (self.targets[agent_num][0] == row +1 or self.targets[agent_num][0] == row -1)):
                return True

        return False


    def is_forced_move(self, row, col, player):
        """
        Checks for a forced move.
        :param row: The given row index.
        :param col:  The given column index.
        :param player: The given agent number.
        :return: True if(row, col) is the only option for player to move, False otherwise.
        """
        if(self.check_move_valid(row, col) and (self.num_of_free_neighbours(row, col) == 1)):
            return True
        return False



    def num_of_free_neighbours(self, row, col):
        """
        Returns the number of free neighbours for the square [row][col]
        :param row: The given row index.
        :param col:  The given column index.
        :return: The number of free adjacent neighbours for the square [row][col]
        """
        num_of_free_neighbors = 0;
        # checks for an up free neighbour
        if ((row + 1) < self.size):
            if (self.board[row+1][col] == FREE):
                num_of_free_neighbors += 1

        # checks for a down free neighbour
        if ((row - 1) >= 0 ):
            if (self.board[row-1][col] == FREE):
                num_of_free_neighbors += 1

        # checks for a right free neighbour
        if ((col + 1) < self.size):
            if (self.board[row][col+1] == FREE):
                num_of_free_neighbors += 1

        # checks for a left free neighbour
        if ((col - 1) >= 0 ):
            if (self.board[row][col-1] == FREE):
                num_of_free_neighbors += 1

        return num_of_free_neighbors



    def edgepoints_neighbour_didnt_finish(self, row, col):
        """
        Checks for existence of a neighbour which is an edge point for an agent who didn't complete his flow yet.
        :param row: The given row index.
        :param col:  The given column index.
        :return: True IFF there is such a neighbour
        """
        # Checks the up neighbour
        if ((row+1, col) in self.targets.values() or (row+1, col) in self.sources.values()):
            agent = self.board[row + 1][col]
            if(self.finished[agent] == False):
                return True

        # Checks the down neighbour
        if ((row-1, col) in self.targets.values() or (row-1, col) in self.sources.values()):
            agent = self.board[row - 1][col]
            if(self.finished[agent] == False):
                return True

        # Checks the right neighbour
        if ((row, col+1) in self.targets.values() or (row, col+1) in self.sources.values()):
            agent = self.board[row][col + 1]
            if(self.finished[agent] == False):
                return True

        # Checks the left neighbour
        if ((row, col-1) in self.targets.values() or (row, col-1) in self.sources.values()):
            agent = self.board[row][col - 1]
            if(self.finished[agent] == False):
                return True

        return False

    ##############################################################
    # -----------Optional moves and Performing moves------------
    ##############################################################

    def perform_move (self, row, col, agent):
        """
        Performs agent's move at square (row, col) on the current State
        :param row: The given row index.
        :param col:  The given column index.
        :param agent: The correspond agent (object) that execute the move.
        """
        # First, checks the validity of (row,col) and the agent's number
        if(not(self.check_move_valid(row,col) and (agent.player_num in range(len(self.players))))):
            print("An illegal move, was'nt played")
            return

        # updates the relevant fields of the current State
        self.board[row][col] = agent.player_num # updates the board
        self.head = (row, col) # updates the head of the agent's flow

        # checks the criteria for forced-move case
        successors = self.get_possible_moves_for_player()
        only_one_free_neighbor = (self.num_of_free_neighbours(row,col) == 1)

        # updates the g and h values
        # self.curr_empty_tiles -= 1
        # manhattan_dist = self.manhattan_distance_heur(row, col, self.targets[agent.player_num][ROW], self.targets[agent.player_num][COL])
        # self.h_value = self.curr_empty_tiles + manhattan_dist - 1
        self.h_value -= 1
        # checks for a goal state for this agent and updates the agent and this board accordingly
        if (agent.target[0] == row and agent.target[1] == col):
            agent.finished = True
            agent.complete = self
            self.finished[agent.player_num] = True
        # case of forced move - that doesn't lead to goal State
        elif (len(successors) == 1 or only_one_free_neighbor or self.is_agent_goal_state(agent.player_num)):
            pass
        elif (len(successors) > 1):
            self.g_value += 1



    def get_possible_moves_for_player(self):
        """
        Calculates all the optional valid moves for the playing agent.
        :return: List of the optional valid moves
        """
        optional_moves=[]
        row,col = self.head
        if(self.check_move_valid(row+1,col)):
            optional_moves.append([row+1,col]) #one row down
        if(self.check_move_valid(row-1,col)):
            optional_moves.append([row-1,col]) #one row up
        if(self.check_move_valid(row,col+1)):
            optional_moves.append([row,col+1]) #one col right
        if(self.check_move_valid(row,col-1)):
            optional_moves.append([row,col-1]) #one col left

        return optional_moves


    ##############################################################
    # ---------Implementation of the Comparable Interface--------
    ##############################################################

    def __eq__(self, other):
        return ((self.h_value + self.g_value) == (other.h_value + other.g_value) and self.is_same_board(other))

    def __ne__(self, other):
        return ((self.h_value + self.g_value) != (other.h_value + other.g_value))

    def __lt__(self, other):
        return ((self.h_value + self.g_value) < (other.h_value + other.g_value))

    def __le__(self, other):
        return ((self.h_value + self.g_value) <= (other.h_value + other.g_value))

    def __gt__(self, other):
        return ((self.h_value + self.g_value) > (other.h_value + other.g_value))

    def __ge__(self, other):
        return ((self.h_value + self.g_value) >= (other.h_value + other.g_value))




    def is_head_a_neighbour(self, row, col):
        """
        Checks whether the current head of the flow is a neighbour of (row, col)
        :param row: The given row index.
        :param col:  The given column index.
        :return: True IFF the current head of the flow is a neighbour of (row, col)
        """
        head_row, head_col = self.head[0], self.head[1]

        # checks all the possibilities
        if (head_row == row and (head_col == col +1 or head_col == col -1)):
            return True
        if (head_col == col and (head_row == row + 1 or head_row == row -1)):
            return True

        return False

##############################################################
# ---------------------Help Functions----------------------
##############################################################

    def print_board(self):
        """
         Prints the current board of the State.
        """
        for row in self.board:
            print(row)

    # Implementing Comparable interface
    def is_same_board(self, other):
        """
         Checks whether this State is equivalent to other.
        :param other: The State to compare with
        :return: True IFF they both contain the same number (agent) for every index
        """
        for i in range(self.size):
            for j in range(self.size):
                if (self.board[i][j] != other.board[i][j]):
                    return False
        return True


    def from_rowcol_to_position(self, row, col):
        """
         A method for converting indexes: from [row][col] format to the correspond total index
         (a number in range [0, (size*size) -1]). Raises an Exception in case of an illegal argument.
        :param row: The given row index
        :param col:  The given column index
        :return: The correspond total index
        """
        if (row >= self.size or col >= self.size):
            raise Exception("Illegal arguments for from_rowcol_to_position", "check row/col relating to self.size")
        return row*self.size + col;

    def from_position_to_rowcol (self, position):
        """
          A method for converting indexes: from total index (a number in range [0, (size*size) -1]) format to the
          correspond [row][col] square. Raises an Exception in case of an illegal argument.
        :param position: The given total index
        :return: The correspond [row][col] square
        """
        if (position >= (self.size * self.size)):
            raise Exception("Illegal arguments for from_position_to_rowcol", "The given position is out of the board sizes!!!")
        return (position // self.size, position % self.size)


    def manhattan_distance_heur(self, src_row, src_col, trg_row, trg_col):
        return (abs(trg_row - src_row) + abs (trg_col - src_col))

    def how_many_empty_tiles(self):
        num_of_empty_tiles = EMPTY
        for row in range(self.size):
            for col in range(self.size):
                num_of_empty_tiles += 1

        return num_of_empty_tiles

##############################################################
# ---------------------Testing Function----------------------
##############################################################
def board_test(size, boardStringRepresentation, colorsAndPlayers):
   state = State(size, boardStringRepresentation, colorsAndPlayers)

   state.print_board()
   print("square (0,0)")
   print(state.check_move_valid(0,0))
   print("square (2,-1)")
   print(state.check_move_valid(2, -1))
   print("square (10,13)")
   print(state.check_move_valid(10, 13))
   print("square (4,7)")
   print(state.check_move_valid(4, 7))
   print("square (5,7)")
   print(state.check_move_valid(5, 7))
   print("square (-1,3)")
   print(state.check_move_valid(-1, 3))
   print("square (11,11)")
   print(state.check_move_valid(11, 11))
   print("square (12,10)")
   print(state.check_move_valid(12, 10))

   state.perform_move(0,0,4)
   state.perform_move(0, 0,3)
   state.print_board()

   print ("optional moves for player 6")


   agent = Agent.Agent(0, state, state.sources[0], state.targets[0])
   print(state.get_possible_moves_for_player(agent))

   print (agent.is_goal_state(state))

   agent.find_successors(state)

   print("-----------------------converting positions to indexes test:-----------------")
   print("from_rowcol_to_position(0,0)")
   print(state.from_rowcol_to_position(0,0))
   print("from_rowcol_to_position(1,2)")
   print(state.from_rowcol_to_position(1,2))
   print("from_rowcol_to_position(0,2)")
   print(state.from_rowcol_to_position(0,2))
   print("from_rowcol_to_position(5,8)")
   print(state.from_rowcol_to_position(5,8))
   print("from_rowcol_to_position(5,0)")
   print(state.from_rowcol_to_position(5, 0))
   # print("from_rowcol_to_position(13,0)")
   # print(state.from_rowcol_to_position(13, 0))

   print("\n ----now from position to row-col---- \n")

   print("from_position_to_rowcol(0)")
   print(state.from_position_to_rowcol(0))
   print("from_position_to_rowcol(68)")
   print(state.from_position_to_rowcol(68))
   print("from_position_to_rowcol(59)")
   print(state.from_position_to_rowcol(59))
   print("from_position_to_rowcol(141)")
   print(state.from_position_to_rowcol(141))
   #print("from_position_to_rowcol(145)")
   #print(state.from_position_to_rowcol(145))

   print("\n ----check stroing---- \n")
   print(state.sources)
   print("\n\n")
   print(state.targets)


   print("\n g and h vals- \n")
   print("g_val is:  \n")
   print(state.g_value)
   print("\n h_val is:  \n")
   print(state.h_value)

   return state

