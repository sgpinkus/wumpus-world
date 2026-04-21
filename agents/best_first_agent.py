
#!/usr/bin/env python
'''
Local greedy best first search.
'''
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any, Literal, cast
from contextlib import suppress
import utils.directions as d
from collections import defaultdict
from utils import BaseAgent, FullPerceptData, Location, Move, Runner

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NHood: d.DMap = d.Hood4

Scores: dict[str, float] = {
  'P': -1e3,
  'W': -1e3,
  'G': 1e3,
  'V': -1e1,
}


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


class MoveStrategy():
  ''' Pure local next best.
  '''
  def __init__(self, agent: MyAgent):
    self.agent = agent
    self.last_move: Move | None = None
    self.frontier: dict[Location, list[str]] = {}  # Record dead ends

  def move(self, _agent: Any):
    logger.debug(f'Move {self.last_move}, {self.current_location}')
    if self.current_location not in self.frontier:
      self.frontier[self.current_location] = [d for d in NHood.directions.copy()]
    if self.last_move and self.last_move.location == self.current_location:
      with suppress(KeyError):
        self.frontier[self.current_location].remove(self.last_move.direction)
    next_direction = self._next_direction()
    # If next directio and it's not back tracking
    if next_direction:
      self.last_move = Move(self.current_location, next_direction)
      return _move(next_direction)

  def reset(self):
    self.move_stack = []
    self.frontier = {}  # Unexplored directions for each visited location.

  def _next_direction(self):
    def _score(m: Move):
      model: Model = cast(Model, self.agent.model)  # type: ignore
      return model.get(m.location, 'score', 'meta') or 0.
    next_directions = self.frontier[self.current_location]
    if not next_directions:
      return None
    next_moves = [Move(NHood.next(self.current_location, d), d) for d in next_directions]
    next_moves = sorted(next_moves, key=_score, reverse=True)
    logger.debug(f'next moves: {[(move, _score(move)) for move in next_moves]}')
    return next_moves[0].direction

  @property
  def current_location(self) -> Location:
    return self.agent.current_location


Source = Literal['Observed', 'ProximityRule', 'meta']


class Model():
  sources: list[Source]
  locations: defaultdict[Location, defaultdict[str, defaultdict[Source, float | None]]]  # premise, source

  def __init__(self, sources: list[Source]):
    self.locations = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))
    self.sources = sources

  def set(self, loc: Location, premise: str, source: Source, p: float | None):
    self.locations[loc][premise][source] = p

  def get_best(self, loc: Location, premise: str) -> float | None:
    premise_sources = self.locations[loc][premise]
    for source in self.sources:
      if source in premise_sources:
        return premise_sources[source]

  def get(self, loc: Location, premise: str, source: Source) -> float | None:
    return self.locations[loc][premise][source]

  def to_dict(self) -> dict[Location, dict[str, dict[Source, float]]]:
    out: dict[Location, dict[str, dict[Source, float]]] = {}
    for loc, premises in self.locations.items():
      loc_dict: dict[str, dict[Source, float]] = {}
      for premise, sources in premises.items():
        src_dict: dict[Source, float] = {
          source: value
          for source, value in sources.items()
          if value is not None
        }
        if src_dict:
          loc_dict[premise] = src_dict
      if loc_dict:
        out[loc] = loc_dict
    return out


class Rule(metaclass=ABCMeta):
  def wants(self, symbol: str) -> bool:
    return True

  @abstractmethod
  def update_model(self, loc: Location, model: Model) -> None:
    pass


@dataclass(frozen=True)
class ProximityRule(Rule):
  condition: str
  consequent: str

  def update_model(self, loc: Location, model: Model):
    if model.get(loc, self.condition, 'Observed'):
      nhood = NHood.neighbour_of_list(loc)
      consequent_observations = [n for n in nhood if model.get(n, self.consequent, 'Observed') is not None]
      known_consequents = [n for n in consequent_observations if model.get(n, self.consequent, 'Observed') == 1.0]
      known_no_consequents = [n for n in consequent_observations if model.get(n, self.consequent, 'Observed') == 0.0]
      known_unknowns = [n for n in nhood if n not in known_consequents and n not in known_no_consequents]
      # TODO: Actual probability ...
      if known_consequents:
        p = 1e-3  # ~ prior
      else:
        p = 1/(len(NHood) - len(known_no_consequents))
      for l in known_unknowns:
        model.set(l, self.consequent, 'ProximityRule', p)


class DFEAgent(MyAgent):

  def __init__(self, percept: FullPerceptData):
    self.knowledge_sources = [ProximityRule('B', 'P'), ProximityRule('S', 'W')]
    self.sources: list[Source] = ['Observed', 'ProximityRule']  # In order of precedence
    self.model = Model(self.sources)
    self.current_agent_state = percept.agent.model_copy()
    self.current_cell = percept.cell.copy()
    self.current_percept = percept.percept.copy()
    self.strategies: list[Any] = [PickStrategy(self), MoveStrategy(self)]
    self.percept(percept)

  def __str__(self):
    return (f"current_location\t{self.current_location}\n"
            f"current_cell\t{self.current_cell}\n"
            f"current_percept\t{self.current_percept}\n"
            f"current_agent_state\t{self.current_agent_state}\n"
    )

  def percept(self, p: FullPerceptData):
    ''' A percept is { percept: string[], cell: string[], agent: Agent }. '''
    self.current_cell = p.cell.copy()
    self.current_percept = p.percept.copy()
    self.current_agent_state = p.agent.model_copy()
    # Update model

  def score_cell(self, location: Location) -> float | None:
    score = 0
    if location not in self.model.locations:
      return 0
    for premise, u in Scores.items():
      for source in self.sources:
        v = self.model.get(location, premise, source)
        if v is not None:
          score += u*v
          break
    return score

  @property
  def current_location(self) -> Location:
    return self.current_agent_state.location

  @property
  def known_things(self):
    return ['W', 'P', 'S', 'B', 'G', 'H']

  def turn(self):
    # Add all direct observations
    visited_count = self.model.get(self.current_location, 'V', 'Observed') or 0.
    self.model.set(self.current_location, 'V', 'Observed', visited_count + 1)
    for observation in self.current_cell + self.current_percept:
      self.model.set(self.current_location, observation, 'Observed', 1.0)
    # Assert the absence of some things.
    for known_thing in self.known_things:
      if known_thing not in self.current_cell + self.current_percept:
        self.model.set(self.current_location, known_thing, 'Observed', 0.0)
    # Inference
    for rule in self.knowledge_sources:
      rule.update_model(self.current_location, self.model)
    # Rescore each possibly affected cell.
    for loc in NHood.neighbour_of_list(self.current_location) + [self.current_location]:
      self.model.set(loc, 'score', 'meta', self.score_cell(loc))
    for k, v in self.model.to_dict().items():
      logger.debug(f'{k}, {v}')
    for strategy in self.strategies:
      if action := strategy.move(self):
        return action


def _move(move: str) -> dict[str, Any]:
  return {'type': 'MOVE', 'payload': {'direction': move}}


if __name__ == '__main__':
  runner = Runner(DFEAgent)
  runner.run()
