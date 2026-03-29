import { send } from "./ws";

const pressedKeys = new Set<string>();

function handleKeyDown(e: KeyboardEvent): void {
  // Ignore repeat events (key held down)
  if (e.repeat) return;

  // Prevent default for game keys
  const gameKeys = [
    "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
    " ", "KeyX", "KeyZ", "KeyA", "KeyD",
  ];
  if (gameKeys.includes(e.code)) {
    e.preventDefault();
  }

  // Track pressed state
  pressedKeys.add(e.code);

  switch (e.code) {
    case "ArrowLeft":
      send({ type: "move", dir: "left" });
      break;
    case "ArrowRight":
      send({ type: "move", dir: "right" });
      break;
    case "ArrowDown":
      send({ type: "move", dir: "down" });
      break;
    case "ArrowUp":
    case "KeyX":
      send({ type: "rotate", dir: "cw" });
      break;
    case "KeyZ":
      send({ type: "rotate", dir: "ccw" });
      break;
    case "Space":
      send({ type: "hard_drop" });
      break;
    case "KeyA":
      // Attack left neighbor (relative index -1)
      send({ type: "attack", target_zone: -1 });
      break;
    case "KeyD":
      // Attack right neighbor (relative index 1)
      send({ type: "attack", target_zone: 1 });
      break;
  }
}

function handleKeyUp(e: KeyboardEvent): void {
  pressedKeys.delete(e.code);
}

export function setupInput(): void {
  window.addEventListener("keydown", handleKeyDown);
  window.addEventListener("keyup", handleKeyUp);
}

export function teardownInput(): void {
  window.removeEventListener("keydown", handleKeyDown);
  window.removeEventListener("keyup", handleKeyUp);
  pressedKeys.clear();
}
