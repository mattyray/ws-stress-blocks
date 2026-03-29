"""Dataclass models for ws-stress-blocks."""

from __future__ import annotations

import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

from config import DECAY_BASE_INTERVAL, ZONE_HEIGHT, ZONE_WIDTH


@dataclass
class Piece:
    piece_type: str
    rotation: int
    x: int
    y: int


@dataclass
class Zone:
    zone_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    column_offset: int = 0
    grid: list[list[Optional[str]]] = field(default_factory=list)
    alive: bool = True
    player_ws: Any = None  # WebSocket reference
    piece_queue: list[str] = field(default_factory=list)
    active_piece: Optional[Piece] = None
    lock_delay_counter: int = 0
    decay_timer: int = 0
    decay_interval: float = DECAY_BASE_INTERVAL
    survival_start: float = field(default_factory=time.time)
    lines_cleared: int = 0
    kos: int = 0
    attacks_sent: int = 0

    def __post_init__(self) -> None:
        if not self.grid:
            self.grid = [
                [None for _ in range(ZONE_WIDTH)]
                for _ in range(ZONE_HEIGHT)
            ]


@dataclass
class Board:
    zones: OrderedDict[str, Zone] = field(default_factory=OrderedDict)
    tick: int = 0


@dataclass
class AttackPiece:
    piece: Piece
    source_zone_id: str
    target_zone_id: str
    control_ticks_remaining: int
