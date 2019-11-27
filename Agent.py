import queue
import Board
import Optimizations
import copy
import FlowFreeThreads
from threading import Lock, Semaphore, Event,BoundedSemaphore
import signal

FREE = -1
STATE = 1
EMPTY = 0
NO_REGIONS = 0
EVERYONE_FINISHED = 0
NO_FREE_NEIGHBOUR = 0
SINGLE_FREE_NEIGHBOUR = 1
ROW = 0
COL = 1
NUMBER_OF_STRANDED_COLORS = 0
EDGE = 0

agents = {}
print_mutex = Lock()

global sem
sem = BoundedSemaphore(value = 1)
inter_agents_finished_states = {}


# A global function to sum the total expanded nodes of all the agents.
def get_total_expanded_nodes():
    """
    Sums the total expanded nodes of all the agents.
    :return: The calculated sum.
    """
    total_expanded_nodes = 0
    for agent_num in agents:
        total_expanded_nodes += agents[agent_num].expanded_states
        print("Agent " + str(agent_num) + " Expanded " + str(agents[agent_num].expanded_states) + " nodes")

    return total_expanded_nodes

class Agent:
    """
    A class represents a player (color) in the game. Every player has to complete a flow from his unique source square
    to his unique target square without interrupting the other agents (players/colors). The agent uses A* search in
    order to calculate his moves. For every agent we will store the following Attributes:
    - openList: A minimum priority queue contains the States that the agent already achieved and still were not expanded.
     It is ordered according to the f = g+ h values of the States: g value - How many moves the current agent performed
     (not including forced moves and reaching his target moves). h value - The number of empty squares in the State's
     board.
    - closedList: A list contains the States that have already been expanded.
    - finished & globalGoalState: Boolean variables indicate whether the current agent completed his flow and whether
      a solution to the puzzle (composed of the completed flows of all the agents) was found respectively.
    - player_num: A unique number that is identified with the agent's flow.
    - current_state: The State that the agent is now expanding.
    - source & target: Stores the source's square coordinates and the target's square coordinates respectively.
    - board_complete_own_path: A State contains the last calculated board with a completed flow of the current agent.
    - expanded_states: Counts the expanded States (nodes) by this agent.
    - waking_event: An Event instance from the "threading" module. It is responsible to notify the current agent that
      there is a State (node) to expand or that a global goal State was reached in case that the current agent's thread
      is sleeping.
    """

    #------------------------------------------------Constructor-------------------------------------------------------
    def __init__(self, player_num, init_state, source_point, target_point):

        self.openList = queue.PriorityQueue()
        self.closedList = []
        self.finished = False
        self.globalGoalState = False
        self.player_num = player_num
        self.curr_state = init_state
        self.source = source_point
        self.target = target_point
        self.curr_state.set_head(*source_point)
        self.board_complete_own_path = None
        self.expanded_states = 0
        self.waking_event = Event()
        self.statesFromOtherAgents_closedList = []

    # ------------------------------------------Methods for finding Goal state-----------------------------------------

    def is_global_goal_state(self, stat):
        if not self.all_players_played(stat):
            return False
        if not self.no_empty_squares(stat):
            return False

        return True


    def all_players_played(self, stat):
        for player in stat.finished:
            if (stat.finished[player] == False):
                return False
        return True

    def no_empty_squares(self, stat):
        for i in range(stat.size):
            for j in range(stat.size):
                if (stat.board[i][j] == FREE):
                    return False
        return True

    ##############################################################
    # ---------------------Multiagent A* API----------------------
    ##############################################################
    # The Major - Multiagent A* method
    def multiagent_astar(self):
        """
        Performs the Multiagent A* algorithm. Runs unless a (global) solution to the puzzle has been found.
        """
        # First expanding
        self.expand(self.curr_state)
        self.expanded_states += 1

        # Major loop- runs until the solution's finding
        while (not self.globalGoalState):
            got_state_from_dict = False
            # trying to get a State contains other agents' completed flows
            sem.acquire() # Avoiding mutual access to the shared resource contains completed States of the other agents.
            # Checks whether other agents posted State/s for this agent to complete his flow
            if (inter_agents_finished_states[self.player_num].qsize() > EMPTY):
                self.curr_state = inter_agents_finished_states[self.player_num].get()[STATE]
                got_state_from_dict = True
                # DEBUG: self.curr_state.print_board()
                # # DEBUG:
                # print("Agent " + str(self.player_num) + " Expanded " + str(self.expanded_states) + " nodes")
                # if (self.expanded_states > 1000):
                #     print("Agent " + str(self.player_num) + " Expanded more than 1000 nodes")
            sem.release()

            if (got_state_from_dict): #and (not(self.curr_state in self.statesFromOtherAgents_closedList))):
                self.statesFromOtherAgents_closedList.append(self.curr_state)
                self.expand(self.curr_state)
                self.expanded_states += 1
            else: # There is no State from the shared resource for now - Expand a State(node) from the agent's openList
                if (self.openList.qsize() > EMPTY):
                    self.curr_state = self.openList.get()[1]
                    #if (not(self.curr_state in self.closedList)):
                    self.expand(self.curr_state)
                    self.expanded_states += 1
                else: # openList is empty - going to sleep
                    self.waking_event.clear()
                    self.waking_event.wait()


    def expand(self, state):
        """
        Expands the agent's current State. Broadcasts an expanded State to the other agents if it contains a complete
        flow of this agent.
        :param state: The agent's current State
        :return: Exits this function and notifies the other agents in case that a global goal State is found.
        """
        self.closedList.append(state) # Marks state as visited
        # In case that we reached to a global goal state
        if (state.is_agent_goal_state(self.player_num)):
            return

        # General case, we are not in a global goal state. We will generate the successors of the current state.
        successors = self.find_successors(state)
        for s in successors:
            if ((s not in self.closedList) or (state.g_value + state.h_value > s.g_value + s.h_value)):
                self.openList.put((s.g_value + s.h_value, s))

        # In case that the last action was public i.e -this- agent finished his path
        if (self.finished):
            self.finished = False
            # Broadcasts the state to the agents who hasn't played yet
            self.broadcast_miss_agents()



    def find_successors(self,state):
        """
        Calculates the legal successors of the given State- A legal successor is free of: dead-end, region stranded,
        color stranded and bottleneck.
        Uses fast-forwarding as possible.
        :param state: The given State object.
        :return: A list contains legal successors of the given State
        """
        optional_moves = state.get_possible_moves_for_player()

        # Fast-forwarding: trying to advance the given State as long as there are only forced moves.
        while (len(optional_moves) == 1):
            state.perform_move(optional_moves[0][0], optional_moves[0][1], self)
            state.dependencies = {}
            self.expanded_states += 1
            if(self.process_state(state)):
                optional_moves.remove(optional_moves[0])
            else:
                optional_moves = state.get_possible_moves_for_player()

        successors = [] #list of the possible next states
        for move in optional_moves:
            successor = copy.deepcopy(state)
            successor.perform_move(*move, self) # The '*' unpacks the row,col which are stored in move
            #----------------------------------------------- prints for DEBUG-----------------------------------------

            # print("A successor with optional move for player " + str(self.player_num) + " is square " + str(move[0]) + "," + str(move[1]) + "\n")
            # s.print_board()
            # print("\n")
            # print("g_val is:  \n")
            # print(s.g_value)
            # print("\n h_val is:  \n")
            # print(s.h_value)
            # print("\n")

            # checking for dead-end, region stranded, color stranded and bottleneck as a result from the last move
            if(self.process_state(successor)):
                pass # The successor was already treated and eliminated (reducing the branching factor)
            else:
                successors.append(successor)
        return successors



    def process_state(self, state):
        """
        Checks whether the given State contains dead-end, region stranded, color stranded or bottleneck (as a part of
        reducing the branching factor). In case of an agent's goal State for this agent, it updates the relevant fields.
        :param state: The given State
        :return: True if there is a dead-end, region stranded, color stranded, bottleneck or this agent's goal State,
        False - otherwise.
        """
        # checks for dead-end, region stranded, color stranded or bottleneck
        try:
            if (Optimizations.detect_blocked_agent(state, self.player_num) or Optimizations.detect_dead_end(state) or Optimizations.check_for_stranded_color_and_region(state)
                or Optimizations.check_for_bottleneck(state, self)):
                # print_mutex.acquire()
                # print ("\nThe following is a bottleneck state: \n")
                # state.print_board()
                # print_mutex.release()
                self.closedList.append(state)
                return True
        except Exception as e:
            print("errorno: " + str(e))
        # case of reaching self-goal state (target)
        if state.is_agent_goal_state(self.player_num):
            state.finished[self.player_num] = True
            state.update_finished_agents()
            self.closedList.append(self.curr_state)
            self.board_complete_own_path = copy.deepcopy(state)
            self.finished = True

            return True

        return False

        
    def broadcast_miss_agents(self):
        """
        Updates the agents that haven't played yet using the shared resource (dictionary) by sending them a copy with the
        complete flow of this agent. Init. the relevant fields in the copied States for them.
        """
        not_finished = 0 # counts the agents that haven't played yet. not_finished == 0 <=> global goal state
        sem.acquire()
        #DEBUG prints
        # print("\n " + " achieve LOCAL goal state for player "+ str(self.player_num) +" with board- " + "    \n")
        # self.board_complete_own_path.print_board()

        # Loop iterates over the agents who haven't played yet on the board_complete_own_path State
        for agent_num in self.board_complete_own_path.finished:
            if (self.board_complete_own_path.finished[agent_num] == False):
                not_finished += 1
                state_clone = copy.deepcopy(self.board_complete_own_path)
                state_clone.g_value = 0  # In order that the other agents will prioritize this State
                state_clone.dependencies = {}
                state_clone.set_head(*self.board_complete_own_path.sources[agent_num]) # also determines the player number
                state_clone.finished[self.player_num] = True

                # updates the shared resource
                global inter_agents_finished_states
                inter_agents_finished_states[agent_num].put((state_clone.g_value + state_clone.h_value, state_clone))

                agents[agent_num].waking_event.set() # notifies an agent that hasn't played yet on the current board

        sem.release()
        # checks for a global goal State
        if (not_finished == EVERYONE_FINISHED):
            self.globalGoalState = True
            self.update_agents_about_goal_state(self.board_complete_own_path)



    def update_agents_about_goal_state(self,goal_stat):
        """
        Updates all the agents about finding the solution.
        :param goal_stat: The reached global goal State
        """
        global agents
        for agent_num in agents:
            agents[agent_num].globalGoalState = True
            agents[agent_num].waking_event.set()

        Board.update_global_goal_mutex.acquire()
        Board.goal_state = goal_stat
        Board.update_global_goal_mutex.release()


        FlowFreeThreads.service_shutdown(signal.SIGTERM)


