# pyright: reportMissingImports=false
"""Enum for puzzle solve status. Stored per item in game state (room_solved).
Default for every puzzle is NOT_SOLVED until it is solved."""
from enum import Enum


class PuzzleStatus(str, Enum):
    """Status of a single puzzle in the room (per group/game)."""

    NOT_SOLVED = "not_solved"
    SOLVED = "solved"
