"""Battleship AI. Pure logic (no pygame): agents read a TargetView and return a cell."""
from .agents import BattleshipAgent, HuntTargetAgent, ProbabilityAgent, RandomAgent, agent_for
from .probability import heat_map

__all__ = ["BattleshipAgent", "HuntTargetAgent", "ProbabilityAgent", "RandomAgent", "agent_for", "heat_map"]
