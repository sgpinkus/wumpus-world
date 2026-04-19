from typing import Any, NamedTuple, TypedDict
from pydantic import BaseModel

Location = tuple[int, int]


class Move(NamedTuple):
  location: Location
  direction: str


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
  percept: list[str]  # senses relating to neighbouring cells.
  cell: list[str]  # things in the cell
  agent: AgentData
