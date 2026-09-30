# abilities.py - Tactical Mino Abilities
# Implemented with clear, readable logic. No confusing shortcuts.

import random
from config import (
    BOARD_WIDTH, TOTAL_HEIGHT,
    ABILITY_NONE, ABILITY_BOMB, ABILITY_LIGHTNING,
    ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_BURNING, ABILITY_HEAVY
)

def assign_random_ability(chance=0.25):
    """
    Rolls to see if a newly spawned piece should have a special ability mino.
    By default, 25% chance of spawning one special block in the piece.
    """
    roll = random.random()
    if roll > chance:
        return ABILITY_NONE
    
    # Pick one of the 6 special abilities with equal probability
    abilities = [
        ABILITY_BOMB,
        ABILITY_LIGHTNING,
        ABILITY_MAGNET,
        ABILITY_FREEZE,
        ABILITY_BURNING,
        ABILITY_HEAVY
    ]
    return random.choice(abilities)


def execute_bomb(board, bomb_x, bomb_y, radius=1):
    """
    💣 Bomb block: Detonates upon locking.
    Clears all blocks within 'radius' (default 1 = 3x3 square).
    Returns the list of (x, y) coordinates that were blown up.
    """
    destroyed_cells = []
    
    # Check all cells from bomb_y - radius to bomb_y + radius
    for y in range(bomb_y - radius, bomb_y + radius + 1):
        for x in range(bomb_x - radius, bomb_x + radius + 1):
            # Make sure we are within the board boundaries
            if 0 <= x < BOARD_WIDTH and 0 <= y < TOTAL_HEIGHT:
                if board[y][x] is not None:
                    destroyed_cells.append((x, y, board[y][x]))
                    board[y][x] = None
                    
    return destroyed_cells


def execute_lightning(board, bolt_x, bolt_y):
    """
    ⚡ Lightning block: Fires an ionizing cross upon locking.
    Clears the entire horizontal row and the entire vertical column.
    Returns the list of (x, y) coordinates destroyed.
    """
    destroyed_cells = []
    
    # 1. Clear the entire horizontal row
    for x in range(BOARD_WIDTH):
        if board[bolt_y][x] is not None:
            destroyed_cells.append((x, bolt_y, board[bolt_y][x]))
            board[bolt_y][x] = None
            
    # 2. Clear the entire vertical column
    for y in range(TOTAL_HEIGHT):
        if board[y][bolt_x] is not None:
            # Avoid adding the intersection cell twice
            if (bolt_x, y, board[y][bolt_x]) not in destroyed_cells:
                destroyed_cells.append((bolt_x, y, board[y][bolt_x]))
            board[y][bolt_x] = None
            
    return destroyed_cells


def execute_magnet(board, center_x, center_y, radius=3):
    """
    🧲 Magnet block: Emits a magnetic pull in a radius.
    Pulls floating blocks downward into any empty air gaps directly underneath them.
    Returns the count of blocks moved to reward bonus score.
    """
    moved_count = 0
    
    # Determine the search box boundaries
    min_x = max(0, center_x - radius)
    max_x = min(BOARD_WIDTH - 1, center_x + radius)
    min_y = max(0, center_y - radius)
    max_y = min(TOTAL_HEIGHT - 1, center_y + radius)
    
    # Go column by column in the affected area
    for x in range(min_x, max_x + 1):
        # We scan from the bottom row up so blocks drop into lower gaps first
        for y in range(max_y, min_y, -1):
            if board[y][x] is None:
                # We found an empty gap at (x, y). Look above it for a block to pull down!
                for above_y in range(y - 1, min_y - 1, -1):
                    if board[above_y][x] is not None:
                        # Pull this block down into the empty gap
                        board[y][x] = board[above_y][x]
                        board[above_y][x] = None
                        moved_count += 1
                        break  # Move on to the next gap
                        
    return moved_count


def execute_freeze(game, duration=8.0, piece_count=3):
    """
    🧊 Freeze block: Flash freezes gravity descent.
    The player can freely rotate and move without gravity rushing them.
    Lasts for either 'duration' seconds or 'piece_count' locked pieces.
    """
    game.freeze_timer = duration
    game.freeze_pieces_remaining = piece_count


def update_burning_blocks(board, delta_time):
    """
    🔥 Burning block: Ticks down the 3-second fuse.
    When fuse reaches zero, it burns itself and adjacent 4 neighbor blocks.
    Returns list of cells destroyed by explosions this tick.
    """
    detonated_cells = []
    blocks_to_explode = []
    
    # First pass: find all burning blocks and decrement their timers
    for y in range(TOTAL_HEIGHT):
        for x in range(BOARD_WIDTH):
            cell = board[y][x]
            if cell is not None and cell.get('ability') == ABILITY_BURNING:
                timer = cell.get('burn_timer', 3.0) - delta_time
                cell['burn_timer'] = timer
                if timer <= 0.0:
                    blocks_to_explode.append((x, y))
                    
    # Second pass: explode finished burning blocks
    for bx, by in blocks_to_explode:
        # Neighbor offsets: center, up, down, left, right
        offsets = [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]
        for dx, dy in offsets:
            nx = bx + dx
            ny = by + dy
            if 0 <= nx < BOARD_WIDTH and 0 <= ny < TOTAL_HEIGHT:
                if board[ny][nx] is not None:
                    detonated_cells.append((nx, ny, board[ny][nx]))
                    board[ny][nx] = None
                    
    return detonated_cells
