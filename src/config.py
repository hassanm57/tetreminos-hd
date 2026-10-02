# config.py - Game settings and constants for Tetreminos HD
# Keep everything simple and easy to read.

# Board dimensions
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
HIDDEN_ROWS = 4  # rows above visible ceiling where pieces spawn
TOTAL_HEIGHT = BOARD_HEIGHT + HIDDEN_ROWS

# Canvas block size in pixels
BLOCK_SIZE = 30

# Speeds and timings (in seconds)
LOCK_DELAY = 0.5            # Time piece can rest on ground before locking
MAX_LOCK_RESETS = 15        # Maximum moves/rotations allowed while on ground
INITIAL_FALL_SPEED = 1.0    # Seconds per fall step at level 1
SOFT_DROP_SPEED = 0.05      # Seconds per step when holding down arrow
DAS_DELAY = 0.10            # Snappy Delayed Auto Shift initial wait time (100ms)
ARR_RATE = 0.03             # Auto Repeat Rate between repeated shifts (30ms)
LINE_CLEAR_DELAY = 0.20     # Line clear explosion animation duration before ceiling rows collapse

# Color palette - Cyberpunk neon theme
COLORS = {
    'I': '#00f0f0',  # Cyan
    'J': '#0040ff',  # Deep Blue
    'L': '#ff8000',  # Neon Orange
    'O': '#ffe600',  # Cyber Yellow
    'S': '#00ff66',  # Toxic Green
    'T': '#b000ff',  # Synth Purple
    'Z': '#ff0055',  # Hot Pink
    'GARBAGE': '#4a5568', # Glitch / Garbage block gray
    'EMPTY': '#0c0f1d',   # Matrix cell background
}

# Mino ability types
ABILITY_NONE = 'NONE'
ABILITY_BOMB = 'BOMB'
ABILITY_LIGHTNING = 'LIGHTNING'
ABILITY_MAGNET = 'MAGNET'
ABILITY_FREEZE = 'FREEZE'
ABILITY_BURNING = 'BURNING'
ABILITY_HEAVY = 'HEAVY'

# Ability colors and visual badge symbols
ABILITY_INFO = {
    ABILITY_BOMB: {
        'symbol': '💣',
        'name': 'Bomb',
        'color': '#ff4500',
        'desc': 'Clears 3x3 radius on lock'
    },
    ABILITY_LIGHTNING: {
        'symbol': '⚡',
        'name': 'Lightning',
        'color': '#00ffff',
        'desc': 'Clears full row and column'
    },
    ABILITY_MAGNET: {
        'symbol': '🧲',
        'name': 'Magnet',
        'color': '#da70d6',
        'desc': 'Pulls nearby blocks into gaps'
    },
    ABILITY_FREEZE: {
        'symbol': '🧊',
        'name': 'Freeze',
        'color': '#87cefa',
        'desc': 'Halts gravity for 8 seconds'
    },
    ABILITY_BURNING: {
        'symbol': '🔥',
        'name': 'Burning',
        'color': '#ff2200',
        'desc': '3s fuse, melts adjacent blocks'
    },
    ABILITY_HEAVY: {
        'symbol': '🪨',
        'name': 'Heavy',
        'color': '#708090',
        'desc': 'Falls 3x faster, cannot rotate'
    },
}

# Standard scoring values based on official guidelines
SCORE_SINGLE = 100
SCORE_DOUBLE = 300
SCORE_TRIPLE = 500
SCORE_TETRIS = 800
SCORE_TSPIN_MINI = 100
SCORE_TSPIN_SINGLE = 800
SCORE_TSPIN_DOUBLE = 1200
SCORE_TSPIN_TRIPLE = 1600
SCORE_SOFT_DROP = 1   # Per cell
SCORE_HARD_DROP = 2   # Per cell

# Synthwave pentatonic musical frequencies (Hz) for procedural Web Audio
# A Minor Pentatonic: A, C, D, E, G across 3 octaves
SCALE_FREQUENCIES = [
    220.00,  # A3
    261.63,  # C4
    293.66,  # D4
    329.63,  # E4
    392.00,  # G4
    440.00,  # A4
    523.25,  # C5
    587.33,  # D5
    659.25,  # E5
    783.99,  # G5
    880.00,  # A5
]
