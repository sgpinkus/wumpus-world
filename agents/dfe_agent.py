#!/usr/bin/env python
'''
Depth First Exploring agent. Once entire map is explored it just loops. Agent visits many of the same locations
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
from collections import OrderedDict
import logging
from operator import itemgetter
import random
from utils import Runner, BaseAgent


logging.basicConfig()
logger = logging.getLogger('wumpus')
logger.setLevel(logging.DEBUG)

# In reveres order of preference.
# valid_directions = ['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE']
valid_directions = ['E', 'N', 'W', 'S']


class PickStrategy():
  def move(self, agent):
    if 'G' in agent.current_cell:
      return { 'type': 'PICK', 'payload': { 'what': 'G' } }


class DfeAgent(BaseAgent):
  def __init__(self):
    self.strategies = [PickStrategy()]
    self.reset()
    self.current_cell = None
    self.current_percept = None
    self.current_agent_state = None # location, score, and other agent meta provided by server.

  def __str__(self):
    return str(f"current_state\t{self.current_location}\n"
               f"visited\t{list(self.move_stack)}\n"
               f"frontier at current {self.current_location}\t{self._current_frontier()}\n"
    )

  def reset(self):
    self.move_stack = []
    self.frontiers = {} # Unexplored directions for each visited location.

  def percept(self, p):
    ''' Percept is { percept: string[], cell: string[], agent: Agent }. '''
    self.current_cell, self.current_percept, self.current_agent_state = itemgetter('cell', 'percept', 'agent')(p)

  @property
  def current_location(self):
    return tuple(self.current_agent_state['location'])

  def turn(self):
    for strategy in self.strategies:
      action = strategy.move(self)
      if action:
        return action
    if self._visited_current_location():
        (last_location, last_direction) = self._pop_move_stack()
        if not last_location:
          logger.debug('No backtrack but visited node.')
          return None
        if self.current_location != last_location:
          return _move(_inverse_direction(last_direction))
    else:
      next_direction = self._pop_next_direction()
      if next_direction:
        self._push_move_stack(self.current_location, next_direction)
        return _move(next_direction)
      else:
        (last_location, last_direction) = self._pop_move_stack()
        if not last_location:
          logger.debug('No backtrack and no more unexplored actions.')
          return None
        return _move(_inverse_direction(last_direction))

  def _push_move_stack(self, location, dir):
    self.move_stack.append((location, dir))

  def _pop_move_stack(self):
    try:
      return self.move_stack.pop()
    except:
      return (None, None)

  def _visited_current_location(self):
    return self.current_location in [l for (l,d) in self.move_stack]

  def _pop_next_direction(self):
    ''' Get the next action when in state '''
    try:
      return self._current_frontier().pop()
    except Exception as e:
      return None

  def _current_frontier(self):
    ''' Like get_next_direction, idempotently init actions for state but don't pop one. '''
    if self.current_location not in self.frontiers:
      self.frontiers[self.current_location] = valid_directions.copy()
    return self.frontiers[self.current_location]


def _inverse_direction(move):
  l = len(valid_directions)
  return valid_directions[(valid_directions.index(move)+l//2)%l]


def _move(move):
  return { 'type': 'MOVE', 'payload': { 'direction': move } }

if __name__ == '__main__':
  agent = DfeAgent()
  runner = Runner(agent)
  runner.run()

