"""Game constants for ws-stress-blocks."""

# Server tick rate (ticks per second)
TICK_RATE: int = 20

# Zone dimensions
ZONE_WIDTH: int = 8
ZONE_HEIGHT: int = 20

# Attack settings
ATTACK_RANGE: int = 2
ATTACK_CONTROL_TICKS: int = 50  # 2.5 sec at 20 tps

# Lock delay before piece locks after landing
LOCK_DELAY_TICKS: int = 10  # 0.5 sec at 20 tps

# Preview queue size
PREVIEW_COUNT: int = 3

# Decay settings
DECAY_BASE_INTERVAL: int = 300  # ticks, ~15 sec
DECAY_ACCELERATION: float = 0.98  # multiplier per decay event
