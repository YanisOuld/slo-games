"""Connect Four AI. Pure logic (no pygame): agents read the game and return a column.

MinimaxAgent is the non-learning baseline; learning agents (MCTS, self-play) go here next.
"""
from .agent import Connect4Agent
from .minimax import MinimaxAgent

__all__ = ["Connect4Agent", "MinimaxAgent"]
