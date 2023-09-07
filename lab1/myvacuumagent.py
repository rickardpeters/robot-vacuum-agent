from lab1.liuvacuum import *
from random import randint
from math import sqrt
import numpy as np

DEBUG_OPT_DENSEWORLDMAP = False

AGENT_STATE_UNKNOWN = 0
AGENT_STATE_WALL = 1
AGENT_STATE_CLEAR = 2
AGENT_STATE_DIRT = 3
AGENT_STATE_HOME = 4

AGENT_DIRECTION_NORTH = 0
AGENT_DIRECTION_EAST = 1
AGENT_DIRECTION_SOUTH = 2
AGENT_DIRECTION_WEST = 3

def direction_to_string(cdr):
    cdr %= 4
    return  "NORTH" if cdr == AGENT_DIRECTION_NORTH else\
            "EAST"  if cdr == AGENT_DIRECTION_EAST else\
            "SOUTH" if cdr == AGENT_DIRECTION_SOUTH else\
            "WEST" #if dir == AGENT_DIRECTION_WEST

"""
Internal state of a vacuum agent
"""
class MyAgentState:

    def __init__(self, width, height):

        # Initialize perceived world state
        self.world = [[AGENT_STATE_UNKNOWN for _ in range(height)] for _ in range(width)]
        self.world[1][1] = AGENT_STATE_HOME

        # Agent internal state
        self.last_action = ACTION_NOP
        self.direction = AGENT_DIRECTION_EAST
        self.pos_x = 1
        self.pos_y = 1

        # Metadata
        self.world_width = width
        self.world_height = height

    """
    Update perceived agent location
    """
    def update_position(self, bump):
        if not bump and self.last_action == ACTION_FORWARD:
            if self.direction == AGENT_DIRECTION_EAST:
                self.pos_x += 1
            elif self.direction == AGENT_DIRECTION_SOUTH:
                self.pos_y += 1
            elif self.direction == AGENT_DIRECTION_WEST:
                self.pos_x -= 1
            elif self.direction == AGENT_DIRECTION_NORTH:
                self.pos_y -= 1

    """
    Update perceived or inferred information about a part of the world
    """
    def update_world(self, x, y, info):
        self.world[x][y] = info

    """
    Dumps a map of the world as the agent knows it
    """
    def print_world_debug(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y] == AGENT_STATE_UNKNOWN:
                    print("?" if DEBUG_OPT_DENSEWORLDMAP else " ? ", end="")
                elif self.world[x][y] == AGENT_STATE_WALL:
                    print("#" if DEBUG_OPT_DENSEWORLDMAP else " # ", end="")
                elif self.world[x][y] == AGENT_STATE_CLEAR:
                    print("." if DEBUG_OPT_DENSEWORLDMAP else " . ", end="")
                elif self.world[x][y] == AGENT_STATE_DIRT:
                    print("D" if DEBUG_OPT_DENSEWORLDMAP else " D ", end="")
                elif self.world[x][y] == AGENT_STATE_HOME:
                    print("H" if DEBUG_OPT_DENSEWORLDMAP else " H ", end="")

            print() # Newline
        print() # Delimiter post-print

"""
Vacuum agent
"""
class MyVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)
        self.initial_random_actions = 10
        self.state = MyAgentState(world_width, world_height)
        self.iteration_counter = (self.state.world_height * self.state.world_width * 4)
        self.log = log
        self.map = [[0 for _ in range(world_height)] for _ in range(world_width)]
        self.mark_perimeter()

    def move_to_random_start_position(self, bump):
        action = random()

        self.initial_random_actions -= 1
        self.state.update_position(bump)

        if action < 0.1666666:   # 1/6 chance
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            return ACTION_TURN_LEFT
        elif action < 0.3333333: # 1/6 chance
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            return ACTION_TURN_RIGHT
        else:                    # 4/6 chance
            self.state.last_action = ACTION_FORWARD
            return ACTION_FORWARD
    
    # Set perimeter to heat 100 so the agent never goes there.
    def mark_perimeter(self):
        for y in range(self.state.world_height):
            self.map[0][y] = 100
            self.map[self.state.world_height - 1][y] = 100
        for x in range(self.state.world_width):
            self.map[x][0] = 100
            self.map[x][self.state.world_width - 1] = 100

    def turn_right(self):
        self.state.direction = (self.state.direction + 1) % 4
        self.state.last_action = ACTION_TURN_RIGHT
        return ACTION_TURN_RIGHT

    def turn_left(self):
        self.state.direction = (self.state.direction - 1) % 4
        self.state.last_action = ACTION_TURN_LEFT
        return ACTION_TURN_LEFT
    
    def go_forward(self):
        self.state.last_action = ACTION_FORWARD
        return ACTION_FORWARD

    def turn_random(self):
        random_action = randint(1,2)
        if random_action == 1:
            return self.turn_right()
        elif random_action == 2:
            return self.turn_left()
    
    # Checks all tiles and returns true if they are all visited.
    def map_clear(self):
        for y in range(1,self.state.world_height - 1):
            for x in range(1,self.state.world_width - 1):
                if self.state.world[x][y] == AGENT_STATE_UNKNOWN:
                    return False
        return True
    
    # Updating heatmap by incrementing visited squares
    def update_map(self):
        if self.state.last_action == ACTION_FORWARD:
            self.map[self.state.pos_x][self.state.pos_y] += 1

    # Increases the heat of the tiles longer from home. Creates a "slope"
    def go_home(self, home):
        if home:
            self.log("Shutting down")
            self.log("Iterations left:")
            self.log(self.iteration_counter)
            self.iteration_counter = 0
            self.state.last_action = ACTION_NOP
            return ACTION_NOP
        
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                self.map[x][y] += int(sqrt(x ** 2 + y ** 2))
    
    # Agent decision making based on surrounding "heat" - how many times the agent has visited a location.
    def make_decision(self, bump, home):
        offset_left = [(-1, 0), (0, -1), (1, 0), (0, 1)][self.state.direction]
        offset_right = [(1, 0), (0, 1), (-1, 0), (0, -1)][self.state.direction]
        offset_forward = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.state.direction]
        
        surr_heat = [self.map[self.state.pos_x + offset_forward[0]][self.state.pos_y + offset_forward[1]],
                     self.map[self.state.pos_x + offset_left[0]][self.state.pos_y + offset_left[1]],
                     self.map[self.state.pos_x + offset_right[0]][self.state.pos_y + offset_right[1]]]

        if self.map_clear():
            self.go_home(home)

        if bump:
            if surr_heat[1] < surr_heat[2]:
                return self.turn_left()
            elif surr_heat[1] > surr_heat[2]:
                return self.turn_right()
            else:
                return self.turn_random()

        if surr_heat.index(min(surr_heat)) == 0:
            return self.go_forward()

        elif surr_heat.index(min(surr_heat)) == 1:
            return self.turn_left()

        elif surr_heat.index(min(surr_heat)) == 2:
            return self.turn_right()

        else:
            return self.go_forward()

    def execute(self, percept):

        ###########################
        # DO NOT MODIFY THIS CODE #
        ###########################

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Move agent to a randomly chosen initial position
        if self.initial_random_actions > 0:
            self.log("Moving to random start position ({} steps left)".format(self.initial_random_actions))
            return self.move_to_random_start_position(bump)

        # Finalize randomization by properly updating position (without subsequently changing it)
        elif self.initial_random_actions == 0:
            self.initial_random_actions -= 1
            self.state.update_position(bump)
            self.state.last_action = ACTION_SUCK
            self.log("Processing percepts after position randomization")
            return ACTION_SUCK


        ########################
        # START MODIFYING HERE #
        ########################

        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log("Performance: {}".format(self.performance))
            return ACTION_NOP

        self.log("Position: ({}, {})\t\tDirection: {}".format(self.state.pos_x, self.state.pos_y,
                                                              direction_to_string(self.state.direction)))

        self.iteration_counter -= 1

        # Track position of agent
        self.state.update_position(bump)
        self.update_map()

        if bump:
            # Get an xy-offset pair based on where the agent is facing
            offset = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.state.direction]

            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(self.state.pos_x + offset[0], self.state.pos_y + offset[1], AGENT_STATE_WALL)

            # Set the heat to 100 at the position of the wall, so the agent will never go there.
            self.map[self.state.pos_x + offset[0]][self.state.pos_y + offset[1]] = 100

        # Update perceived state of current tile
        if dirt:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_DIRT)
        else:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_CLEAR)
            
        # Debug the regular map and the heatmap
        self.state.print_world_debug()
        print(np.matrix(np.transpose(self.map)))
        print() #newline

        # Decide action
        if dirt:
            self.log("DIRT -> choosing SUCK action!")
            self.state.last_action = ACTION_SUCK
            return ACTION_SUCK
        else:
            return self.make_decision(bump, home)