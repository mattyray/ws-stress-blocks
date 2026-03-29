"""FastAPI application entry point for ws-stress-blocks."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import TICK_RATE, ZONE_WIDTH
from game import GameManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

game_manager = GameManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start the game loop on startup and stop it on shutdown."""
    task = asyncio.create_task(game_manager.run())
    logger.info("Game loop background task created")
    yield
    game_manager.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Game loop stopped")


app = FastAPI(title="ws-stress-blocks", lifespan=lifespan)

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static client files if they exist
CLIENT_DIST = os.path.join(os.path.dirname(__file__), "..", "client", "dist")
if os.path.isdir(CLIENT_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(CLIENT_DIST, "assets")), name="assets")


# ------------------------------------------------------------------
# HTTP endpoints
# ------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the client or a simple status page."""
    index_path = os.path.join(CLIENT_DIST, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content=(
            "<html><body>"
            "<h1>ws-stress-blocks server running</h1>"
            f"<p>Tick rate: {TICK_RATE} tps</p>"
            "<p>Connect via WebSocket at <code>/ws</code></p>"
            "</body></html>"
        )
    )


@app.get("/stats")
async def stats() -> JSONResponse:
    """Return basic server statistics."""
    alive_count = sum(1 for z in game_manager.board.zones.values() if z.alive)
    total_width = alive_count * ZONE_WIDTH
    return JSONResponse(
        content={
            "players_alive": alive_count,
            "total_board_width": total_width,
            "tick": game_manager.board.tick,
        }
    )


# ------------------------------------------------------------------
# WebSocket endpoint
# ------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Handle a player WebSocket connection."""
    await ws.accept()
    zone_id: str | None = None

    try:
        zone_id = await game_manager.add_player(ws)

        while True:
            raw = await ws.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from %s: %s", zone_id, raw[:100])
                continue
            game_manager.queue_input(zone_id, message)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", zone_id)
    except Exception:
        logger.exception("WebSocket error for %s", zone_id)
    finally:
        if zone_id:
            await game_manager.remove_player(zone_id)
