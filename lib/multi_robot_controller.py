#!/usr/bin/env python3
from map import Map
from junction import Junction
from road import Road
from collections import deque
'''
Represents a path that an agent will follow.

Allows transactional path traversal down roads and through junctions
'''
class Path:
    '''
    Instantiate a new path, given a starting location, a list of roads, and a list of junctions.

    The lists of roads and junctions should be ordered
    '''
    def __init__(self, start_loc: Cell, roads: list[Road], junctions: list[Junction], priority: int): #TODO: Update to load roads from map based on junctions, add parking spot
        self.priority = priority
        self.pending = True
        self.prior_loc = start_loc
        self.current_loc = start_loc
        # Array to keep cells we're traversing on the grid graph
        self.cells = deque()
        juncqueue = deque(junctions)
        for r in roads:
            self.cells.extend(r.path) # TODO: Check path direction
            self.cells.append(junqueue.pop) # TODO: Ensure data structures are compatible here

    '''
    Updates the path based on where the agent wants to move next, if such movement is possible.

    Accepts a callback function that tells the method whether or not the desired course of action is possible,
    if this function returns null then we have a no-op
    '''
    def iterate(self):
        self._mark_pending()
        self.prior_loc = self.current_loc
        self.current_loc = self.cells.peek()
        return self.current_loc

    '''
    Mark the current iteration as finished.

    Pops the next location off the queue, opening us for further iteration.
    '''
    def finalize(self):
        self.cells.pop()
        self._mark_finalized()

    '''
    Roll back the current iteration to the previous state. Only called when the course of action for this path conflicts with another
    '''
    def rollback(self):
        self.current_loc = self.prior_loc
        self._mark_finalized()

    def _mark_pending(self):
        assert not self.pending
        self.pending = True

    def _mark_finalized(self):
        assert self.pending
        self.pending = False

class MultiRobotController:
    def __init__(self, map: Map):
        self.map = map
        self.paths = [] # TODO: Convert to sorted list by priority

    def register_path(self, path):
        # Register a path to follow, adds to the list of paths the controller needs to check each cycle
        self.paths.append(path)

    def deregister_path(self):
        # Deregister an agent from path following
        pass

    def iterate(self):
        locations = HashMap() # TODO: Hashmap of cells to paths
        for p in self.paths:
            if not locations.insert(p.iterate()):
                p.rollback()
            else:
                p.finalize()
