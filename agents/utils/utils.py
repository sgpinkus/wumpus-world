from typing import Any
from collections.abc import Callable


def set_it(v: dict[Any, Any], locs: list[Any], default: Callable[[], dict[Any, Any]] = lambda: {}):  # Fucking Python
  for loc in locs:
    if loc not in v:
      v[loc] = default()
