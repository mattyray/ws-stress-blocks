import { useEffect, useRef } from "react";
import type { DeathMessage, GameState, ServerMessage } from "./types";
import { GameRenderer } from "./renderer";
import { connect, disconnect, send } from "./ws";
import { setupInput, teardownInput } from "./input";

interface GameProps {
  onDeath: (stats: DeathMessage) => void;
}

export function Game({ onDeath }: GameProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<GameRenderer | null>(null);
  const stateRef = useRef<GameState | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Initialize renderer
    rendererRef.current = new GameRenderer(canvas);

    // Handle incoming server messages
    const handleMessage = (msg: ServerMessage) => {
      switch (msg.type) {
        case "welcome":
          stateRef.current = msg.board_state;
          break;
        case "state":
          stateRef.current = {
            zones: msg.zones,
            tick: msg.tick,
            your_zone_id: msg.your_zone_id,
            players_alive: msg.players_alive,
          };
          break;
        case "death":
          onDeath(msg);
          break;
        case "collapse":
          // Collapse is informational; the next state update will reflect
          // the removed zone. Nothing to handle explicitly here.
          break;
      }
    };

    const handleClose = () => {
      // Connection lost; state will go stale. Reconnect handled by ws module.
    };

    // Connect to server and send join
    connect(handleMessage, handleClose);
    send({ type: "join" });

    // Set up keyboard input
    setupInput();

    // Start render loop
    const renderLoop = () => {
      if (stateRef.current && rendererRef.current) {
        rendererRef.current.render(stateRef.current);
      }
      rafRef.current = requestAnimationFrame(renderLoop);
    };
    rafRef.current = requestAnimationFrame(renderLoop);

    // Cleanup
    return () => {
      cancelAnimationFrame(rafRef.current);
      teardownInput();
      disconnect();
    };
  }, [onDeath]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        display: "block",
        width: "100vw",
        height: "100vh",
        cursor: "none",
      }}
    />
  );
}
