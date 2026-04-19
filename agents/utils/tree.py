
from directions import DirectionMap, inverse_path

from .types import Location, Move


def path_of(loc: Location, tree: dict[Location, Move]) -> list[str]:
  path: list[str] = []
  while loc in tree:
    path.append(tree[loc].direction)
    loc = tree[loc].location
  return list(reversed(path))


def path_to(a: Location, b: Location, tree: dict[Location, Move], dmap: DirectionMap):
  path_a: list[str] = path_of(a, tree)
  path_b: list[str] = path_of(b, tree)
  splice = 0
  for i, l in enumerate(path_a):
    if i >= len(path_b):
      break
    if path_b[i] != l:
      break
    splice = i+1
  return inverse_path(dmap, path_a[splice:]) + path_b[splice:]
