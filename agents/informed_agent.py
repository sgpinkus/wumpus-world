#!/usr/bin/env python
'''
Informed exploration similar to A*. A frontier of all possible next moves is maintained and the best chosen. cost function
is expected cost of visiting target location plus the cost of getting there. A complication is the figuring out how to
get to a target location. Simple approach used here is to just backtrack. Bu that means backtracking through any pits it
visited. The optimal approach would be A* search (not exploration) to every possible target location, but that's also
more expensive. This agent assumes it knows the result location of every move as an offset from the current location
apriori (i.e. it knows NHood.map).

Agent won't risk visiting wumpus but will visit a pit if no provably safe options left (pits don't kill in this world).
'''
import math
from collections import OrderedDict
import logging
from operator import itemgetter
from utils import Runner, BaseAgent
import directions as d

logging.basicConfig()
logger = logging.getLogger('wumpus')
logger.setLevel(logging.INFO)

NHood = d.Hood4

class PickStrategy():
  def __init__(self, agent):
    pass

  def move(self, agent):
    if 'G' in agent.current_cell:
      return { 'type': 'PICK', 'payload': { 'what': 'G' } }


class IDFEAgent(BaseAgent):
  def __init__(self):
    self.cost_factors = {
      'W': 1e5,
      'P': 1e3,
      'G': -1e3
    }
    self.model: dict[tuple[int, int], list[str]] = {} # kb of observations of static things in the world.
    self.current_cell = None
    self.current_percept = None
    self.current_agent_state = None # location, score, and other agent meta provided by server.
    # Record unique path to every node we visit when first visiting it. This is used to find a safe path between any two visited nodes.
    self.paths: dict[tuple[int, int], str] = {}
    # Every time visit a new node, add all available move action to this global priority queue. Next move is popped then we
    # navigate from the current nod to the target node and then make the move.
    # There is no need to keep a record for back tracking.
    self.frontier: OrderedDict[tuple[tuple[int, int], str], int] = OrderedDict()
    self.last_move_direction: str = ''
    self.current_path = ''
    self.preset_path = []
    self.preset_move = None

  def __str__(self):
    _str = self.map_str()
    _frontier_str = '; '.join([f'({_move_str(l)}={v}' for l, v in self.frontier.items()])
    return _str + str(
      f"current_location\t{self.current_location}\n"
      f"frontier\t{_frontier_str}\n"
      f"current_path\t{self.current_path}\n"
      f"preset_path\t{self.preset_path}\n"
      f"current_percept\t{self.current_percept}\n"
      f"model\t{self.model}"
    )

  def map_str(self):
    n = 10
    _str = ''
    for y in range(n):
      for x in range(n):
        symbols = []
        if (x,y) in self.model:
          symbols.extend([k for k, v in self.model[(x,y)].items() if v and v > 0])
          if self.current_location == (x,y):
            symbols.append('A')
        (o, c) = ('[', ']') if self.visited((x,y)) else ('|', '|') if self.on_frontier((x,y)) else (' ', ' ')
        _str += '{o}{x:<8}{c}'.format(x=''.join(symbols), o=o, c=c)
      _str += '\n'
    return _str


  @property
  def current_location(self):
    return tuple(self.current_agent_state['location'])

  def percept(self, p):
    ''' A percept is { percept: string[], cell: string[], agent: Agent }. '''
    def set_it(v: dict, k, default = {}): # Pedantic KeyError worst part of Python ..
      if k not in v:
        v[k] = default.copy()
    self.current_cell, self.current_percept, self.current_agent_state = itemgetter('cell', 'percept', 'agent')(p)
    # Update model
    known_things = ['W', 'P']
    sense_map = { 'S': 'W', 'B': 'P' }
    set_it(self.model, self.current_location)
    for thing in known_things:
      self.model[self.current_location][thing] = 1.0 if thing in self.current_cell else 0.0
    for sense, thing in sense_map.items():
      for l in NHood.neighbour_of_list(self.current_location):
        set_it(self.model, l)
        if sense in self.current_percept:
          self.model[self.current_location][sense] = 1.0
          if thing not in self.model[l]:
            self.model[l][thing] = 0.25
        else:
            self.model[l][thing] = 0.0

  def turn(self):
    print('##### TURN ##########')
    self.frontier_costs() # Done early for debug.
    print(f'have_preset_path={bool(len(self.preset_path))}, have_preset_move={bool(self.preset_move)}')
    print(self)
    if 'G' in agent.current_cell:
      return { 'type': 'PICK', 'payload': { 'what': 'G' } }
    if not self.visited(self.current_location): # Have visited.
      self.add_current_location_to_frontier()
      self.current_path += self.last_move_direction
      self.paths[self.current_location] = self.current_path
    else:
      self.current_path = self.paths[self.current_location]
    if len(self.preset_path):
      next_move_direction = self.preset_path.pop()
      return _move(next_move_direction)
    elif self.preset_move:
      next_move_direction = self.preset_move
      self.preset_move = None
      return _move(next_move_direction)
    else:
      (next_move_location, next_move_direction, score) = self._pop_next_move()
      while next_move_location and self.visited(NHood.next(next_move_location, next_move_direction)):
        print('already visited', NHood.next(next_move_location, next_move_direction))
        (next_move_location, next_move_direction, score) = self._pop_next_move()
      print('next_move', _move_str((next_move_location, next_move_direction)) if next_move_location else '-')
      if next_move_location:
        self.last_move_direction = next_move_direction
        if self.current_location == next_move_location:
          return _move(next_move_direction)
        else: # Navigate to next_move_location then take next_move_direction move.
          self.preset_path = self.known_path(self.current_location, next_move_location)
          self.preset_move = next_move_direction # We could just tac this onto preset_path but it's confusing.
          next_move_direction = self.preset_path.pop()
          return _move(next_move_direction)
      else:
        logger.info('Out of moves')
        if self.current_location != (0, 0):
          logger.info('Heading home')
          self.preset_path = self.known_path(self.current_location, (0, 0))
          next_move_direction = self.preset_path.pop()
          return _move(next_move_direction)
        else:
          return None

  def visited(self, l):
    return l in self.paths.keys()

  def on_frontier(self, l):
    return l in [NHood.next(x[0], x[1]) for x in self.frontier.keys()]

  def known_path(self, a, b):
    ''' Returns path travelled a to b in reversed order (so can pop next).'''
    if a == b:
      return []
    diff = (b[0] - a[0], b[1] - a[1])
    if diff in NHood.inversed.keys():
      return [NHood.inversed[diff]]
    if (a not in self.paths) or (b not in self.paths):
      return None
    path_a = self.paths[a]
    path_b = self.paths[b]
    return d.known_path(path_a, path_b, NHood)

  def add_current_location_to_frontier(self):
    ''' Assumes agent knows implicitly the location offset outcome moves. Means don't go back to where we just came from. '''
    adjacent = NHood.neighbour_of_dict(self.current_location)
    for d, l in adjacent.items():
      if l not in self.paths.keys():
        self.frontier[(self.current_location, d)] = 0

  def _pop_next_move(self):
    self.frontier_costs()
    if not len(self.frontier):
      return (None, None, None)
    best_score = math.inf
    best_move = (None, None, None)
    for ((l, d), score) in self.frontier.items():
      if score < best_score:
        best_score = score
        best_move = (l, d)
    if best_score >= 1e3:
      return (None, None, None)
    self.frontier.pop(best_move)
    return (*best_move, best_score)

  def frontier_costs(self):
    ''' Assign cost = travel_cost + visit_cost to every possible next move on frontier. Assumes travel is along the
    previously travelled path current location to frontier location.
    '''
    for ((l, d), x) in self.frontier.items():
      cost = self.move_cost(l, d)
      destination_location = NHood.next(l, d)
      if destination_location not in self.model:
         self.frontier[(l, d)] = math.inf
      else:
        _path = self.known_path(self.current_location, l)
        path_cost = self.path_cost(self.current_location, _path) + 1 if _path != None else math.inf
        destination_cost = 0
        for thing, factor in self.cost_factors.items():
          if thing in self.model[destination_location]:
            destination_cost += factor * self.model[destination_location][thing]
        self.frontier[(l, d)] = path_cost + destination_cost

  def move_cost(self, l, d):
    ''' Rank a location (which should be represented in model) based on distance and heursitic probability of bad things. '''

  def path_cost(self, l, path):
    next = l
    cost = 0
    for d in reversed(path):
      next = NHood.next(next, d)
      cost += self.location_cost(next) + 1
    return cost

  def location_cost(self, l):
    cost = 0
    if l in self.model:
      for thing, factor in self.cost_factors.items():
        if thing in self.model[l]:
          cost += factor * self.model[l][thing]
    return cost


def _move(move):
  return { 'type': 'MOVE', 'payload': { 'direction': move } }


def _move_str(l):
  return f'({l[0][0]},{l[0][1]},{l[1]})'


if __name__ == '__main__':
  agent = IDFEAgent()
  runner = Runner(agent)
  runner.run()

