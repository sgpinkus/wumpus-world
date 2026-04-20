#!/usr/bin/env python
'''
Depth First Exploring agent. Once entire map is explored it just stops.
'''
from abc import abstractmethod
import logging
from typing import Any

import utils.directions as d
from utils import BaseAgent, FullPerceptData, Location, Move, Runner

logging.basicConfig()
logger = logging.getLogger('wumpus')
logger.setLevel(logging.INFO)

NHood: d.DMap = d.Hood4


class MyAgent(BaseAgent):
  @property
  @abstractmethod
  def current_location(self) -> Location:
    pass


class PickStrategy():
  def __init__(self, _agent: BaseAgent):
    pass

  def move(self, agent: Any) -> dict[str, Any] | None:
    if 'G' in agent.current_cell:
      return {'type': 'PICK', 'payload': {'what': 'G'}}


class DFEStrategy():
  def __init__(self, agent: MyAgent):
    self.agent = agent
    self.move_stack: list[Move] = []
    self.frontiers: dict[Location, list[str]] = {}  # Unexplored directions for each visited location.

  def move(self, _agent: Any):
    last_move = self.move_stack[-1] if len(self.move_stack) else None
    if self._visited_current_location():  # If visited attempt to backtrack
      self._pop_move_stack()
      if not last_move:
        return None
      if self.current_location != last_move.location:
        return _move(NHood.inverse_direction(last_move.direction))
      else:
        pass  # Last move did nothing, continue.
    if self.current_location not in self.frontiers:
      self.frontiers[self.current_location] = [d for d in NHood.directions.copy() if last_move and d != NHood.inverse_direction(last_move.direction)]
    next_direction = self.frontiers[self.current_location].pop() if len(self.frontiers[self.current_location]) else None
    if next_direction:
      self._push_move_stack(self.current_location, next_direction)
      return _move(next_direction)
    else:  # backtrack
      last_move = self._pop_move_stack()
      if not last_move:
        return None
      return _move(NHood.inverse_direction(last_move.direction))

  def reset(self):
    self.move_stack = []
    self.frontiers = {}  # Unexplored directions for each visited location.

  def _push_move_stack(self, location: Location, dir: str):
    self.move_stack.append(Move(location, dir))

  def _pop_move_stack(self) -> Move | None:
    try:
      return self.move_stack.pop()
    except:
      return None

  def _visited_current_location(self):
    return self.current_location in [l for (l, _d) in self.move_stack]

  @property
  def current_location(self) -> Location:
    return self.agent.current_location


class DFEAgent(MyAgent):

  def __init__(self, percept: FullPerceptData):
    self.u = {
      'P': -1e3,
      'w': -1e3,
      'G': 1e3,
    }
    self.model: dict[Location, dict[str, float]] = {}  # kb of observations of static things in the world.
    self.current_agent_state = percept.agent.model_copy()
    self.current_cell = percept.cell.copy()
    self.current_percept = percept.percept.copy()
    self.strategies: list[Any] = [PickStrategy(self), DFEStrategy(self)]

  def __str__(self):
    return f"current_location\t{self.current_location}\n"

  def percept(self, p: FullPerceptData):
    ''' A percept is { percept: string[], cell: string[], agent: Agent }. '''
    def set_it(v: dict[Any, Any], k: Location, default: Any = {}):  # Fucking Python
      if k not in v:
        v[k] = default
    self.current_cell = p.cell.copy()
    self.current_percept = p.percept.copy()
    self.current_agent_state = p.agent.model_copy()
    # Update model
    set_it(self.model, self.current_location, {})
    for thing in self.known_things:
      self.model[self.current_location][thing] = 1.0 if thing in self.current_cell else 0.0
    for sense in self.current_percept:
      for l in NHood.neighbour_of_list(self.current_location):
        set_it(self.model, l)
        if sense in self.sense_map and self.sense_map[sense] not in self.model[l]:
          self.model[l][self.sense_map[sense]] = 0.25

  def score_cell(self, location: Location):
    if location not in self.model:
      return 0
    _cell = self.model[location]
    return sum([self.u[v] if v in self.u else 0 for v in _cell])

  @property
  def current_location(self) -> Location:
    return self.current_agent_state.location

  @property
  def known_things(self):
    return ['W', 'P', 'S', 'B']

  @property
  def sense_map(self):
    return {'S': 'W', 'B': 'P'}

  def turn(self):
    for strategy in self.strategies:
      action = strategy.move(self)
      if action:
        return action


def _move(move: str) -> dict[str, Any]:
  return {'type': 'MOVE', 'payload': {'direction': move}}


if __name__ == '__main__':
  runner = Runner(DFEAgent)
  runner.run()
