# OVERVIEW
Simple HTTP wrapper over a single WumpusWorld instance.

  1. As soon as the server starts a game is made ready.
  2. 1 or more agents join.
  3. The game is started (ready -> running).
  4. The game stops after a certain number of moves or because a viewer requested it.
  5. The game can be restarted (goto step #3).
  5. Or else an new game is started (goto step #1).

Agents cannot join a started game. Once a game is finished agents are diconnected and forgotten.
Agents can join the next game but there's no tracking of agent state or anything from game to game (agents and viewer
may track that).