Wumpus world demo agent. Agent semantics:

May assume:

  - Same set of movements is available in every state and we know them apriori.
  - Moves are reverisble and we know what the reverse move is.
  - The same move in the same state never results in anything new (determinism).
  - That some actions have inverse actions and what they are.

Should not assume:

  - The outcome of a move (i.e. that south from (0,0) -> (0,1) even though it's deterministic, unless it learns it.
  - The size or shape of the space to be explored.
