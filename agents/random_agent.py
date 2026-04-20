#!/usr/bin/env python
''' Sample random move agent. '''
import logging
import random
from typing import Any
from utils import Action, Runner, BaseAgent
from utils.directions import map4


logging.basicConfig()
logger = logging.getLogger('wumpus')
logger.setLevel(logging.DEBUG)


class RandomAgent(BaseAgent):
  def __init__(self, *args: list[Any]):
    pass

  def turn(self) -> Action:
    d = random.sample(list(map4.keys()), 1)[0]
    return {'type': 'MOVE', 'payload': {'direction': d}}

  def percept(self, p: Any):
    pass


if __name__ == '__main__':
  runner = Runner(RandomAgent)
  runner.run()
