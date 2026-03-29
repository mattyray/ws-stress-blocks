import { useCallback, useState } from "react";
import type { DeathMessage } from "./types";
import { Game } from "./Game";

type Screen = "landing" | "playing" | "dead";

export function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [deathStats, setDeathStats] = useState<DeathMessage | null>(null);

  const handleDeath = useCallback((stats: DeathMessage) => {
    setDeathStats(stats);
    setScreen("dead");
  }, []);

  const handlePlay = () => {
    setDeathStats(null);
    setScreen("playing");
  };

  const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  // Landing screen
  if (screen === "landing") {
    return (
      <div className="overlay">
        <div className="overlay-box">
          <h1 className="title">STRESS BLOCKS</h1>
          <p className="subtitle">Shared-board multiplayer Tetris</p>
          <div className="spacer" />
          <p className="hint">Drop in. Survive. Attack your neighbors.</p>
          <div className="spacer" />
          <button className="btn btn-primary" onClick={handlePlay}>
            PLAY
          </button>
          <p className="hint small">
            Arrow keys to move &middot; Up/X to rotate &middot; Space to drop
            &middot; A/D to attack
          </p>
        </div>
      </div>
    );
  }

  // Playing
  if (screen === "playing") {
    return <Game onDeath={handleDeath} />;
  }

  // Death screen
  return (
    <div className="overlay">
      <div className="overlay-box">
        <h1 className="title death-title">GAME OVER</h1>
        <div className="spacer" />
        {deathStats && (
          <div className="stats">
            <div className="stat-row">
              <span className="stat-label">SURVIVED</span>
              <span className="stat-value">
                {formatTime(deathStats.survival_time)}
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">LINES CLEARED</span>
              <span className="stat-value">{deathStats.lines_cleared}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">KOs</span>
              <span className="stat-value">{deathStats.kos}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">ATTACKS SENT</span>
              <span className="stat-value">{deathStats.attacks_sent}</span>
            </div>
          </div>
        )}
        <div className="spacer" />
        <div className="btn-group">
          <button className="btn btn-primary" onClick={handlePlay}>
            PLAY AGAIN
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => {
              // Spectate placeholder — for now, go back to landing
              setScreen("landing");
            }}
          >
            SPECTATE
          </button>
        </div>
      </div>
    </div>
  );
}
