import copy

OCCUPIED = -2
FREE = -1
NO_REPRESENTATIVE = 1000

class RegionsMap ():
   """
    A Class represents a Regions Map that's produced by the Connected Component Labeling algorithm.
   """
   def __init__(self, board, size, orig_state):
      """
      The custom Thread Constructor.
      :param threadID: Thr ID of the identified Agent.
      :param agent: The identified Agent object.
      :param queue: A container for catching the thrown Exceptions
      """
      self.size = size
      self.orig_state = orig_state
      self.board = board
      self.dependencies = {}

    ######################################################################################
    # ---------------------Connected-component Labeling Functions-------------------------
    ######################################################################################

    #************************************* Pass_1 Function and Support Methods*****************************************

   def regions_map_init_and_first_row_calculation(self, regions_map, current_label, decrease_label):
        """
        Inits the cells of the regions map to the default value (OCCUPIED -2)and calculates the labels of the first row
        (need to check only the left neighbour).
        :param regions_map: The regions map to work on
        :param current_label: The current free label
        :param decrease_label: Boolean value, according to this flag we can deduce whether to decrease the current
        labeling value.
        :return: Updated values of the current label and decrease_label
        """
        # Init the regions map with the default value -2: represents an occupied cell.
        for row in range(self.size):
            for col in range(self.size):
                self.regions_map[row][col] = OCCUPIED

        # special case - top left corner
        content = self.board[0][0]
        if (content == FREE):  # or ((((0,0) in self.sources.values()) or ((0,0) in self.targets.values())) and (self.finished[content] == False))):
            self.regions_map[0][0] = current_label
        # Most top Row (not include the top left corner)
        for row_index in range(1, self.size):
            content = self.board[0][row_index]
            if (content == FREE):  # or ((((0,row_index) in self.sources.values()) or ((0,row_index) in self.targets.values())) and (self.finished[content] == False))):
                if (decrease_label == False):
                    self.regions_map[0][row_index] = current_label
                else:
                    current_label -= 1
                    self.regions_map[0][row_index] = current_label
                    decrease_label = False
            elif (decrease_label == False):
                decrease_label = True

        return decrease_label, current_label


    # Major Function of this section - performs pass1 on the current game board
   def produce_regions_map_pass1(self):
        """
        Performs the first pass of the Connected-component Labeling algorithm on the current board.
        For further reading - http://aishack.in/tutorials/labelling-connected-components-example/
        :return: The corresponded dependencies list
        """
        self.regions_map = copy.deepcopy(self.board)
        current_label = -3
        decrease_label = False
        self.dependencies = {}

        decrease_label, current_label = self.regions_map_init_and_first_row_calculation(self.regions_map, current_label, decrease_label)

        # Main loop - Iterates all over the board (except the first row)
        for row in range (1,self.size):
            for col in range (self.size):
                content = self.board [row][col]
                if (content == FREE):
                    # First cell in the row
                    if (col - 1 < 0):
                        # Look only up
                        if (self.regions_map[row - 1][col] != OCCUPIED):
                            self.regions_map[row][col] = self.regions_map[row - 1][col] # The up cell in the board is also empty -> we'll have the same label

                        else: # The up cell is occupied in the board, will have to get new label
                            current_label -= 1
                            self.regions_map[row][col] = current_label

                    # The general case: we look both at the up and at theleft neighbours in the regions_map
                    else:
                        # Both of the neighbours are occupied in the board, will have to get new label
                        if (self.regions_map[row - 1][col] == OCCUPIED and self.regions_map[row][col - 1] == OCCUPIED):
                            current_label -= 1
                            self.regions_map[row][col] = current_label

                        # Only the up neighbour is free in the board
                        elif (self.regions_map[row - 1][col] != OCCUPIED and self.regions_map[row][col - 1] == OCCUPIED):
                            self.regions_map[row][col] = self.regions_map[row - 1][col]
                        # Only the left neighbour is free in the board
                        elif (self.regions_map[row - 1][col] == OCCUPIED and self.regions_map[row][col - 1] != OCCUPIED):
                            self.regions_map[row][col] = self.regions_map[row][col - 1]
                        # Both the up and the left neighbours are free in the board, we'll take the minimum and ENTER A DEPENDENCY TO THE DICT.
                        else:
                            self.dependencies_updating(row, col)

        return self.dependencies

   def dependencies_updating (self, row, col):
        """
        Updates the dependencies list to the regions map.
        :param row: The given row index.
        :param col:  The given column index.
        """
        # Case that the up and left neighbours have the same regions_map value
        if (self.regions_map[row - 1][col] == self.regions_map[row][col - 1]):
            self.regions_map[row][col] = self.regions_map[row - 1][col]
        # The up and left neighbours DON'T have the same regions_map value
        else:
            minimum = min(self.regions_map[row - 1][col], self.regions_map[row][col - 1])
            maximum = max(self.regions_map[row - 1][col], self.regions_map[row][col - 1])
            self.regions_map[row][col] = maximum

            head_of_max = self.find_representative(self.dependencies, maximum)
            # case that maximum is NOT in dependencies (neither as key nor as a set member) - we'll add it as a key
            if (head_of_max == NO_REPRESENTATIVE):
                self.dependencies[maximum] = set()
                self.dependencies[maximum].add(maximum)
                head_of_max = maximum

            head_of_min = self.find_representative(self.dependencies, minimum)
            # case that minimum is NOT in the dependencies -> we'll add it to the maximum's set
            if (head_of_min == NO_REPRESENTATIVE):
                self.dependencies[head_of_max].add(minimum)
            # case that minimum is IN the dependencies(as a key or as a set member) with other head than head_of_max -> we'll unite these 2 sets
            elif (head_of_min != head_of_max):
                minimum_set = copy.deepcopy(self.dependencies[head_of_min])
                del self.dependencies[head_of_min]
                self.dependencies[head_of_max] = (self.dependencies[head_of_max] | minimum_set)


   def find_representative(self, given_depends, item):
        """
        Finds the item's representative in the given dependencies list.
        :param given_depends: A dependencies list
        :param item: A given item.
        :return: The representative of item in the dependencies list.
        """
        # case the item is the head of a set
        if (item in given_depends.keys()):
            return item

        # case the item is a member in other list
        for key_val in given_depends:
            if (item in given_depends[key_val]):
                return key_val

        # case that item is NOT in dict
        return NO_REPRESENTATIVE

   def produce_regions_map_pass2(self,dependencies):
        """
        Perform pass 2 of the  Connected-component Labeling algorithm.
        :param dependencies: The dependencies list calculated in pass 1 (a dictionary)
        :return: The set of labels after regions union (according to the dependencies list).
        """
        labels_set = set()
        # Main loop - Iterates all over the board and determines the regions
        for row in range (self.size):
            for col in range (self.size):
                if (self.regions_map[row][col] == OCCUPIED): # An occupied cell - there is nothing to do
                    pass
                else:
                    if (self.regions_map[row][col] in dependencies.keys()):
                        pass # The region of (row, col) is a representative in the dependency list
                    else: # The label in regions_map[row][col] has a dependency, lets find which
                        for key_val in dependencies.keys():
                            if (self.regions_map[row][col] in dependencies[key_val]):
                                self.regions_map[row][col]= key_val
                                break
                    # if regions_map[row][col] has no dependency (neither as a key nor as a dependence)
                    # we'll leave it with the label of itself

                    labels_set.add(self.regions_map[row][col])

        return labels_set



   def find_regions(self, row, col):
        """
        Finds the regions which are adjacent to (row, col)
        :param row: The given row index.
        :param col:  The given column index.
        :return: A set contains the adjacent regions to (row, col)
        """
        regions = set ()

        if ((row + 1) < self.size):
            if (self.regions_map[row +1][col] != OCCUPIED):
                regions.add(self.regions_map[row +1][col])
        if ((row - 1) >= 0 ):
            if (self.regions_map[row - 1][col] != OCCUPIED):
                regions.add(self.regions_map[row - 1][col])
        if ((col + 1) < self.size):
            if (self.regions_map[row][col + 1] != OCCUPIED):
                regions.add(self.regions_map[row][col + 1])
        if ((col - 1) >= 0 ):
            if (self.regions_map[row][col - 1] != OCCUPIED):
                regions.add(self.regions_map[row][col - 1])

        return regions

   def regions_lists_contains_mutual_area(self, region_list1, region_list2, agent_num):
        """
        Checks whether 2 given regions lists contain at least one mutual region.
        :param region_list1: The first given regions list
        :param region_list2: The second given regions list
        :param agent_num: The number of agent to check whether he just completed his flow, in this case there is no
        significance to the regions list.
        :return: True IFF (there is at least one mutual region among the lists OR the given agent just completed his flow).
        """
        if (self.orig_state.is_agent_goal_state(agent_num)):
            return True
        for item in region_list1:
            if (item in region_list2):
                return True

        return False