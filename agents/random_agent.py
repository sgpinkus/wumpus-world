#!/usr/bin/env python
''' Sample random move agent. '''
import logging
from operator import itemgetter
import random
from utils import Runner, BaseAgent


logging.basicConfig()
logger = logging.getLogger('wumpus')
logger.setLevel(logging.DEBUG)

class RandomAgent(BaseAgent):
  def init(cell, percept, agent):
    pass

  def turn(self):
    d = random.sample(['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE'], 1)[0]
    return {'type': 'MOVE', 'payload': { 'direction': d } }

  def percept(self, p):
     pass


if __name__ == '__main__':
  agent = RandomAgent()
  runner = Runner(agent)
  runner.run()

