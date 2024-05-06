from operator import itemgetter
from abc import *
import logging
import httpx
import json
import random
import sys


logger = logging.getLogger('wumpus')


class BaseAgent(metaclass=ABCMeta):
  @abstractmethod
  def turn(self):
    pass
  @abstractmethod
  def percept(self, percept):
    pass
  def new_agent(self):
    pass


class Runner():
  base_url: str = None
  agent: BaseAgent = None

  def __init__(self, agent: BaseAgent, base_url: str = 'https://127.0.0.1:3001'):
    self.agent = agent
    self.base_url = base_url if base_url else self.base_url

  def run(self):
    try:
      client = httpx.Client(http2=True, verify=False, base_url=self.base_url)
      res = client.post(f'/agent/join/', data={'type': 'MOVE', 'payload': { 'direction': 'SW' } })
      assert_ok(res)
      _percept = res.json()
      cell, percept, agent = itemgetter('cell', 'percept', 'agent')(_percept)
      self.agent.percept(_percept)
      logger.info(f'Joined agent {agent["id"]}')
      logger.debug(f'Initial percept {_percept}')
      stream_client = httpx.Client(http2=True, verify=False, base_url=self.base_url)
      with stream_client.stream("GET", f'/agent/{agent["id"]}/events', timeout=1e3) as res:
        logger.debug('Waiting for agent details and game start')
        for m in _filter(res):
          logger.debug(f'New message: {m}')
          [type, payload] = parse_message(m)
          if type == 'new-game':
            logger.info('Game over')
            sys.exit()
          elif type == 'new-agent':
            self.agent.new_agent()
          elif type == 'turn-start':
            action = self.agent.turn()
            logger.debug(f'Agent chose action: {action}')
            if action:
              res = client.post(f'/agent/{agent["id"]}/action/', json=action)
              assert_ok(res)
              _percept = res.json()
              logger.debug(f'Agent receives percept: {_percept}')
              cell, percept, agent = itemgetter('cell', 'percept', 'agent')(_percept)
              self.agent.percept(_percept)
          logger.debug(f'Agent {agent}')
    except httpx.ConnectError as e: # Cant connect
      logger.error('ConnectError:', e)
    except httpx.RemoteProtocolError as e: # Server closed connection.
      logger.error('RemoteProtocolError:', e)
    except httpx.ReadTimeout as e: # No response was sent within timeout.
      logger.error('ReadTimeout', e)
    except KeyboardInterrupt as e:
      logger.info('KeyboardInterrupt. Exiting.')


def _filter(r):
  for m in r.iter_lines():
    if not m.strip('\n'):
      continue
    yield m


def assert_ok(res: httpx.Response):
  if 200 <= res.status_code < 300: return True
  raise Exception(res.text)


def parse_message(m: str):
  type = m[0:4]
  if type != 'data': raise Exception(f'Unknown message type {type}')
  data = m[6:].strip('\n')
  data = json.loads(data)
  return [data['type'], data['payload'] if 'payload' in data else None]