// Piece types matching server tetrominoes
export type PieceType = "I" | "O" | "T" | "S" | "Z" | "J" | "L";

// A cell is either a color string or null (empty)
export type Cell = string | null;

// Active piece state from server
export interface ActivePiece {
  piece_type: PieceType;
  rotation: number;
  x: number;
  y: number;
}

// Per-zone state broadcast by the server
export interface ZoneState {
  zone_id: string;
  grid: Cell[][];
  active_piece: ActivePiece | null;
  alive: boolean;
  is_you: boolean;
  survival_time: number;
  lines_cleared: number;
  kos: number;
  attacks_sent: number;
  piece_queue?: PieceType[];
}

// Full game state from server
export interface GameState {
  zones: ZoneState[];
  tick: number;
  your_zone_id: string | null;
  players_alive: number;
}

// --- Server -> Client messages (discriminated union on "type") ---

export interface StateMessage {
  type: "state";
  zones: ZoneState[];
  tick: number;
  your_zone_id: string | null;
  players_alive: number;
}

export interface DeathMessage {
  type: "death";
  zone_id: string;
  killer_zone_id: string | null;
  survival_time: number;
  lines_cleared: number;
  kos: number;
  attacks_sent: number;
}

export interface WelcomeMessage {
  type: "welcome";
  your_zone_id: string;
  board_state: GameState;
}

export interface CollapseMessage {
  type: "collapse";
  dead_zone_id: string;
}

export type ServerMessage =
  | StateMessage
  | DeathMessage
  | WelcomeMessage
  | CollapseMessage;

// --- Client -> Server messages ---

export interface MoveMessage {
  type: "move";
  dir: "left" | "right" | "down";
}

export interface RotateMessage {
  type: "rotate";
  dir: "cw" | "ccw";
}

export interface HardDropMessage {
  type: "hard_drop";
}

export interface AttackMessage {
  type: "attack";
  target_zone: number;
}

export interface JoinMessage {
  type: "join";
}

export type ClientMessage =
  | MoveMessage
  | RotateMessage
  | HardDropMessage
  | AttackMessage
  | JoinMessage;
