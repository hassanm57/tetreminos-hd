# engine.py - Core Guideline Tetris Game Engine with Mino Abilities
# Written simply and cleanly. Easy to read, debug, and understand.

import random
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, HIDDEN_ROWS, TOTAL_HEIGHT,
    INITIAL_FALL_SPEED, SOFT_DROP_SPEED, LOCK_DELAY, MAX_LOCK_RESETS,
    COLORS, ABILITY_NONE, ABILITY_BOMB, ABILITY_LIGHTNING,
    ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_BURNING, ABILITY_HEAVY,
    SCORE_SINGLE, SCORE_DOUBLE, SCORE_TRIPLE, SCORE_TETRIS,
    SCORE_TSPIN_MINI, SCORE_TSPIN_SINGLE, SCORE_TSPIN_DOUBLE, SCORE_TSPIN_TRIPLE,
    SCORE_SOFT_DROP, SCORE_HARD_DROP
)
from srs_tables import TETROMINO_SHAPES, get_kicks
from abilities import (
    assign_random_ability, execute_bomb, execute_lightning,
    execute_magnet, execute_freeze, update_burning_blocks
)

class Piece:
    """
    Represents an active falling tetromino piece.
    Contains its shape, rotation state, board coordinates, and any special ability.
    """
    def __init__(self, shape_type, ability=ABILITY_NONE):
        self.shape = shape_type
        self.rotation = 0  # 0: spawn, 1: 90 deg, 2: 180 deg, 3: 270 deg
        self.color = COLORS.get(shape_type, '#ffffff')
        self.ability = ability
        
        # If this piece has a special ability, pick which of its 4 blocks has it
        if self.ability != ABILITY_NONE:
            self.ability_block_index = random.randint(0, 3)
        else:
            self.ability_block_index = None

        # Spawn coordinates: center horizontally, just above the visible ceiling
        self.x = 3
        if shape_type == 'O':
            self.x = 4
        self.y = HIDDEN_ROWS - 2

    def get_block_positions(self, offset_x=0, offset_y=0, rotation_state=None):
        """
        Calculates the grid coordinates (x, y) of the piece's 4 blocks.
        Can preview positions with custom offsets or rotation states.
        """
        if rotation_state is None:
            rotation_state = self.rotation

        shape_offsets = TETROMINO_SHAPES[self.shape][rotation_state]
        positions = []
        for ox, oy in shape_offsets:
            positions.append((self.x + offset_x + ox, self.y + offset_y + oy))
        return positions


class TetrisGame:
    """
    Main Tetris Game engine. Manages board state, piece movement, SRS rotation,
    line clears, ability block execution, and game loop timing.
    """
    def __init__(self, enable_abilities=True):
        self.enable_abilities = enable_abilities
        self.board = self.create_empty_board()
        
        # Core game stats
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.combo = -1
        self.back_to_back = False
        self.game_over = False
        self.is_paused = False

        # Randomizer 7-bag and queue
        self.bag = []
        self.next_queue = []
        self.hold_piece = None
        self.can_hold = True

        # Active piece state
        self.current_piece = None
        self.fall_timer = 0.0
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.last_move_was_rotation = False
        self.t_spin_type = None

        # Tactical abilities state
        self.freeze_timer = 0.0
        self.freeze_pieces_remaining = 0
        self.last_cleared_rows = []

        # Event log for audio and visual effects (consumed by renderer/audio each tick)
        self.pending_events = []

        # Initialize game
        self.populate_next_queue()
        self.spawn_next_piece()

    def create_empty_board(self):
        """Creates a 2D grid of size TOTAL_HEIGHT x BOARD_WIDTH initialized to None."""
        board = []
        for row in range(TOTAL_HEIGHT):
            new_row = []
            for col in range(BOARD_WIDTH):
                new_row.append(None)
            board.append(new_row)
        return board

    def refill_bag(self):
        """Fills the 7-bag with each tetromino and shuffles them."""
        pieces = ['I', 'J', 'L', 'O', 'S', 'T', 'Z']
        random.shuffle(pieces)
        for p in pieces:
            ability = ABILITY_NONE
            if self.enable_abilities:
                ability = assign_random_ability(chance=0.25)
            self.bag.append(Piece(p, ability))

    def populate_next_queue(self):
        """Ensures the next queue has at least 5 pieces ready for preview."""
        while len(self.next_queue) < 5:
            if len(self.bag) == 0:
                self.refill_bag()
            self.next_queue.append(self.bag.pop(0))

    def spawn_next_piece(self):
        """Takes the next piece from the queue and places it on the board."""
        self.populate_next_queue()
        self.current_piece = self.next_queue.pop(0)
        self.can_hold = True
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.last_move_was_rotation = False
        self.t_spin_type = None

        # If freeze is active on a count basis, decrement count
        if self.freeze_pieces_remaining > 0:
            self.freeze_pieces_remaining -= 1

        # Alert if newly spawned piece is a Power Piece
        if self.current_piece and self.current_piece.ability != ABILITY_NONE:
            self.pending_events.append({'type': 'power_spawn', 'ability': self.current_piece.ability})

        # Check for immediate game over (spawn collision)
        if not self.is_valid_position(self.current_piece):
            self.game_over = True
            self.pending_events.append({'type': 'game_over'})

    def is_valid_position(self, piece, offset_x=0, offset_y=0, test_rotation=None):
        """
        Checks whether the piece can legally occupy the given position without
        hitting the board walls, floor, or existing locked blocks.
        """
        blocks = piece.get_block_positions(offset_x, offset_y, test_rotation)
        for x, y in blocks:
            # Wall checks
            if x < 0 or x >= BOARD_WIDTH:
                return False
            # Floor check
            if y >= TOTAL_HEIGHT:
                return False
            # Ceiling check (can exist in hidden rows y >= 0)
            if y < 0:
                return False
            # Collision with already locked blocks
            if self.board[y][x] is not None:
                return False
        return True

    def move_left(self):
        """Moves active piece 1 column to the left if unobstructed."""
        if self.game_over or self.is_paused or self.current_piece is None:
            return False

        if self.is_valid_position(self.current_piece, offset_x=-1):
            self.current_piece.x -= 1
            self.last_move_was_rotation = False
            self.reset_lock_delay_on_move()
            self.pending_events.append({'type': 'move', 'direction': 'left'})
            return True
        return False

    def move_right(self):
        """Moves active piece 1 column to the right if unobstructed."""
        if self.game_over or self.is_paused or self.current_piece is None:
            return False

        if self.is_valid_position(self.current_piece, offset_x=1):
            self.current_piece.x += 1
            self.last_move_was_rotation = False
            self.reset_lock_delay_on_move()
            self.pending_events.append({'type': 'move', 'direction': 'right'})
            return True
        return False

    def rotate(self, clockwise=True):
        """
        Performs Guideline SRS rotation with full 5-test wall kick evaluation.
        Heavy pieces cannot rotate!
        """
        if self.game_over or self.is_paused or self.current_piece is None:
            return False

        # Heavy block cannot be rotated
        if self.current_piece.ability == ABILITY_HEAVY:
            self.pending_events.append({'type': 'rotate_blocked_heavy'})
            return False

        current_rot = self.current_piece.rotation
        if clockwise:
            target_rot = (current_rot + 1) % 4
        else:
            target_rot = (current_rot - 1) % 4

        # Get list of 5 wall kick tests from SRS kick tables
        kicks = get_kicks(self.current_piece.shape, current_rot, target_rot)

        # Step through each kick offset candidate
        for kx, ky in kicks:
            if self.is_valid_position(self.current_piece, offset_x=kx, offset_y=ky, test_rotation=target_rot):
                self.current_piece.x += kx
                self.current_piece.y += ky
                self.current_piece.rotation = target_rot
                self.last_move_was_rotation = True
                self.reset_lock_delay_on_move()
                self.pending_events.append({'type': 'rotate', 'clockwise': clockwise})
                return True

        return False

    def reset_lock_delay_on_move(self):
        """
        Guideline rule: moving or rotating while resting on a surface resets
        the lock delay timer, up to a maximum of 15 resets.
        """
        if self.is_on_ground():
            if self.lock_resets < MAX_LOCK_RESETS:
                self.lock_timer = 0.0
                self.lock_resets += 1

    def is_on_ground(self):
        """Returns True if the piece is resting directly on the floor or another block."""
        if self.current_piece is None:
            return False
        return not self.is_valid_position(self.current_piece, offset_y=1)

    def soft_drop(self):
        """Drops the piece down by 1 cell. Awards 1 point."""
        if self.game_over or self.is_paused or self.current_piece is None:
            return False

        if self.is_valid_position(self.current_piece, offset_y=1):
            self.current_piece.y += 1
            self.score += SCORE_SOFT_DROP
            self.last_move_was_rotation = False
            return True
        return False

    def hard_drop(self):
        """
        Instantly drops piece to the lowest valid position, locks it,
        and awards 2 points per cell dropped.
        """
        if self.game_over or self.is_paused or self.current_piece is None:
            return

        drop_distance = 0
        while self.is_valid_position(self.current_piece, offset_y=1):
            self.current_piece.y += 1
            drop_distance += 1

        self.score += drop_distance * SCORE_HARD_DROP
        self.pending_events.append({'type': 'hard_drop', 'distance': drop_distance})
        self.lock_current_piece()

    def get_ghost_y(self):
        """Calculates the lowest y position the piece can reach (for ghost piece)."""
        if self.current_piece is None:
            return 0
        ghost_y = self.current_piece.y
        while self.is_valid_position(self.current_piece, offset_y=(ghost_y - self.current_piece.y + 1)):
            ghost_y += 1
        return ghost_y

    def hold(self):
        """
        Swaps current piece into the hold slot. Can only be done once per turn.
        """
        if self.game_over or self.is_paused or not self.can_hold or self.current_piece is None:
            return False

        shape_to_hold = self.current_piece.shape
        ability_to_hold = self.current_piece.ability

        if self.hold_piece is None:
            self.hold_piece = Piece(shape_to_hold, ability_to_hold)
            self.spawn_next_piece()
        else:
            temp = self.hold_piece
            self.hold_piece = Piece(shape_to_hold, ability_to_hold)
            self.current_piece = Piece(temp.shape, temp.ability)
            self.current_piece.x = 3
            if self.current_piece.shape == 'O':
                self.current_piece.x = 4
            self.current_piece.y = HIDDEN_ROWS - 2

        self.can_hold = False
        self.pending_events.append({'type': 'hold'})
        return True

    def lock_current_piece(self):
        """
        Locks the active piece onto the board, executes any special abilities,
        clears filled lines, calculates scoring, and spawns the next piece.
        """
        if self.current_piece is None:
            return

        blocks = self.current_piece.get_block_positions()
        ability = self.current_piece.ability
        ability_idx = self.current_piece.ability_block_index

        # Place the blocks on the board
        placed_ability_coord = None
        for i, (x, y) in enumerate(blocks):
            if 0 <= y < TOTAL_HEIGHT and 0 <= x < BOARD_WIDTH:
                cell_ability = ABILITY_NONE
                if i == ability_idx:
                    cell_ability = ability
                    placed_ability_coord = (x, y)

                self.board[y][x] = {
                    'color': self.current_piece.color,
                    'ability': cell_ability,
                    'burn_timer': 3.0 if cell_ability == ABILITY_BURNING else None
                }

        # Check for T-Spin before line clears modify the board
        self.check_t_spin()

        # Execute Tactical Mino Abilities if one was triggered
        if placed_ability_coord is not None and ability != ABILITY_NONE:
            ax, ay = placed_ability_coord
            if ability == ABILITY_BOMB:
                cleared = execute_bomb(self.board, ax, ay, radius=3)
                self.pending_events.append({'type': 'ability_bomb', 'x': ax, 'y': ay, 'cleared': cleared})
            elif ability == ABILITY_LIGHTNING:
                cleared = execute_lightning(self.board, ax, ay)
                self.pending_events.append({'type': 'ability_lightning', 'x': ax, 'y': ay, 'cleared': cleared})
            elif ability == ABILITY_MAGNET:
                moved = execute_magnet(self.board, ax, ay, radius=3)
                self.score += moved * 50
                self.pending_events.append({'type': 'ability_magnet', 'x': ax, 'y': ay, 'moved': moved})
            elif ability == ABILITY_FREEZE:
                execute_freeze(self, duration=8.0, piece_count=3)
                self.pending_events.append({'type': 'ability_freeze', 'duration': 8.0, 'x': ax, 'y': ay})
            elif ability == ABILITY_BURNING:
                self.pending_events.append({'type': 'ability_burning_placed', 'x': ax, 'y': ay})
            elif ability == ABILITY_HEAVY:
                self.pending_events.append({'type': 'ability_heavy_landed', 'x': ax, 'y': ay})

        # Check and clear completed lines
        lines_cleared_now = self.clear_completed_lines()

        # Update scoring, combos, and level progression
        self.update_score_and_level(lines_cleared_now)

        # Spawn next piece
        self.spawn_next_piece()

    def check_t_spin(self):
        """
        Official 3-corner rule: If a T piece just rotated, check the 4 diagonal
        corners surrounding its center. If at least 3 are occupied, it's a T-Spin!
        """
        self.t_spin_type = None
        if self.current_piece.shape != 'T' or not self.last_move_was_rotation:
            return

        # Center of T is block index 1 in SRS definition
        cx = self.current_piece.x + 1
        cy = self.current_piece.y + 1

        corners = [
            (cx - 1, cy - 1),  # Top-left
            (cx + 1, cy - 1),  # Top-right
            (cx - 1, cy + 1),  # Bottom-left
            (cx + 1, cy + 1),  # Bottom-right
        ]

        occupied_corners = 0
        for x, y in corners:
            if x < 0 or x >= BOARD_WIDTH or y >= TOTAL_HEIGHT or y < 0:
                occupied_corners += 1
            elif self.board[y][x] is not None:
                occupied_corners += 1

        if occupied_corners >= 3:
            self.t_spin_type = 'REGULAR'
            self.pending_events.append({'type': 't_spin', 'spin_type': 'REGULAR'})

    def clear_completed_lines(self):
        """
        Finds any full rows, removes them, and drops rows above down.
        Returns the number of lines cleared.
        """
        full_row_indices = []
        for y in range(TOTAL_HEIGHT):
            is_full = True
            for x in range(BOARD_WIDTH):
                if self.board[y][x] is None:
                    is_full = False
                    break
            if is_full:
                full_row_indices.append(y)

        # Store cleared row indices for visual line-break animations
        self.last_cleared_rows = list(full_row_indices)

        # Remove the full rows and insert fresh empty rows at the very top (index 0)
        for row_idx in full_row_indices:
            del self.board[row_idx]
            new_empty_row = [None for _ in range(BOARD_WIDTH)]
            self.board.insert(0, new_empty_row)

        return len(full_row_indices)

    def update_score_and_level(self, lines):
        """
        Updates game score based on lines cleared, T-spins, combos, and back-to-back.
        Increases game level every 10 lines.
        """
        if lines == 0:
            if self.t_spin_type is not None:
                self.score += SCORE_TSPIN_MINI * self.level
            self.combo = -1
            return

        # Increment total lines cleared
        self.lines_cleared += lines
        self.combo += 1

        # Calculate base points
        base_points = 0
        is_difficult_clear = False

        if self.t_spin_type is not None:
            is_difficult_clear = True
            if lines == 1:
                base_points = SCORE_TSPIN_SINGLE
            elif lines == 2:
                base_points = SCORE_TSPIN_DOUBLE
            elif lines == 3:
                base_points = SCORE_TSPIN_TRIPLE
        else:
            if lines == 1:
                base_points = SCORE_SINGLE
            elif lines == 2:
                base_points = SCORE_DOUBLE
            elif lines == 3:
                base_points = SCORE_TRIPLE
            elif lines == 4:
                base_points = SCORE_TETRIS
                is_difficult_clear = True

        # Apply Back-to-Back multiplier (1.5x) for consecutive difficult clears
        multiplier = 1.0
        if is_difficult_clear:
            if self.back_to_back:
                multiplier = 1.5
            self.back_to_back = True
        else:
            self.back_to_back = False

        points_awarded = int(base_points * multiplier * self.level)

        # Add combo bonus (50 * combo * level)
        if self.combo > 0:
            points_awarded += 50 * self.combo * self.level

        self.score += points_awarded

        # Level up every 10 lines
        new_level = (self.lines_cleared // 10) + 1
        if new_level > self.level:
            self.level = new_level
            self.pending_events.append({'type': 'level_up', 'level': self.level})

        self.pending_events.append({
            'type': 'line_clear',
            'lines': lines,
            'cleared_rows': list(getattr(self, 'last_cleared_rows', [])),
            'is_b2b': self.back_to_back and multiplier > 1.0,
            'combo': self.combo,
            't_spin': self.t_spin_type is not None
        })

    def get_current_fall_speed(self):
        """
        Calculates fall speed in seconds based on current level.
        If heavy piece, falls 3x faster.
        If freeze is active, fall speed is effectively paused.
        """
        if self.freeze_timer > 0.0 or self.freeze_pieces_remaining > 0:
            return 999999.0  # Infinite wait (frozen)

        # Standard Guideline speed curve
        speed = max(0.05, INITIAL_FALL_SPEED * (0.85 ** (self.level - 1)))
        
        # Heavy block drops 3x faster
        if self.current_piece and self.current_piece.ability == ABILITY_HEAVY:
            speed = speed / 3.0

        return speed

    def update(self, delta_time):
        """
        Step the game state forward by delta_time seconds.
        Handles gravity descent, lock delay countdown, and burning timers.
        """
        if self.game_over or self.is_paused:
            return

        # Update freeze timer
        if self.freeze_timer > 0.0:
            self.freeze_timer -= delta_time
            if self.freeze_timer <= 0.0:
                self.freeze_timer = 0.0
                self.pending_events.append({'type': 'freeze_ended'})

        # Update burning blocks
        detonations = update_burning_blocks(self.board, delta_time)
        for det in detonations:
            self.pending_events.append({
                'type': 'ability_burning_exploded',
                'x': det['x'],
                'y': det['y'],
                'cleared': det['cleared']
            })

        if self.current_piece is None:
            return

        # Check if resting on a surface
        if self.is_on_ground():
            self.lock_timer += delta_time
            if self.lock_timer >= LOCK_DELAY:
                self.lock_current_piece()
                return
        else:
            self.lock_timer = 0.0

            # Apply gravity
            fall_speed = self.get_current_fall_speed()
            self.fall_timer += delta_time
            if self.fall_timer >= fall_speed:
                self.fall_timer = 0.0
                if self.is_valid_position(self.current_piece, offset_y=1):
                    self.current_piece.y += 1
                    self.last_move_was_rotation = False
