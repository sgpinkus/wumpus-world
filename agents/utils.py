import json
import logging
import sys
from abc import ABCMeta, abstractmethod
from typing import Any, TypedDict

import httpx
from pydantic import BaseModel

logger = logging.getLogger('wumpus')


# {percept: string[], cell: string[], agent: Agent}

Location = tuple[int, int]


class Action(TypedDict):
  type: str
  payload: Any


class AgentData(BaseModel):
  id: int
  tag: str
  location: Location  # [number, number] becomes a tuple of ints
  arrows: int
  score: int
  moves: int


class FullPerceptData(BaseModel):
  percept: list[str]
  cell: list[str]
  agent: AgentData


class BaseAgent(metaclass=ABCMeta):
  @abstractmethod
  def __init__(self, percept: FullPerceptData):
    pass
  @abstractmethod
  def turn(self) -> Action | None:
    pass
  @abstractmethod
  def percept(self, p: FullPerceptData):
    pass
  def new_agent(self):
    pass


class Runner():
  base_url: str
  agent: BaseAgent
  agent_id: int

  def __init__(self, agent_type: type[BaseAgent], base_url: str = 'https://127.0.0.1:3001'):
    ''' Create agent after join so it always has a valid percept. '''
    self.base_url = base_url if base_url else self.base_url
    self.client = httpx.Client(http2=True, verify=False, base_url=self.base_url)
    res = self.client.post('/agent/join/', data={'type': 'MOVE', 'payload': {'direction': 'SW'}})
    assert_ok(res)
    full_percept = FullPerceptData(**res.json())
    self.agent = agent_type(full_percept)
    self.agent_id = full_percept.agent.id
    logger.info(f'Joined agent {full_percept.agent.id}')
    logger.debug(f'Initial percept {full_percept}')

  def run(self):
    try:
      stream_client = httpx.Client(http2=True, verify=False, base_url=self.base_url)
      with stream_client.stream("GET", f'/agent/{self.agent_id}/events', timeout=1e3) as res:
        logger.debug('Waiting for agent details and game start')
        for m in _filter(res):
          logger.debug(f'New message: {m}')
          [type, _payload] = parse_message(m)
          if type == 'new-game':
            logger.info('Game over')
            sys.exit()
          elif type == 'new-agent':
            self.agent.new_agent()
          elif type == 'turn-start':
            action = self.agent.turn()
            logger.debug(f'Agent chose action: {action}')
            if action:
              res = self.client.post(f'/agent/{self.agent_id}/action/', json=action)
              assert_ok(res)
              full_percept = FullPerceptData(**res.json())
              logger.debug(f'Agent receives percept: {full_percept}')
              self.agent.percept(full_percept)
          logger.debug(f'Agent {self.agent}')
    except httpx.ConnectError as e:  # Cant connect
      logger.error('ConnectError:', e)
    except httpx.RemoteProtocolError as e:  # Server closed connection.
      logger.error('RemoteProtocolError:', e)
    except httpx.ReadTimeout as e:  # No response was sent within timeout.
      logger.error('ReadTimeout', e)
    except KeyboardInterrupt:
      logger.info('KeyboardInterrupt. Exiting.')


def _filter(r: httpx.Response):
  for m in r.iter_lines():
    if not m.strip('\n'):
      continue
    yield m


def assert_ok(res: httpx.Response):
  if 200 <= res.status_code < 300:
    return True
  raise Exception(res.text)


def parse_message(m: str) -> tuple[str, Any]:
  type = m[0:4]
  if type != 'data':
    raise Exception(f'Unknown message type {type}')
  data = m[6:].strip('\n')
  data = json.loads(data)
  return (data['type'], data['payload'] if 'payload' in data else None)
