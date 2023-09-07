from random import randint
from lab1.liuvacuum import *

"""
Random Vacuum agent
"""
class RandomVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)
        self.iteration_counter = 100
        self.log = log

    def execute(self, percept):

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log("Performance: {}".format(self.performance))
            return ACTION_NOP

        self.iteration_counter -= 1

        random_action = randint(1,8)
        #self.log("Rand: {}".format(random_action))
        if dirt:
            self.log("DIRT -> choosing SUCK action!")
            return ACTION_SUCK
        else:
            if random_action == 1:
                self.log("TurnLeft!")
                return ACTION_TURN_LEFT
            elif random_action == 2:
                self.log("TurnRight!")
                return ACTION_TURN_RIGHT
            else:
                self.log("Forward!")
                return ACTION_FORWARD
