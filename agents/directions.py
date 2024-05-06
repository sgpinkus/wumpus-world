from collections import OrderedDict
from os.path import commonprefix


# type DirectionMap = dict[str, tuple[int,int]]

class DMap():
  def __init__(self, dmap):
    self.dmap = dmap

  @property
  def map(self):
    return self.dmap.coppy()

  @property
  def directions(self):
    return list(self.dmap.keys())

  @property
  def inversed(self):
    return { v: k for k, v in self.dmap.items() }

  def inverse_direction(self, d):
    return inverse_direction(self.dmap, d)

  def neighbour_of_list(self, l):
    return neighbour_of_list(self.dmap, l)

  def neighbour_of_dict(self, l):
    return neighbour_of_dict(self.dmap, l)

  def distance(self, a, b):
    return distance(a, b)

  def next(self, l, d):
    return next(self.dmap, l, d)


def offset(map, l):
  return { k: (m[0] + l[0], m[1] + l[1]) for k, m in map.items() }


def inverse_direction(map, d):
  directions = list(map.keys())
  l = len(directions)
  return directions[(directions.index(d)+(l//2))%l]


def neighbour_of_list(map, l, n = 1e6):
    _map = offset(map, l)
    return list(
      filter(
        lambda z: (lambda x, y: x >= 0 and y >= 0 and x < n and y < n)(*z),
        _map.values()
      )
    )


def neighbour_of_dict(map, l, n = 1e6):
  return { k: v for k, v in offset(map, l).items() if (lambda x, y: x >= 0 and y >= 0 and x < n and y < n)(*v) }


def distance(a: tuple[int, int], b: tuple[int, int]) -> int:
  return abs(a[0] - b[0]) + abs(a[1] - b[1])


def next(map, l, d):
  return (l[0] + map[d][0], l[1] + map[d][1])

# Direction meaning map in *sequence*.
map4 = OrderedDict({
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
