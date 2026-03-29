import type { ActivePiece, Cell, GameState, PieceType, ZoneState } from "./types";
import {
  BG_COLOR,
  CELL_SIZE,
  GRID_COLOR,
  GRID_LINE_COLOR,
  MINIMAP_HEIGHT,
  PIECE_COLORS,
  PIECE_SHAPES,
  ZONE_BORDER_COLOR,
  ZONE_HEIGHT,
  ZONE_WIDTH,
} from "./constants";

export class GameRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d")!;
  }

  /** Main render entry point, called every animation frame. */
  render(state: GameState): void {
    this.resizeCanvas();
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Clear
    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, w, h);

    if (state.zones.length === 0) return;

    // Find player zone index
    const playerIdx = state.zones.findIndex((z) => z.is_you);
    const centerIdx = playerIdx >= 0 ? playerIdx : 0;

    // Calculate viewport: center on player's zone
    const zonePixelWidth = ZONE_WIDTH * CELL_SIZE;
    const boardTop = MINIMAP_HEIGHT + 10;
    const boardAreaWidth = w;

    // The pixel X where the player's zone starts in "world" coords
    const playerWorldX = centerIdx * zonePixelWidth;
    // We want to center the player zone in the viewport
    const viewportCenterX = playerWorldX + zonePixelWidth / 2;
    const cameraX = viewportCenterX - boardAreaWidth / 2;

    // Draw minimap
    this.drawMinimap(state.zones, playerIdx, w);

    ctx.save();
    ctx.translate(-cameraX, boardTop);

    // Determine visible zone range
    const firstVisibleZone = Math.max(
      0,
      Math.floor(cameraX / zonePixelWidth) - 1
    );
    const lastVisibleZone = Math.min(
      state.zones.length - 1,
      Math.ceil((cameraX + boardAreaWidth) / zonePixelWidth) + 1
    );

    // Draw each visible zone
    for (let i = firstVisibleZone; i <= lastVisibleZone; i++) {
      const zone = state.zones[i];
      const xOffset = i * zonePixelWidth;
      const isYours = zone.is_you;

      this.drawZoneBackground(xOffset);
      this.drawGrid(xOffset);
      this.drawZoneCells(zone, xOffset, isYours);

      if (zone.active_piece) {
        // Draw ghost piece first (behind the real piece)
        this.drawGhostPiece(zone.active_piece, zone.grid, xOffset);
        this.drawPiece(
          zone.active_piece,
          xOffset,
          PIECE_COLORS[zone.active_piece.piece_type]
        );
      }

      // Draw zone border (right edge)
      if (i < state.zones.length - 1) {
        this.drawZoneBorder(xOffset + zonePixelWidth);
      }

      // Dim non-player zones
      if (!isYours && playerIdx >= 0) {
        ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
        ctx.fillRect(xOffset, 0, zonePixelWidth, ZONE_HEIGHT * CELL_SIZE);
      }
    }

    ctx.restore();

    // Draw HUD on top
    this.drawHUD(state, playerIdx, w, h, boardTop);
  }

  private resizeCanvas(): void {
    const dpr = window.devicePixelRatio || 1;
    const displayW = window.innerWidth;
    const displayH = window.innerHeight;

    if (
      this.canvas.width !== displayW * dpr ||
      this.canvas.height !== displayH * dpr
    ) {
      this.canvas.width = displayW * dpr;
      this.canvas.height = displayH * dpr;
      this.canvas.style.width = `${displayW}px`;
      this.canvas.style.height = `${displayH}px`;
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
  }

  /** Draw the background fill for a zone. */
  private drawZoneBackground(xOffset: number): void {
    this.ctx.fillStyle = GRID_COLOR;
    this.ctx.fillRect(xOffset, 0, ZONE_WIDTH * CELL_SIZE, ZONE_HEIGHT * CELL_SIZE);
  }

  /** Draw grid lines within a zone. */
  drawGrid(xOffset: number): void {
    const ctx = this.ctx;
    ctx.strokeStyle = GRID_LINE_COLOR;
    ctx.lineWidth = 0.5;

    // Vertical lines
    for (let col = 0; col <= ZONE_WIDTH; col++) {
      const x = xOffset + col * CELL_SIZE;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, ZONE_HEIGHT * CELL_SIZE);
      ctx.stroke();
    }

    // Horizontal lines
    for (let row = 0; row <= ZONE_HEIGHT; row++) {
      const y = row * CELL_SIZE;
      ctx.beginPath();
      ctx.moveTo(xOffset, y);
      ctx.lineTo(xOffset + ZONE_WIDTH * CELL_SIZE, y);
      ctx.stroke();
    }
  }

  /** Draw the locked cells in a zone's grid. */
  private drawZoneCells(zone: ZoneState, xOffset: number, _isYours: boolean): void {
    const grid = zone.grid;

    for (let row = 0; row < grid.length; row++) {
      for (let col = 0; col < grid[row].length; col++) {
        const cell: Cell = grid[row][col];
        if (cell) {
          this.drawBlock(xOffset + col * CELL_SIZE, row * CELL_SIZE, cell);
        }
      }
    }
  }

  /** Draw a single pixel-art block with shadow for depth. */
  private drawBlock(x: number, y: number, color: string): void {
    const ctx = this.ctx;
    const s = CELL_SIZE;
    const inset = 1;

    // Main block fill
    ctx.fillStyle = color;
    ctx.fillRect(x + inset, y + inset, s - inset * 2, s - inset * 2);

    // Highlight (top-left edges) — lighter
    ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
    ctx.fillRect(x + inset, y + inset, s - inset * 2, 2); // top
    ctx.fillRect(x + inset, y + inset, 2, s - inset * 2); // left

    // Shadow (bottom-right edges) — darker
    ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
    ctx.fillRect(x + inset, y + s - inset - 2, s - inset * 2, 2); // bottom
    ctx.fillRect(x + s - inset - 2, y + inset, 2, s - inset * 2); // right
  }

  /** Draw the active falling piece. */
  drawPiece(piece: ActivePiece, xOffset: number, color: string): void {
    const blocks = PIECE_SHAPES[piece.piece_type][piece.rotation % 4];
    for (const [dr, dc] of blocks) {
      const row = piece.y + dr;
      const col = piece.x + dc;
      if (row >= 0 && row < ZONE_HEIGHT && col >= 0 && col < ZONE_WIDTH) {
        this.drawBlock(xOffset + col * CELL_SIZE, row * CELL_SIZE, color);
      }
    }
  }

  /** Draw translucent ghost piece showing where hard drop would land. */
  drawGhostPiece(piece: ActivePiece, grid: Cell[][], xOffset: number): void {
    const blocks = PIECE_SHAPES[piece.piece_type][piece.rotation % 4];
    const color = PIECE_COLORS[piece.piece_type];

    // Find the lowest valid Y by simulating drop
    let ghostY = piece.y;
    while (true) {
      const nextY = ghostY + 1;
      let valid = true;
      for (const [dr, dc] of blocks) {
        const r = nextY + dr;
        const c = piece.x + dc;
        if (r >= ZONE_HEIGHT || r < 0 || c < 0 || c >= ZONE_WIDTH) {
          valid = false;
          break;
        }
        if (grid[r] && grid[r][c]) {
          valid = false;
          break;
        }
      }
      if (!valid) break;
      ghostY = nextY;
    }

    // Don't draw ghost if it's at the same position as the piece
    if (ghostY === piece.y) return;

    const ctx = this.ctx;
    for (const [dr, dc] of blocks) {
      const row = ghostY + dr;
      const col = piece.x + dc;
      if (row >= 0 && row < ZONE_HEIGHT && col >= 0 && col < ZONE_WIDTH) {
        const x = xOffset + col * CELL_SIZE;
        const y = row * CELL_SIZE;
        const inset = 1;
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.2;
        ctx.fillRect(x + inset, y + inset, CELL_SIZE - inset * 2, CELL_SIZE - inset * 2);
        ctx.globalAlpha = 0.5;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x + inset, y + inset, CELL_SIZE - inset * 2, CELL_SIZE - inset * 2);
        ctx.globalAlpha = 1.0;
      }
    }
  }

  /** Draw a colored separator line between zones. */
  drawZoneBorder(x: number): void {
    const ctx = this.ctx;
    ctx.strokeStyle = ZONE_BORDER_COLOR;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, ZONE_HEIGHT * CELL_SIZE);
    ctx.stroke();
  }

  /** Draw minimap at top of screen showing all zones as colored bars. */
  drawMinimap(zones: ZoneState[], playerIdx: number, canvasWidth: number): void {
    const ctx = this.ctx;
    const totalZones = zones.length;
    if (totalZones === 0) return;

    const barWidth = Math.max(4, Math.min(20, (canvasWidth - 20) / totalZones));
    const totalWidth = barWidth * totalZones;
    const startX = (canvasWidth - totalWidth) / 2;

    // Background bar
    ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
    ctx.fillRect(startX - 2, 2, totalWidth + 4, MINIMAP_HEIGHT + 4);

    for (let i = 0; i < totalZones; i++) {
      const zone = zones[i];
      const x = startX + i * barWidth;

      if (!zone.alive) {
        ctx.fillStyle = "#333";
        ctx.fillRect(x, 4, barWidth - 1, MINIMAP_HEIGHT);
        continue;
      }

      // Calculate stack height (highest non-empty row)
      const stackHeight = this.getStackHeight(zone.grid);
      const fillRatio = stackHeight / ZONE_HEIGHT;

      // Color based on danger: green -> yellow -> red
      let barColor: string;
      if (fillRatio < 0.4) {
        barColor = "#00cc44";
      } else if (fillRatio < 0.7) {
        barColor = "#cccc00";
      } else {
        barColor = "#cc2200";
      }

      // Draw bar background
      ctx.fillStyle = "#111";
      ctx.fillRect(x, 4, barWidth - 1, MINIMAP_HEIGHT);

      // Draw fill level from bottom
      const fillHeight = Math.round(MINIMAP_HEIGHT * fillRatio);
      ctx.fillStyle = barColor;
      ctx.fillRect(
        x,
        4 + MINIMAP_HEIGHT - fillHeight,
        barWidth - 1,
        fillHeight
      );

      // Highlight player's zone
      if (i === playerIdx) {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.strokeRect(x - 1, 3, barWidth + 1, MINIMAP_HEIGHT + 2);
      }
    }
  }

  /** Draw HUD elements: timer, lines, KOs, player count, piece preview. */
  drawHUD(
    state: GameState,
    playerIdx: number,
    canvasWidth: number,
    _canvasHeight: number,
    boardTop: number
  ): void {
    const ctx = this.ctx;
    const playerZone =
      playerIdx >= 0 ? state.zones[playerIdx] : null;

    ctx.font = "14px monospace";
    ctx.textBaseline = "top";

    const hudX = canvasWidth - 160;
    let hudY = boardTop + 10;

    // Players alive
    ctx.fillStyle = "#aaaaaa";
    ctx.fillText(`ALIVE: ${state.players_alive}`, hudX, hudY);
    hudY += 22;

    if (playerZone) {
      // Survival time
      const survSec = playerZone.survival_time;
      const mins = Math.floor(survSec / 60);
      const secs = Math.floor(survSec % 60);
      const timeStr = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
      ctx.fillStyle = "#ffffff";
      ctx.font = "20px monospace";
      ctx.fillText(timeStr, hudX, hudY);
      hudY += 28;

      ctx.font = "14px monospace";

      // Lines cleared
      ctx.fillStyle = "#aaaaaa";
      ctx.fillText(`LINES: ${playerZone.lines_cleared}`, hudX, hudY);
      hudY += 20;

      // KOs
      ctx.fillText(`KOs: ${playerZone.kos}`, hudX, hudY);
      hudY += 20;

      // Attacks sent
      ctx.fillText(`ATTACKS: ${playerZone.attacks_sent}`, hudX, hudY);
      hudY += 30;

      // Piece preview
      if (playerZone.piece_queue && playerZone.piece_queue.length > 0) {
        ctx.fillStyle = "#666666";
        ctx.fillText("NEXT", hudX, hudY);
        hudY += 20;

        for (const pieceType of playerZone.piece_queue) {
          this.drawPreviewPiece(pieceType, hudX + 10, hudY);
          hudY += 50;
        }
      }
    }
  }

  /** Draw a small preview piece in the HUD. */
  private drawPreviewPiece(
    pieceType: PieceType,
    x: number,
    y: number
  ): void {
    const ctx = this.ctx;
    const blocks = PIECE_SHAPES[pieceType][0]; // rotation 0
    const color = PIECE_COLORS[pieceType];
    const previewCellSize = 12;

    for (const [dr, dc] of blocks) {
      const bx = x + dc * previewCellSize;
      const by = y + dr * previewCellSize;

      ctx.fillStyle = color;
      ctx.fillRect(bx, by, previewCellSize - 1, previewCellSize - 1);

      // Mini highlight
      ctx.fillStyle = "rgba(255, 255, 255, 0.2)";
      ctx.fillRect(bx, by, previewCellSize - 1, 1);
      ctx.fillRect(bx, by, 1, previewCellSize - 1);
    }
  }

  /** Get the stack height of a zone grid (number of rows from bottom with blocks). */
  private getStackHeight(grid: Cell[][]): number {
    for (let row = 0; row < grid.length; row++) {
      for (let col = 0; col < grid[row].length; col++) {
        if (grid[row][col]) {
          return grid.length - row;
        }
      }
    }
    return 0;
  }
}
