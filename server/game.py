"""Game loop and board management for ws-stress-blocks."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import OrderedDict
from typing import Any

from config import (
    ATTACK_CONTROL_TICKS,
    ATTACK_RANGE,
    DECAY_ACCELERATION,
    DECAY_BASE_INTERVAL,
    GRAVITY_INTERVAL,
    LOCK_DELAY_TICKS,
    PREVIEW_COUNT,
    TICK_RATE,
    ZONE_HEIGHT,
    ZONE_WIDTH,
)
from models import AttackPiece, Board, Piece, Zone
from tetris import (
    PIECE_COLORS,
    check_collision,
    check_top_out,
    clear_lines,
    generate_bag,
    get_cells,
    lock_piece,
    rotate_piece,
    spawn_piece,
)

logger = logging.getLogger(__name__)


class GameManager:
    def __init__(self) -> None:
        self.board = Board()
        self.attack_pieces: list[AttackPiece] = []
        self.connections: dict[str, Any] = {}  # zone_id -> WebSocket
        self.input_queues: dict[str, list[dict[str, Any]]] = {}
        self._running = False

    # ------------------------------------------------------------------
    # Player management
    # ------------------------------------------------------------------

    async def add_player(self, ws: Any) -> str:
        """Create a new zone for a connecting player and return its zone_id."""
        zone = Zone()
        zone.player_ws = ws

        # Position the new zone to the right of all existing zones
        if self.board.zones:
            last_zone = list(self.board.zones.values())[-1]
            zone.column_offset = last_zone.column_offset + ZONE_WIDTH
        else:
            zone.column_offset = 0

        # Fill the piece queue and spawn the first piece
        self._refill_queue(zone)
        self._spawn_next_piece(zone)

        self.board.zones[zone.zone_id] = zone
        self.connections[zone.zone_id] = ws
        self.input_queues[zone.zone_id] = []

        # Send welcome message with initial board state
        welcome = {
            "type": "welcome",
            "your_zone_id": zone.zone_id,
            "board_state": self.get_state_for_client(zone.zone_id),
        }
        try:
            await ws.send_json(welcome)
        except Exception:
            logger.exception("Failed to send welcome to %s", zone.zone_id)

        logger.info("Player joined: %s (total: %d)", zone.zone_id, len(self.connections))
        return zone.zone_id

    async def remove_player(self, zone_id: str) -> None:
        """Remove a player's zone and compress the board."""
        if zone_id in self.board.zones:
            self.board.zones[zone_id].alive = False
            del self.board.zones[zone_id]
        self.connections.pop(zone_id, None)
        self.input_queues.pop(zone_id, None)

        # Remove any attack pieces involving this zone
        self.attack_pieces = [
            ap for ap in self.attack_pieces
            if ap.source_zone_id != zone_id and ap.target_zone_id != zone_id
        ]

        self.compress_board()
        logger.info("Player left: %s (total: %d)", zone_id, len(self.connections))

    def queue_input(self, zone_id: str, message: dict[str, Any]) -> None:
        """Queue an input message for processing on the next tick."""
        if zone_id in self.input_queues:
            self.input_queues[zone_id].append(message)

    # ------------------------------------------------------------------
    # Piece queue helpers
    # ------------------------------------------------------------------

    def _refill_queue(self, zone: Zone) -> None:
        """Ensure the piece queue has enough pieces for previews + active."""
        while len(zone.piece_queue) < PREVIEW_COUNT + 1:
            zone.piece_queue.extend(generate_bag())

    def _spawn_next_piece(self, zone: Zone) -> None:
        """Pop the next piece from the queue and spawn it."""
        self._refill_queue(zone)
        piece_type = zone.piece_queue.pop(0)
        zone.active_piece = spawn_piece(piece_type)
        zone.lock_delay_counter = LOCK_DELAY_TICKS

        # If the new piece immediately collides, the player has topped out
        if check_collision(zone.grid, zone.active_piece):
            zone.alive = False
            zone.active_piece = None

    # ------------------------------------------------------------------
    # Input processing
    # ------------------------------------------------------------------

    def _process_inputs(self, zone: Zone, inputs: list[dict[str, Any]]) -> None:
        """Process all queued inputs for a zone."""
        if not zone.alive or zone.active_piece is None:
            return

        for msg in inputs:
            action = msg.get("type")
            if action == "move":
                self._handle_move(zone, msg.get("dir", ""))
            elif action == "rotate":
                dir_str = msg.get("dir", "cw")
                direction = 1 if dir_str == "cw" else -1
                self._handle_rotate(zone, direction)
            elif action == "hard_drop":
                self._handle_hard_drop(zone)
            elif action == "attack":
                self._handle_attack_relative(zone, msg.get("target_zone", 0))

    def _handle_move(self, zone: Zone, direction: str) -> None:
        """Move the active piece left, right, or down (soft drop)."""
        piece = zone.active_piece
        if piece is None:
            return

        if direction == "down":
            # Soft drop: move piece down one row
            below = Piece(piece.piece_type, piece.rotation, piece.x, piece.y + 1)
            if not check_collision(zone.grid, below):
                zone.active_piece = below
            return

        dx = -1 if direction == "left" else 1 if direction == "right" else 0
        if dx == 0:
            return

        candidate = Piece(piece.piece_type, piece.rotation, piece.x + dx, piece.y)
        if not check_collision(zone.grid, candidate):
            zone.active_piece = candidate
            zone.lock_delay_counter = LOCK_DELAY_TICKS

    def _handle_rotate(self, zone: Zone, direction: int) -> None:
        """Rotate the active piece."""
        piece = zone.active_piece
        if piece is None:
            return

        rotated = rotate_piece(zone.grid, piece, direction)
        if rotated is not None:
            zone.active_piece = rotated
            zone.lock_delay_counter = LOCK_DELAY_TICKS

    def _handle_hard_drop(self, zone: Zone) -> None:
        """Hard-drop the active piece to the lowest valid position and lock immediately."""
        piece = zone.active_piece
        if piece is None:
            return

        # Move piece down until collision
        while True:
            below = Piece(piece.piece_type, piece.rotation, piece.x, piece.y + 1)
            if check_collision(zone.grid, below):
                break
            piece = below

        zone.active_piece = piece
        self._lock_and_spawn(zone)

    def _handle_attack(self, zone: Zone, target_zone_id: str) -> None:
        """Send an attack to a nearby zone."""
        if target_zone_id not in self.board.zones:
            return

        target = self.board.zones[target_zone_id]
        if not target.alive:
            return

        # Check attack range: zones must be within ATTACK_RANGE of each other
        zone_index = list(self.board.zones.keys()).index(zone.zone_id)
        target_index = list(self.board.zones.keys()).index(target_zone_id)
        if abs(zone_index - target_index) > ATTACK_RANGE:
            return

        # Create a garbage line attack: add a row of blocks with one gap
        import random
        gap_col = random.randint(0, ZONE_WIDTH - 1)
        garbage_row = ["gray" if c != gap_col else None for c in range(ZONE_WIDTH)]

        # Push the garbage row onto the bottom of the target grid
        target.grid.pop(0)  # Remove top row
        target.grid.append(garbage_row)

        zone.attacks_sent += 1

    def _handle_attack_relative(self, zone: Zone, relative_offset: int) -> None:
        """Send an attack to a neighbor zone by relative offset (-1 = left, +1 = right)."""
        if relative_offset == 0:
            return
        zone_ids = list(self.board.zones.keys())
        zone_index = zone_ids.index(zone.zone_id)
        target_index = zone_index + relative_offset
        if target_index < 0 or target_index >= len(zone_ids):
            return
        target_zone_id = zone_ids[target_index]
        if abs(relative_offset) > ATTACK_RANGE:
            return
        self._handle_attack(zone, target_zone_id)

    # ------------------------------------------------------------------
    # Gravity / locking
    # ------------------------------------------------------------------

    def _apply_gravity(self, zone: Zone) -> None:
        """Move the active piece down by one row on a timer."""
        piece = zone.active_piece
        if piece is None:
            return

        # Only drop when gravity counter hits zero
        zone.gravity_counter -= 1
        if zone.gravity_counter > 0:
            # Still waiting — but check lock delay if resting
            below = Piece(piece.piece_type, piece.rotation, piece.x, piece.y + 1)
            if check_collision(zone.grid, below):
                zone.lock_delay_counter -= 1
                if zone.lock_delay_counter <= 0:
                    self._lock_and_spawn(zone)
            return

        zone.gravity_counter = GRAVITY_INTERVAL

        below = Piece(piece.piece_type, piece.rotation, piece.x, piece.y + 1)
        if not check_collision(zone.grid, below):
            zone.active_piece = below
            zone.lock_delay_counter = LOCK_DELAY_TICKS
        else:
            zone.lock_delay_counter -= 1
            if zone.lock_delay_counter <= 0:
                self._lock_and_spawn(zone)

    def _lock_and_spawn(self, zone: Zone) -> None:
        """Lock the active piece, clear lines, check top-out, spawn next."""
        piece = zone.active_piece
        if piece is None:
            return

        color = PIECE_COLORS.get(piece.piece_type, "white")
        lock_piece(zone.grid, piece, color)
        zone.active_piece = None

        lines = clear_lines(zone.grid)
        zone.lines_cleared += lines

        if check_top_out(zone.grid):
            zone.alive = False
            return

        self._spawn_next_piece(zone)

    # ------------------------------------------------------------------
    # Attack pieces
    # ------------------------------------------------------------------

    def _process_attack_pieces(self) -> None:
        """Tick down control timers on attack pieces and lock expired ones."""
        remaining: list[AttackPiece] = []
        for ap in self.attack_pieces:
            ap.control_ticks_remaining -= 1
            if ap.control_ticks_remaining <= 0:
                # Lock the attack piece into the target zone's grid
                target = self.board.zones.get(ap.target_zone_id)
                if target and target.alive:
                    color = PIECE_COLORS.get(ap.piece.piece_type, "gray")
                    lock_piece(target.grid, ap.piece, color)
                    lines = clear_lines(target.grid)
                    target.lines_cleared += lines
                    if check_top_out(target.grid):
                        target.alive = False
                        # Credit the KO to the source
                        source = self.board.zones.get(ap.source_zone_id)
                        if source:
                            source.kos += 1
            else:
                remaining.append(ap)
        self.attack_pieces = remaining

    # ------------------------------------------------------------------
    # Decay
    # ------------------------------------------------------------------

    def _apply_decay(self, zone: Zone) -> None:
        """Apply decay: periodically add a garbage row from the bottom."""
        zone.decay_timer += 1
        if zone.decay_timer >= zone.decay_interval:
            zone.decay_timer = 0
            zone.decay_interval *= DECAY_ACCELERATION

            # Add a garbage row at the bottom with a random gap
            import random
            gap_col = random.randint(0, ZONE_WIDTH - 1)
            garbage_row: list[str | None] = [
                "gray" if c != gap_col else None for c in range(ZONE_WIDTH)
            ]
            zone.grid.pop(0)  # Remove top row to make room
            zone.grid.append(garbage_row)

            # Check if decay caused a top-out
            if check_top_out(zone.grid):
                zone.alive = False

    # ------------------------------------------------------------------
    # Board compression
    # ------------------------------------------------------------------

    def compress_board(self) -> None:
        """Remove dead zones and reindex column offsets."""
        alive_zones = OrderedDict(
            (zid, z) for zid, z in self.board.zones.items() if z.alive
        )
        offset = 0
        for zone in alive_zones.values():
            zone.column_offset = offset
            offset += ZONE_WIDTH
        self.board.zones = alive_zones

    # ------------------------------------------------------------------
    # Eliminations
    # ------------------------------------------------------------------

    def _process_eliminations(self) -> None:
        """Remove dead zones, credit KOs, and compress the board."""
        dead_ids = [zid for zid, z in self.board.zones.items() if not z.alive]
        for zid in dead_ids:
            self.connections.pop(zid, None)
            self.input_queues.pop(zid, None)
            # Clean up attack pieces involving dead zones
            self.attack_pieces = [
                ap for ap in self.attack_pieces
                if ap.source_zone_id != zid and ap.target_zone_id != zid
            ]
        if dead_ids:
            self.compress_board()

    # ------------------------------------------------------------------
    # State broadcasting
    # ------------------------------------------------------------------

    def get_state_for_client(self, zone_id: str) -> dict[str, Any]:
        """Build the full game state from a specific player's perspective."""
        import time

        zones_data: list[dict[str, Any]] = []
        for zid, zone in self.board.zones.items():
            is_you = zid == zone_id
            survival_time = time.time() - zone.survival_start if zone.alive else 0

            zone_state: dict[str, Any] = {
                "zone_id": zid,
                "grid": zone.grid,
                "alive": zone.alive,
                "is_you": is_you,
                "survival_time": round(survival_time, 1),
                "lines_cleared": zone.lines_cleared,
                "kos": zone.kos,
                "attacks_sent": zone.attacks_sent,
            }

            # Active piece visible for all zones
            if zone.active_piece:
                zone_state["active_piece"] = {
                    "piece_type": zone.active_piece.piece_type,
                    "rotation": zone.active_piece.rotation,
                    "x": zone.active_piece.x,
                    "y": zone.active_piece.y,
                }
            else:
                zone_state["active_piece"] = None

            # Only send piece queue to the owning player
            if is_you:
                zone_state["piece_queue"] = zone.piece_queue[:PREVIEW_COUNT]

            zones_data.append(zone_state)

        players_alive = sum(1 for z in self.board.zones.values() if z.alive)

        return {
            "type": "state",
            "tick": self.board.tick,
            "zones": zones_data,
            "your_zone_id": zone_id,
            "players_alive": players_alive,
        }

    async def broadcast_state(self) -> None:
        """Send current game state to every connected client."""
        disconnected: list[str] = []
        for zone_id, ws in list(self.connections.items()):
            state = self.get_state_for_client(zone_id)
            try:
                await ws.send_json(state)
            except Exception:
                disconnected.append(zone_id)

        # Clean up any connections that errored
        for zid in disconnected:
            await self.remove_player(zid)

    # ------------------------------------------------------------------
    # Main tick
    # ------------------------------------------------------------------

    async def tick(self) -> None:
        """Execute one tick of the game loop."""
        self.board.tick += 1

        # 1. Process all queued inputs per zone
        for zone_id, zone in list(self.board.zones.items()):
            inputs = self.input_queues.get(zone_id, [])
            if inputs:
                self._process_inputs(zone, inputs)
                self.input_queues[zone_id] = []

        # 2. Apply gravity to all active pieces
        for zone in list(self.board.zones.values()):
            if zone.alive and zone.active_piece:
                self._apply_gravity(zone)

        # 3-4. Lock delay is handled inside _apply_gravity

        # 5. Process attack pieces
        self._process_attack_pieces()

        # 6. Apply decay to zones
        for zone in list(self.board.zones.values()):
            if zone.alive:
                self._apply_decay(zone)

        # 7. Process eliminations and compress board
        self._process_eliminations()

        # 8. Broadcast state delta
        await self.broadcast_state()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Run the main game loop."""
        self._running = True
        tick_interval = 1.0 / TICK_RATE
        logger.info("Game loop started (tick rate: %d)", TICK_RATE)

        while self._running:
            start = asyncio.get_event_loop().time()
            try:
                await self.tick()
            except Exception:
                logger.exception("Error in game tick %d", self.board.tick)

            elapsed = asyncio.get_event_loop().time() - start
            sleep_time = max(0.0, tick_interval - elapsed)
            await asyncio.sleep(sleep_time)

    def stop(self) -> None:
        """Signal the game loop to stop."""
        self._running = False
