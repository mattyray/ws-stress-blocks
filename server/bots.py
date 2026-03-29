"""Bot players that connect via WebSocket and play automatically."""

import asyncio
import json
import random
import sys

import websockets


async def run_bot(url: str, bot_id: int) -> None:
    """Run a single bot that plays basic Tetris."""
    while True:
        try:
            async with websockets.connect(url) as ws:
                print(f"Bot {bot_id} connected")

                # Read messages in background
                zone_id = None

                async def read_messages():
                    nonlocal zone_id
                    async for raw in ws:
                        msg = json.loads(raw)
                        if msg.get("type") == "welcome":
                            zone_id = msg.get("your_zone_id")
                        elif msg.get("type") == "death":
                            # Reconnect after death
                            return

                reader = asyncio.create_task(read_messages())

                # Wait for welcome
                await asyncio.sleep(0.5)

                # Play loop: make random moves
                while not reader.done():
                    action = random.choices(
                        ["move_left", "move_right", "rotate", "drop", "wait", "attack"],
                        weights=[20, 20, 15, 10, 30, 5],
                    )[0]

                    if action == "move_left":
                        await ws.send(json.dumps({"type": "move", "dir": "left"}))
                    elif action == "move_right":
                        await ws.send(json.dumps({"type": "move", "dir": "right"}))
                    elif action == "rotate":
                        d = random.choice(["cw", "ccw"])
                        await ws.send(json.dumps({"type": "rotate", "dir": d}))
                    elif action == "drop":
                        await ws.send(json.dumps({"type": "hard_drop"}))
                    elif action == "attack":
                        d = random.choice([-1, 1])
                        await ws.send(json.dumps({"type": "attack", "target_zone": d}))

                    # Random delay between actions (simulates thinking)
                    await asyncio.sleep(random.uniform(0.1, 0.6))

                print(f"Bot {bot_id} died, respawning...")
                await asyncio.sleep(1)

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            print(f"Bot {bot_id} disconnected ({e}), reconnecting...")
            await asyncio.sleep(2)


async def main():
    num_bots = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    url = sys.argv[2] if len(sys.argv) > 2 else "ws://localhost:34197/ws"

    print(f"Spawning {num_bots} bots connecting to {url}")

    tasks = [asyncio.create_task(run_bot(url, i + 1)) for i in range(num_bots)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
