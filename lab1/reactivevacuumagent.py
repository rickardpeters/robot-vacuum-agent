from random import randint
from lab1.liuvacuum import *

"""
Simple Reactive Vacuum agent
"""
class ReactiveVacuumAgent(Agent):

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
                self.alive = False
            return ACTION_NOP

        self.iteration_counter -= 1

        random_action = randint(1,8)
        #self.log("Rand: {}".format(random_action))
        if dirt:
            self.log("DIRT -> choosing SUCK action!")
            return ACTION_SUCK
        else:
            if bump:
                random_turn_action = randint(1,2)
                if random_turn_action == 1:
                    self.log("BUMP -> choosing TURN_LEFT action!")
                    return ACTION_TURN_LEFT
                else:
                    self.log("BUMP -> choosing TURN_RIGHT action!")
                    return ACTION_TURN_RIGHT
            else:
                return ACTION_FORWARD
