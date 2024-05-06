#!/usr/bin/env python
'''
Depth First Exploring agent. Once entire map is explored it just stops. Agent visits many of the same locations
over and over because of [non]assumptions:

  - Assumes: Same set of movements is available in every state and we know them apriori.
  - Assumes: Moves are reverisble and we know what the reverse move is.
  - Assumes: The same move in the same state never results in anything new (determinism).
  - Does not assume: The outcome of a move (i.e. that south from (0,0) -> (0,1) even though it's deterministic.
  - Does not assume: The size or shape of the space to be explored.
  - Does not know: That it has explored the inverse of the direction it took to get to current (see TODO).

TODO: Given the agent has implicit knowledge about what action to take to backtrack (see _inverse_direction)
it should have implicit knowledge that inverse direction has been explored already.
'''
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


class DFEStrategy():
  def __init__(self, agent):
    self.agent = agent
    self.move_stack = []
    self.frontiers: dict[tuple[int, int], str] = {} # Unexplored directions for each visited location.

  def move(self, agent):
    if self._visited_current_location():
        (last_location, last_direction) = self._pop_move_stack()
        if not last_location:
          logger.debug('No backtrack but visited node.')
          return None
        if self.current_location != last_location:
          return _move(NHood.inverse_direction(last_direction))
        else:
          pass # Continue from current location.
    next_direction = self._get_next_direction()
    if next_direction:
      self._push_move_stack(self.current_location, next_direction)
      return _move(next_direction)
    else:
      (last_location, last_direction) = self._pop_move_stack()
      if not last_location:
        logger.debug('No backtrack and no more unexplored actions.')
        return None
      return _move(NHood.inverse_direction(last_direction))

  def avialable_move(self, agent):
    return self._current_frontier()

  def reset(self):
    self.move_stack = []
    self.frontiers = {} # Unexplored directions for each visited location.

  def _push_move_stack(self, location, dir):
    self.move_stack.append((location, dir))

  def _pop_move_stack(self):
    try:
      return self.move_stack.pop()
    except:
      return (None, None)

  def _get_next_direction(self):
    ''' Get the next best action from current state. '''
    try:
      return self._current_frontier().pop()
    except Exception as e:
      return None

  def _visited_current_location(self):
    return self.current_location in [l for (l,d) in self.move_stack]

  def _current_frontier(self):
    ''' Like get_next_direction, idempotently init actions for state but don't pop one. '''
    if self.current_location not in self.frontiers:
      self.frontiers[self.current_location] = NHood.directions.copy()
    return self.frontiers[self.current_location]

  @property
  def current_location(self):
    return self.agent.current_location


class DFEAgent(BaseAgent):
  def __init__(self):
    self.u = {
      'P': -1e3,
      'w': -1e3,
      'G': 1e3,
    }
    self.model: dict[tuple[int, int], list[str]] = {} # kb of observations of static things in the world.
    self.current_cell = None
    self.current_percept = None
    self.current_agent_state = None # location, score, and other agent meta provided by server.
    self.strategies = [PickStrategy(self), DFEStrategy(self)]

  def __str__(self):
    return f"current_location\t{self.current_location}\n"

  def percept(self, p):
    ''' A percept is { percept: string[], cell: string[], agent: Agent }. '''
    def set_it(v: dict, k, default = {}): # Fucking Python
      if k not in v:
        v[k] = default
    self.current_cell, self.current_percept, self.current_agent_state = itemgetter('cell', 'percept', 'agent')(p)
    # Update model
    known_things = ['W', 'P', 'S', 'B']
    sense_map = { 'S': 'W', 'B': 'P' }
    set_it(self.model, self.current_location, {})
    for thing in known_things:
      self.model[self.current_location][thing] = 1.0 if thing in self.current_cell else 0.0
    for sense in self.current_percept:
      for l in NHood.neighbour_of_list(self.current_location):
        set_it(self.model, l)
        if sense in sense_map and not sense_map[sense] in self.model[l]:
          self.model[l][sense_map[sense]] = 0.25

  def score_cell(self, location):
    if not location in self.model:
      return 0
    _cell = self.model[location]
    return sum([self.u[v] if v in self.u else 0 for v in _cell])

  @property
  def current_location(self):
    return tuple(self.current_agent_state['location'])

  def turn(self):
    for strategy in self.strategies:
      action = strategy.move(self)
      if action:
        return action

def _move(move):
  return { 'type': 'MOVE', 'payload': { 'direction': move } }


if __name__ == '__main__':
  agent = DFEAgent()
  runner = Runner(agent)
  runner.run()

