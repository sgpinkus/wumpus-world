from collections import OrderedDict
from os.path import commonprefix

from utils import Location


DirectionMap = OrderedDict[str, tuple[int, int]]


class DMap():
  def __init__(self, dmap: OrderedDict[str, tuple[int, int]]):
    self.dmap = dmap

  @property
  def map(self):
    return self.dmap.copy()

  @property
  def directions(self):
    return list(self.dmap.keys())

  @property
  def inversed(self):
    return {v: k for k, v in self.dmap.items()}

  def inverse_direction(self, d: str) -> str:
    return inverse_direction(self.dmap, d)

  def neighbour_of_list(self, l: Location) -> list[Location]:
    return neighbour_of_list(self.dmap, l)

  def neighbour_of_dict(self, l: Location) -> DirectionMap:
    return neighbour_of_dict(self.dmap, l)

  def distance(self, a: Location, b: Location) -> int:
    return distance(a, b)

  def next(self, l: Location, d: str) -> Location:
    return next(self.dmap, l, d)


def offset(dmap: DirectionMap, l: tuple[int, int]) -> DirectionMap:
  return OrderedDict({k: (m[0] + l[0], m[1] + l[1]) for k, m in dmap.items()})


def inverse_direction(dmap: DirectionMap, d: str) -> str:
  directions = list(dmap.keys())
  l = len(directions)
  return directions[(directions.index(d)+(l//2))%l]


def neighbour_of_list(dmap: DirectionMap, l: tuple[int, int], n: int = int(1e6)) -> list[tuple[int, int]]:
  _map = offset(dmap, l)
  return list(
    filter(
      lambda z: (lambda x, y: x >= 0 and y >= 0 and x < n and y < n)(z[0], z[1]),  # type: ignore
      _map.values()
    )
  )


def neighbour_of_dict(dmap: DirectionMap, l: Location, n: int = int(1e6)) -> DirectionMap:
  return OrderedDict({k: v for k, v in offset(dmap, l).items() if (lambda x, y: x >= 0 and y >= 0 and x < n and y < n)(*v)})   # type: ignore


def distance(a: Location, b: Location) -> int:
  return abs(a[0] - b[0]) + abs(a[1] - b[1])


def next(dmap: DirectionMap, l: Location, d: str):
  return (l[0] + dmap[d][0], l[1] + dmap[d][1])


# Direction meaning map in *sequence*.
map4: OrderedDict[str, tuple[int, int]] = OrderedDict({
  'E': (1, 0),
  'N': (0, -1),
  'W': (-1, 0),
  'S': (0, 1),
})

Hood4 = DMap(map4)


def known_path(a: str, b: str, hood: DMap):
  c = len(commonprefix([a, b]))
  bubble = [hood.inverse_direction(d) for d in list(reversed(a[c:]))]
  flow = b[c:]
  return list(reversed([*bubble, *flow]))
