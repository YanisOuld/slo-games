"""Snake AI agents. Pure logic (no pygame): they read game state, return a Direction."""
from .agent import SnakeAgent
from .hamiltonian import HamiltonianAgent

__all__ = ["SnakeAgent", "HamiltonianAgent"]
