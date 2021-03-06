from constants import *
from utils import *
from core import *

import pdb
import copy
from functools import reduce

from statesactions import *


############################
## HELPERS

### Return true if the given state object is a goal. Goal is a State object too.
def is_goal(state, goal):
    return len(goal.propositions.difference(state.propositions)) == 0


### Return true if the given state is in a set of states.
def state_in_set(state, set_of_states):
    for s in set_of_states:
        if s.propositions != state.propositions:
            return False
    return True


### For debugging, print each state in a list of states
def print_states(states):
    for s in states:
        ca = None
        if s.causing_action is not None:
            ca = s.causing_action.name
        print(s.id, s.propositions, ca, s.get_g(), s.get_h(), s.get_f())


############################
### Planner
###
### The planner knows how to generate a plan using a-star and heuristic search planning.
### It also knows how to execute plans in a continuous, time environment.

class Planner():

    def __init__(self):
        self.running = False  # is the planner running?
        self.world = None  # pointer back to the world
        self.the_plan = []  # the plan (when generated)
        self.initial_state = None  # Initial state (State object)
        self.goal_state = None  # Goal state (State object)
        self.actions = []  # list of actions (Action objects)

    ### Start running
    def start(self):
        self.running = True

    ### Stop running
    def stop(self):
        self.running = False

    ### Called every tick. Executes the plan if there is one
    def update(self, delta=0):
        result = False  # default return value
        if self.running and len(self.the_plan) > 0:
            # I have a plan, so execute the first action in the plan
            self.the_plan[0].agent = self
            result = self.the_plan[0].execute(delta)
            if result == False:
                # action failed
                print("AGENT FAILED")
                self.the_plan = []
            elif result == True:
                # action succeeded
                done_action = self.the_plan.pop(0)
                print("ACTION", done_action.name, "SUCCEEDED")
                done_action.reset()
        # If the result is None, the action is still executing
        return result

    ### Call back from Action class. Pass through to world
    def check_preconditions(self, preconds):
        if self.world is not None:
            return self.world.check_preconditions(preconds)
        return False

    ### Call back from Action class. Pass through to world
    def get_x_y_for_label(self, label):
        if self.world is not None:
            return self.world.get_x_y_for_label(label)
        return None

    ### Call back from Action class. Pass through to world
    def trigger(self, action):
        if self.world is not None:
            return self.world.trigger(action)
        return False

    ### Generate a plan. Init and goal are State objects. Actions is a list of Action objects
    ### Return the plan and the closed list
    def astar(self, init, goal, actions):
        '''
        :param init:
        :param goal:
        :param actions:
        :return:
        '''
        plan = []  # the final plan
        open = []  # the open list (priority queue) holding State objects
        closed = []  # the closed list (already visited states). Holds state objects
        ### YOUR CODE GOES HERE
        print(init.propositions)
        open.append(init)

        while len(open) > 0:
            current = min(open, key=State.get_f)

            open.remove(current)
            closed.append(current)

            if is_goal(current, goal):
                break
            else:
                for action in actions:
                    precondition = action.preconditions
                    if precondition.issubset(current.propositions):
                        new_proposition = current.propositions.difference(action.delete_list)
                        new_proposition = new_proposition.union(action.add_list)

                        new_state = State(new_proposition)
                        if new_state in closed:
                            break
                        new_state.g = current.g + action.cost
                        new_state.h = self.compute_heuristic(new_state, goal, actions)
                        new_state.parent = current
                        new_state.causing_action = action
                        open.append(new_state)

        # curr = goal
        while current.parent is not None:
            plan.append(current.causing_action)
            current = current.parent

        plan.reverse()
        ### CODE ABOVE
        return plan, closed

    ### Compute the heuristic value of the current state using the HSP technique.
    ### Current_state and goal_state are State objects.
    def compute_heuristic(self, current_state, goal_state, actions):
        actions = copy.deepcopy(actions)  # Make a deep copy just in case
        h = 0  # heuristic value to return
        ### YOUR CODE BELOW

        # pop
        # judge end?

        # current action

        # dict for prop cost

        # 算出进入的最大p
        dummy_start = Action('dummy_start', preconditions=[], add_list=current_state.propositions, delete_list=[], cost=0)
        dummy_end = Action('dummy_end', preconditions=goal_state.propositions, add_list=[], delete_list=[])

        nodes = [dummy_start, dummy_end]
        nodes = nodes + actions
        edges = []

        for node1 in nodes:
            for node2 in nodes:
                if node1 != node2:
                    for prop in node2.preconditions:
                        if prop in node1.add_list:
                            edges.append((node1, prop, node2))

        queue = [dummy_start]
        visited = []
        dist = {}

        while len(queue) > 0:
            curr = queue.pop()
            visited.append(curr)
            curr_prop = set()
            for v in visited:
                curr_prop = curr_prop.union(v.add_list)

            for edge in edges:
                if edge[0] in visited and edge[2] not in visited:
                    if len(edge[0].preconditions) > 0:
                        # print(e[0].name, 'preconditions', e[0].preconditions)
                        value = 0
                        for pre in edge[0].preconditions:
                            if dist[pre] > value:
                                value = dist[pre]
                        value = value + edge[0].cost

                        if edge[1] in dist:
                            old_value = dist.get(edge[1])
                            if value > old_value:
                                dist[edge[1]] = value
                        else:
                            dist[edge[1]] = value

                    else:
                        dist[edge[1]] = edge[0].cost

                    if edge[2].preconditions.issubset(curr_prop):
                        queue.append(edge[2])

        for prop in dummy_end.preconditions:
            if prop in dist:
                if dist[prop] > h:
                    h = dist[prop]
        ### YOUR CODE ABOVE
        return h

    def construct_edges(self, actions):
        edges = []
        for i in range(len(actions)):
            for j in range(len(actions)):
                if j == i:
                    continue
                action1 = actions[i]
                action2 = actions[j]
                # print(action1.name + " " + action2.name)
                for add_list1 in action1.add_list:
                    if add_list1 in action2.preconditions:
                        edge = [action1, add_list1, action2]
                        edges.append(edge)
        return edges
