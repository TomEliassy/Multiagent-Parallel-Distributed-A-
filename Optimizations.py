import copy
import RegionsMap

ROW = 0
COL = 1
FREE = -1
NO_FREE_NEIGHBOUR = 0
SINGLE_FREE_NEIGHBOUR = 1
NO_REGIONS = 0
EMPTY = 0
NUMBER_OF_STRANDED_COLORS = 0
EDGE = 0



##############################################################
# ------------------------Optimizations------------------------
##############################################################


def detect_blocked_agent(state, player_num):
    """
    Checks whether there is an agent who hasn't played yet and his source/target square is blocked.
    :param state: The given State to check.
    :return: True IFF there is an agent who hasn't played yet and his source/target square is blocked
    """
    for agent_num in state.finished:
        if (state.finished[agent_num] == False and agent_num != player_num):
            if (state.num_of_free_neighbours((state.sources[agent_num])[0],
                                             (state.sources[agent_num])[1]) == 0 or state.num_of_free_neighbours(
                    (state.targets[agent_num])[0], (state.targets[agent_num])[1]) == 0):
                return True
    return False


def detect_dead_end(state):
    """
    Checks whether as a result from the last move a dead-end cell (an inaccesible neighbour) was created
    :param state: The State contains the last move that was executed.
    :return: True IFF there is a dead-end in the given State.
    """
    for row in range(state.size):
        for col in range(state.size):
            if (state.board[row][col] == FREE and state.num_of_free_neighbours(row, col) == NO_FREE_NEIGHBOUR):
                if (not (state.is_head_a_neighbour(row, col) or state.edgepoints_neighbour_didnt_finish(row, col))):
                    return True
            if (state.board[row][col] == FREE and state.num_of_free_neighbours(row, col) == SINGLE_FREE_NEIGHBOUR):
                if (not (state.edgepoints_neighbour_didnt_finish(row, col) or state.is_head_a_neighbour(row, col))):
                    return True
    return False


def check_how_many_stranded_colors(state, is_bottleneck_check):
    """
    Calculates how many stranded colors there are in the given State.
    :param state: The given State
    :param is_bottleneck_check: Indicates whether this function was called by "check_for_bottleneck" function or
    by "check_for_stranded_color_and_region".
    :return:The number of stranded colors in the given State.
    """
    state.regions_map = RegionsMap.RegionsMap(state.board, state.size, state)
    # Connected-component Labeling
    dependencies = state.regions_map.produce_regions_map_pass1()
    labels_set = state.regions_map.produce_regions_map_pass2(dependencies)
    stranded_colors = 0
    regions_contains_edgepoints = set()

    # checks for stranded colors
    for color in state.finished:
        if (state.finished[color] == False):
            if (is_bottleneck_check == False or (is_bottleneck_check == True and state.player != color)):
                # understanding the origin of the flow.
                if (state.player != color):
                    current_row = state.sources[color][ROW]
                    current_col = state.sources[color][COL]
                else:
                    current_row = state.head[ROW]
                    current_col = state.head[COL]
                target_row = state.targets[color][ROW]
                target_col = state.targets[color][COL]
                # finding the regions of the flow's target and the flow's source/head (in case of the current player).
                current_region_lst = state.regions_map.find_regions(current_row, current_col)
                target_region_lst = state.regions_map.find_regions(target_row, target_col)
                # checks for a stranded color using sets intersection
                if (
                not state.regions_map.regions_lists_contains_mutual_area(current_region_lst, target_region_lst, color)):
                    stranded_colors += 1
                else:
                    # updates the regions_contains_edgepoints set about regions of not-stranded colors.
                    for region in current_region_lst:
                        regions_contains_edgepoints.add(region)
                    for region in target_region_lst:
                        regions_contains_edgepoints.add(region)

    return stranded_colors, regions_contains_edgepoints, labels_set


# will check after an agent completed his flow (for each non-completed color there must be a region contains it's source as well at it's target)
def check_for_stranded_color_and_region(state):
    """
    Checks for stranded color and stranded region. for further reading: https://mzucker.github.io/2016/08/28/flow-solver.html
    :param state: The given state to check.
    :return: True IFF there is a stranded color or a stranded region
    """
    # checks for stranded COLORS
    stranded_colors, regions_contains_edgepoints, labels_set = check_how_many_stranded_colors(state, False)
    if (stranded_colors > NO_REGIONS):
        return True

    # checks for stranded REGION
    if (len(labels_set - regions_contains_edgepoints) > EMPTY):
        return True

    return False


def check_for_bottleneck(state, agent):
    """
    Checks for a bottleneck existence respecting a given state.
    :param state: The given state to check.
    :return: True IFF there is a in state
    """
    # Initialization
    up_free, down_free, left_free, right_free = 1, 1, 1, 1
    row, col = state.head[ROW], state.head[COL]
    number_of_stranded_colors = 0

    # checks the up direction
    up_board = copy.deepcopy(state)
    while (row - up_free >= EDGE and up_board.board[row - up_free][col] == FREE):
        up_board.perform_move(row - up_free, col, agent)
        up_free += 1
    number_of_stranded_colors = check_how_many_stranded_colors(up_board, True)[NUMBER_OF_STRANDED_COLORS]
    if (number_of_stranded_colors > up_free - 1):
        return True

    # checks the down direction
    down_board = copy.deepcopy(state)
    while (row + down_free <= state.size - 1 and down_board.board[row + down_free][col] == FREE):
        down_board.perform_move(row + down_free, col, agent)
        down_free += 1
    number_of_stranded_colors = check_how_many_stranded_colors(down_board, True)[NUMBER_OF_STRANDED_COLORS]
    if (number_of_stranded_colors > down_free - 1):
        return True

    # checks the right direction
    right_board = copy.deepcopy(state)
    while (col + right_free <= state.size - 1 and right_board.board[row][col + right_free] == FREE):
        right_board.perform_move(row, col + right_free, agent)
        right_free += 1
    number_of_stranded_colors = check_how_many_stranded_colors(right_board, True)[NUMBER_OF_STRANDED_COLORS]
    if (number_of_stranded_colors > right_free - 1):
        return True

    # checks the left direction
    left_board = copy.deepcopy(state)
    while (col - left_free >= EDGE and left_board.board[row][col - left_free] == FREE):
        left_board.perform_move(row, col - left_free, agent)
        left_free += 1
    number_of_stranded_colors = check_how_many_stranded_colors(left_board, True)[NUMBER_OF_STRANDED_COLORS]
    if (number_of_stranded_colors > left_free - 1):
        return True

    return False
