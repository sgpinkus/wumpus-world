from typing import Any
from collections.abc import Callable
from math import comb


def set_it(v: dict[Any, Any], locs: list[Any], default: Callable[[], dict[Any, Any]] = lambda: {}):  # Fucking Python
  for loc in locs:
    if loc not in v:
      v[loc] = default()


def binomial_pmf(e: int, p: float, n: int) -> float:
  """
  Probability of exactly e successes in n iid trials with success probability p.
  Args:
      e: number of successes (0 <= e <= n)
      p: probability of success on each trial (0 <= p <= 1)
      n: number of trials (n >= 0)
  Returns:
      P(e; p, n) — the binomial probability mass
  """
  if not (0 <= e <= n):
    raise ValueError(f"e must be between 0 and n, got e={e}, n={n}")
  if not (0.0 <= p <= 1.0):
    raise ValueError(f"p must be a probability in [0, 1], got p={p}")
  return comb(n, e) * (p ** e) * ((1 - p) ** (n - e))
