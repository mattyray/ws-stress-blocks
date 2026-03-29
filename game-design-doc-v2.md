# Shared-Board Multiplayer Tetris — Game Design Document

**Status:** Design Complete, Ready to Build  
**Date:** March 2026  
**Inspiration:** One Million Checkboxes (eieio) meets Battle Royale Tetris

---

## 1. Concept

A persistent, always-running multiplayer Tetris game played on a single shared board. Players join instantly via URL — no accounts, no lobbies, no matchmaking. Each player owns a vertical zone on the board and plays standard Tetris to survive. Players can attack neighbors by sending pieces into their zones. When your zone tops out, you're dead. Last player standing dominates the leaderboard.

**One-liner:** "It's Tetris, but the board is alive with other people trying to kill you."

### What Makes This Different

| Feature | Tetris 99 (Nintendo) | This Game |
|---|---|---|
| Board | 99 separate private boards | One shared board, all players visible |
| Attacks | Abstract garbage rows sent to targets | Physical — you steer your piece into their zone |
| Platform | Nintendo Switch, paid online subscription | Browser, free, open a URL and play |
| Joining | Matchmaking lobby, wait for 99 players | Instant, drop in/drop out anytime |
| Persistence | Discrete matches with start/end | Always running, no rounds |
| Identity | Nintendo account | Anonymous — no accounts, no names |

---

## 2. Core Gameplay

### 2.1 The Board

- One shared board, always running, 24/7
- Each player zone is **8 columns wide**, **20 rows tall**
- Board grows dynamically as players join (new zones appended to right edge)
- Board shrinks as players die (zones collapse, remaining players slide together)
- Total board width = 8 × (number of active players) columns

### 2.2 Zones

- Each player owns one zone (8 columns)
- Pieces spawn at the top center of YOUR zone
- Line clears are **zone-local** — fill all 8 cells in a row within your zone to clear it
- Your zone is your health — stack hits the ceiling, you're eliminated
- Zones are visually separated by subtle border lines with distinct colors

### 2.3 Standard Tetris Rules

- **7 standard tetrominoes:** I, O, T, S, Z, J, L
- **Movement:** Left, right, soft drop, hard drop, rotate (clockwise/counterclockwise)
- **Rotation:** Standard rotation with wall kick system (SRS or simplified variant)
- **Gravity:** Pieces fall one row per tick; tick speed is consistent (no acceleration per level)
- **No hold piece** — deal with what you're given
- **3-piece preview** — see the next 3 pieces in your queue
- **Lock delay:** Small grace period after a piece lands before it locks (allows last-second adjustments)

### 2.4 Attacking

- You can push your active piece **sideways out of your zone** into a neighboring zone
- **Attack range:** Any zone within **2–3 zones** of your own position
- When your piece enters an enemy zone, you get **brief control** to steer it — a few seconds to position it before it locks
- The piece is **consumed** from your sequence — you gave it up, your next piece spawns in your own zone
- **Natural cost of attacking:**
  - You lose the piece (can't use it on your own board)
  - You lose attention (your zone is decaying and vulnerable while you're steering a piece elsewhere)
  - No artificial penalties or cooldowns

### 2.5 Decay

- Bottom rows in every zone **slowly dissolve over time**
- Individual cells in the lowest rows fade and disappear on a timer
- Decay rate **accelerates** the longer you've been alive (creates late-game pressure)
- Purposes:
  - Prevents stalemates and AFK survival
  - Keeps the board dynamic even when nobody is attacking
  - Creates a natural skill ceiling — surviving long runs means managing decay AND attacks

### 2.6 Elimination & Board Compression

- When your stack hits the ceiling → **eliminated**
- Your zone plays a pixel explosion animation, then collapses
- Remaining zones **slide together** to fill the gap
- Players who were 3 zones apart might now be neighbors
- The board is constantly compressing as players die, creating escalating tension
- New threat landscapes emerge as unfamiliar (potentially veteran) players enter your attack range

---

## 3. Joining

### 3.1 Join Flow

1. Player opens the URL
2. New 8-column zone **spawns on the right edge** of the board
3. First piece drops immediately — under 2 seconds from page load to gameplay
4. Player starts with only one neighbor (to their left) — safe start

No accounts. No login. No names. Just open the URL and play.

---

## 4. Death & Replay

### 4.1 Death Screen

When eliminated, the player sees an overlay:

```
╔════════════════════════════════╗
║          GAME OVER             ║
║                                ║
║   SURVIVED: 12m 37s            ║
║   LINES CLEARED: 84            ║
║   KOs: 3                       ║
║   ATTACKS SENT: 17             ║
║                                ║
║   YOU OUTLASTED 31 PLAYERS     ║
║                                ║
║   [▶ PLAY AGAIN]  [SPECTATE]  ║
╚════════════════════════════════╝
```

### 4.2 Spectate Mode

- Optional after death
- Watch your killer's zone (their POV)
- Or freely pan across the entire board
- Exit spectate and hit "Play Again" at any time

### 4.3 Instant Replay

- "Play Again" spawns a new zone on the right edge immediately
- No loading, no matchmaking, no countdown
- Under 2 seconds from death to next first piece
- This fast loop is critical for retention — "one more run" energy

---

## 5. Scoring & Leaderboard

### 5.1 Primary Metric

**Survival time** — how long you stayed alive from spawn to elimination.

### 5.2 Secondary Stats (Tracked, No In-Game Advantage)

| Stat | Description |
|---|---|
| Survival Time | Primary score, displayed prominently |
| Lines Cleared | Raw Tetris skill metric |
| KOs | Players you eliminated (your piece/attack caused their top-out) |
| Attacks Sent | Total pieces lobbed into enemy zones |

### 5.3 Leaderboard

- **Session-based leaderboard** — tracks the current browser session's best runs
- Displayed on landing page before joining
- Also shows: players currently alive, longest active run right now, recent KO ticker

### 5.4 Design Philosophy

- **No in-game advantages from KOs** — no badges, no damage multipliers, no snowball mechanics
- Pure skill game — you survive because you're good at Tetris and smart about when to attack
- KOs and attacks are bragging rights only
- This keeps the game fair for new players dropping in alongside veterans

---

## 6. Visual Design

### 6.1 Aesthetic: Retro Pixel Art

- Classic arcade / early Game Boy Tetris feel
- Chunky pixel blocks with subtle shading for depth
- Dark background (deep navy or near-black)
- Subtle grid lines visible within zones

### 6.2 Color Palette

Standard Tetris piece colors:

| Piece | Color |
|---|---|
| I | Cyan |
| O | Yellow |
| T | Purple |
| S | Green |
| Z | Red |
| J | Blue |
| L | Orange |

### 6.3 Zone Visibility

- **Your zone:** Full brightness, sharp colors
- **Neighbor zones:** Slightly dimmed/desaturated in your viewport
- **Zone borders:** Subtle colored lines separating each player's zone
- **Viewport:** Shows your 8 columns + ~3–4 columns of each neighbor

### 6.4 Visual Effects

| Event | Effect |
|---|---|
| Attack (piece crossing zone border) | Pixel spark trail |
| Incoming attack (piece lands in your zone) | Brief screen shake on your viewport |
| Line clear | Flash + row dissolve animation |
| Elimination | Chunky pixel explosion on the dying zone |
| Board compression | Remaining zones slide together with a rumble |

### 6.5 Minimap

- Horizontal strip at top of screen showing the entire board
- Each zone rendered as a colored bar: green (healthy), yellow (struggling), red (near death)
- Gives players a sense of the full game's scale and state
- Your position highlighted

### 6.6 HUD (Minimal)

```
┌──────────────────────────────────┐
│ [MINIMAP BAR ████░░██░███░░████] │
│                                  │
│                        NEXT:     │
│                        ┌───┐     │
│    ┌────────────┐      │ T │     │
│    │            │      ├───┤     │
│    │  YOUR ZONE │      │ I │     │
│    │  (8 cols)  │      ├───┤     │
│    │            │      │ S │     │
│    │            │      └───┘     │
│    │            │                │
│    └────────────┘   12:37        │
│                     LINES: 84    │
│  47 ALIVE           KOs: 3      │
└──────────────────────────────────┘
```

---

## 7. Audio Design

### 7.1 Music

- **Chiptune / 8-bit** soundtrack
- Intensity subtly increases as the board compresses (fewer players alive = more intense music)
- Calm ambient chiptune when the board is wide and spacious
- Driving beat when you're surrounded by active neighbors

### 7.2 Sound Effects

| Event | Sound |
|---|---|
| Piece movement | Soft click |
| Piece rotation | Quick blip |
| Piece lock | Thud |
| Line clear (single) | Satisfying chime |
| Line clear (multiple) | Ascending fanfare |
| Incoming attack | Warning tone |
| Outgoing attack | Whoosh |
| KO (you eliminated someone) | Crunchy 8-bit KO sound |
| Your death | Descending tone + explosion |
| Board compression | Low rumble |

---

## 8. Technical Architecture

### 8.1 Stack

| Layer | Technology | Rationale |
|---|---|---|
| Server | **FastAPI + WebSockets** | Python, async, both devs know it |
| Game Loop | **asyncio task** | Single-threaded authoritative loop at 20 ticks/sec |
| Game State | **In-memory Python dict** | Nanosecond reads/writes for hot game state |
| Persistence | **Redis** | Leaderboard (sorted sets), live stats |
| Client Shell | **React + TypeScript** | Landing page, HUD, death screen, spectate UI |
| Client Game | **HTML5 Canvas** | Direct pixel rendering, 60fps, no React overhead |
| Client Bundler | **Vite** | Fast builds, HMR, TypeScript support |
| Deployment | **Railway** | Familiar, WebSocket support, easy scaling |

### 8.2 Why These Choices

- **Canvas over React for game rendering:** React's virtual DOM diffing is overhead for a 60fps game loop. Canvas gives direct pixel control — each Tetris cell is just a `fillRect` call. Perfect for pixel art.
- **In-memory over Redis for game state:** The board is hot mutable state updated 20 times/second. Local dict access is nanoseconds vs milliseconds for Redis. Redis is used for cold data (leaderboard) only.
- **Single-threaded game loop:** Python's GIL is actually a feature here — one authoritative thread processes all inputs in order, preventing race conditions on shared board state.
- **FastAPI over Django:** Lightweight, native async/WebSocket support, no ORM overhead needed for a game server.

### 8.3 Server Architecture

```
┌─────────────────────────────────────────────┐
│                  RAILWAY                     │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │         FastAPI Server                │   │
│  │                                       │   │
│  │  ┌─────────────┐  ┌───────────────┐  │   │
│  │  │  WebSocket   │  │  Game Loop    │  │   │
│  │  │  Handler     │  │  (asyncio)    │  │   │
│  │  │              │  │               │  │   │
│  │  │  - connect   │  │  20 ticks/sec │  │   │
│  │  │  - receive   │→ │  process all  │  │   │
│  │  │  - broadcast │← │  queued input │  │   │
│  │  │              │  │  apply gravity │  │   │
│  │  └──────────────┘  │  run decay    │  │   │
│  │                     │  collisions   │  │   │
│  │  ┌──────────────┐  │  line clears  │  │   │
│  │  │  Board State  │  │  broadcast   │  │   │
│  │  │  (in-memory)  │  │  state delta │  │   │
│  │  └──────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ┌──────────┐  ┌────────────────────────┐   │
│  │  Redis    │  │  Static Client Files   │   │
│  │  - scores │  │  - React + Canvas      │   │
│  │  - stats  │  │  - TypeScript          │   │
│  └──────────┘  └────────────────────────┘   │
│                                              │
└─────────────────────────────────────────────┘
```

### 8.4 WebSocket Message Protocol

#### Client → Server

```json
{ "type": "move", "dir": "left" | "right" | "down" }
{ "type": "rotate", "dir": "cw" | "ccw" }
{ "type": "hard_drop" }
{ "type": "attack", "target_zone": 3 }
{ "type": "join" }
```

#### Server → Client

```json
{ "type": "state", "zones": [...], "tick": 1234 }
{ "type": "death", "zone": 5, "killer_zone": 3 }
{ "type": "join", "zone_index": 12 }
{ "type": "collapse", "dead_zone": 5 }
{ "type": "welcome", "your_zone": 12, "board_state": {...} }
```

- Full board state sent on initial connect (`welcome` message)
- After that, only **deltas** are broadcast each tick (cells that changed)
- Keeps bandwidth minimal

### 8.5 Game Loop (Pseudocode)

```
every 50ms (20 ticks/second):
    1. Drain all input queues from connected players
    2. For each input:
       - Validate the move (collision check)
       - Apply if valid, reject if not
    3. For each active piece:
       - Apply gravity (move down one row)
       - If can't move down → lock the piece into the board
       - Spawn next piece for that player
    4. For each zone:
       - Check for full rows → clear them, shift above rows down
       - Apply decay to bottom rows
       - Check for top-out → eliminate player
    5. Process eliminations:
       - Remove dead zones
       - Compress board (slide remaining zones together)
       - Update neighbor relationships / attack ranges
    6. Compute state delta (what changed since last tick)
    7. Broadcast delta to all connected clients
```

### 8.6 Project Structure

```
/server
    main.py          # FastAPI app, WebSocket endpoint, server startup
    game.py          # Game loop, tick processing, board management
    models.py        # Dataclasses: Zone, Player, Piece, Board
    tetris.py        # Piece definitions, collision, rotation, line clear logic
    config.py        # Tick rate, decay rate, zone width, attack range constants

/client
    src/
        App.tsx        # React shell: landing page, HUD, death screen
        Game.tsx       # Canvas mount + game renderer bridge
        renderer.ts    # Pixel art drawing: board, pieces, effects, minimap
        ws.ts          # WebSocket client, message send/receive, reconnection
        input.ts       # Keyboard handler, input → WebSocket message mapping
        types.ts       # TypeScript types matching server message protocol
        constants.ts   # Colors, dimensions, timing values
    public/
        audio/         # Chiptune music + sound effects
        fonts/         # Pixel font

    index.html
    vite.config.ts
    package.json
    tsconfig.json
```

---

## 9. Scaling Plan

### Phase 1 — MVP (Build This First)

- Single FastAPI process on Railway
- One board, all players on the same instance
- In-memory game state, Redis for leaderboard
- Target: **100–200 concurrent players**
- This is enough to validate the game is fun and potentially go viral

### Phase 2 — If It Gets Popular

- Multiple game server processes, each owning a range of zones
- Lightweight WebSocket router directs connections to correct process
- Cross-zone attacks become inter-process messages (Redis pub/sub or direct TCP)
- Target: **500–1,000 concurrent players**

### Phase 3 — If It Blows Up

- Multiple independent arenas (game instances)
- New players routed to arena with available space
- Global leaderboard across all arenas via Redis
- Arena browser on landing page: "Arena 1: 87 alive | Arena 2: 134 alive | ..."
- Target: **10,000+ concurrent players**

### Scaling Philosophy

> Don't build Phase 2 until Phase 1 breaks. One Million Checkboxes started as one server and scaled reactively as it went viral. Ship the simplest thing that works, then fix what breaks.

---

## 10. MVP Feature Checklist

### Must Have (v1.0)

- [ ] WebSocket connection handling
- [ ] 8-column zone allocation for new players (right edge spawn)
- [ ] Standard Tetris gameplay: 7 pieces, movement, rotation, gravity, locking
- [ ] 3-piece preview display
- [ ] Zone-local line clears
- [ ] Collision detection (walls, floor, existing blocks)
- [ ] Rotation with basic wall kicks
- [ ] Decay system (bottom rows dissolve over time)
- [ ] Attacking: push piece into neighbor zone with brief control
- [ ] 2–3 zone attack range
- [ ] Elimination on top-out
- [ ] Board compression when a player dies
- [ ] Death screen with survival time and stats
- [ ] Instant replay (new zone on right edge)
- [ ] Pixel art rendering on HTML5 Canvas
- [ ] Minimap showing full board state
- [ ] HUD: timer, preview, stats, player count
- [ ] Basic leaderboard (session-based survival times)

### Nice to Have (v1.1+)

- [ ] Spectate mode after death
- [ ] Chiptune music + sound effects
- [ ] Landing page with live stats (players alive, longest run, KO ticker)
- [ ] Pixel explosion / screen shake effects
- [ ] Mobile touch controls
- [ ] Shareable death screen ("I survived 12:37 on [GAME NAME]")
- [ ] Reconnection handling (brief disconnect shouldn't kill you)

### Future Ideas (v2.0+)

- [ ] Multiple arenas for scaling
- [ ] Arena browser on landing page
- [ ] Daily/weekly leaderboard resets alongside all-time
- [ ] Custom pixel themes / zone colors
- [ ] Optional player nicknames
- [ ] "Rivals" — opt-in to be matched next to specific players

---

## 11. Open Questions

1. **Exact decay rate curve** — needs playtesting. Start slow, find the sweet spot where the board feels alive but not punishing.
2. **Attack control duration** — how many seconds do you get to steer a piece in an enemy zone? 2 seconds? 3? Needs playtesting.
3. **Attack range** — settled on 2–3 zones but exact number needs tuning. Maybe starts at 2 and increases as the board compresses?
4. **Game name** — TBD. Will figure it out during development.
5. **Tetris trademark** — can't use the word "Tetris" commercially, it's trademarked by The Tetris Company. The game mechanic itself isn't patented, but the branding is. Need an original name.
6. **Mobile support** — touch controls for Tetris work fine, but the attack mechanic (steering a piece in someone else's zone) might need a different UX on mobile.

---

*This document represents the complete game design as of March 2026. Ready to build.*
