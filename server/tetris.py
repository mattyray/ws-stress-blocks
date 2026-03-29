"""Core Tetris logic for ws-stress-blocks."""

from __future__ import annotations

import random
from typing import Optional

from config import ZONE_HEIGHT, ZONE_WIDTH
from models import Piece

# Each piece type maps to a list of rotations (0-3).
# Each rotation is a list of (row, col) offsets from the piece origin.
PIECE_SHAPES: dict[str, list[list[tuple[int, int]]]] = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(1, 1), (1, 2), (2, 0), (2, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

PIECE_COLORS: dict[str, str] = {
    "I": "cyan",
    "O": "yellow",
    "T": "purple",
    "S": "green",
    "Z": "red",
    "J": "blue",
    "L": "orange",
}

ALL_PIECE_TYPES: list[str] = list(PIECE_SHAPES.keys())


def get_cells(piece: Piece) -> list[tuple[int, int]]:
    """Return absolute (row, col) positions for a piece."""
    shape = PIECE_SHAPES[piece.piece_type][piece.rotation % 4]
    return [(piece.y + dr, piece.x + dc) for dr, dc in shape]


def check_collision(
    grid: list[list[Optional[str]]],
    piece: Piece,
    zone_width: int = ZONE_WIDTH,
    zone_height: int = ZONE_HEIGHT,
) -> bool:
    """Return True if the piece collides with walls or locked blocks."""
    for row, col in get_cells(piece):
        if col < 0 or col >= zone_width:
            return True
        if row >= zone_height:
            return True
        # Allow pieces above the visible area (row < 0)
        if row < 0:
            continue
        if grid[row][col] is not None:
            return True
    return False


def lock_piece(
    grid: list[list[Optional[str]]],
    piece: Piece,
    color: str,
) -> None:
    """Lock a piece into the grid in-place."""
    for row, col in get_cells(piece):
        if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
            grid[row][col] = color


def clear_lines(grid: list[list[Optional[str]]]) -> int:
    """Clear completed lines, shift rows down, return number cleared."""
    width = len(grid[0]) if grid else 0
    cleared = 0
    row = len(grid) - 1
    while row >= 0:
        if all(cell is not None for cell in grid[row]):
            grid.pop(row)
            grid.insert(0, [None for _ in range(width)])
            cleared += 1
            # Don't decrement row; re-check same index after shift
        else:
            row -= 1
    return cleared


def rotate_piece(
    grid: list[list[Optional[str]]],
    piece: Piece,
    direction: int,
    zone_width: int = ZONE_WIDTH,
    zone_height: int = ZONE_HEIGHT,
) -> Optional[Piece]:
    """Attempt to rotate a piece with basic wall kicks.

    direction: +1 for clockwise, -1 for counter-clockwise.
    Returns a new Piece if successful, None if all kicks fail.
    """
    new_rotation = (piece.rotation + direction) % 4

    # Wall kick offsets to try: no shift, then left/right by 1 and 2
    kick_offsets = [0, 1, -1, 2, -2]

    for dx in kick_offsets:
        candidate = Piece(
            piece_type=piece.piece_type,
            rotation=new_rotation,
            x=piece.x + dx,
            y=piece.y,
        )
        if not check_collision(grid, candidate, zone_width, zone_height):
            return candidate

    return None


def generate_bag() -> list[str]:
    """Generate a shuffled bag of all 7 piece types (standard 7-bag randomizer)."""
    bag = list(ALL_PIECE_TYPES)
    random.shuffle(bag)
    return bag


def spawn_piece(piece_type: str, zone_width: int = ZONE_WIDTH) -> Piece:
    """Spawn a new piece at the top center of the zone."""
    # Calculate spawn x so the piece is roughly centered.
    # Most pieces are 3 wide; I-piece is 4 wide.
    if piece_type == "I":
        spawn_x = (zone_width - 4) // 2
    elif piece_type == "O":
        spawn_x = (zone_width - 2) // 2
    else:
        spawn_x = (zone_width - 3) // 2

    return Piece(
        piece_type=piece_type,
        rotation=0,
        x=spawn_x,
        y=0,
    )


def check_top_out(grid: list[list[Optional[str]]]) -> bool:
    """Return True if any cell in the top row is filled."""
    if not grid:
        return False
    return any(cell is not None for cell in grid[0])
