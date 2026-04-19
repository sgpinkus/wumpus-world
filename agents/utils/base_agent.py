from abc import ABCMeta, abstractmethod
from .types import Action, FullPerceptData


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
