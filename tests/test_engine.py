# test_engine.py - Unit tests for Tetris core mechanics, SRS, and abilities
import unittest
import sys
import os

# Add src/ to path so we can import modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine import TetrisGame, Piece
from config import (
    BOARD_WIDTH, TOTAL_HEIGHT,
    ABILITY_NONE, ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE
)
from srs_tables import TETROMINO_SHAPES, get_kicks
from abilities import execute_bomb, execute_lightning, execute_magnet

class TestTetrisEngine(unittest.TestCase):

    def setUp(self):
        self.game = TetrisGame(enable_abilities=False)

    def test_board_initialization(self):
        """Board should be 10x24 (with hidden rows) and initially empty."""
        self.assertEqual(len(self.game.board), TOTAL_HEIGHT)
        self.assertEqual(len(self.game.board[0]), BOARD_WIDTH)
        for row in self.game.board:
            for cell in row:
                self.assertIsNone(cell)

    def test_spawn_piece(self):
        """A piece should be spawned at the top and next queue populated."""
        self.assertIsNotNone(self.game.current_piece)
        self.assertIn(self.game.current_piece.shape, ['I', 'J', 'L', 'O', 'S', 'T', 'Z'])
        self.assertGreaterEqual(len(self.game.next_queue), 4)

    def test_movement(self):
        """Moving left and right changes x coordinate."""
        start_x = self.game.current_piece.x
        moved = self.game.move_left()
        if moved:
            self.assertEqual(self.game.current_piece.x, start_x - 1)
            self.game.move_right()
            self.assertEqual(self.game.current_piece.x, start_x)

    def test_srs_rotation(self):
        """Rotating changes rotation state between 0, 1, 2, 3."""
        piece = self.game.current_piece
        initial_rot = piece.rotation
        rotated = self.game.rotate(clockwise=True)
        if rotated:
            self.assertEqual(piece.rotation, (initial_rot + 1) % 4)

    def test_hard_drop(self):
        """Hard drop should drop the piece to the bottom and spawn next piece."""
        first_piece_shape = self.game.current_piece.shape
        self.game.hard_drop()
        # After hard drop, board should have at least 4 blocks locked at the bottom
        locked_blocks = 0
        for y in range(TOTAL_HEIGHT):
            for x in range(BOARD_WIDTH):
                if self.game.board[y][x] is not None:
                    locked_blocks += 1
        self.assertEqual(locked_blocks, 4)

    def test_line_clear_and_scoring(self):
        """A fully filled row should be cleared and award score."""
        # Fill the bottom row completely except row 23
        bottom_row = TOTAL_HEIGHT - 1
        for x in range(BOARD_WIDTH):
            self.game.board[bottom_row][x] = {'color': '#00f0f0', 'ability': ABILITY_NONE}

        cleared = self.game.clear_completed_lines()
        self.assertEqual(cleared, 1)
        # Now bottom row should be empty because it moved down
        for x in range(BOARD_WIDTH):
            self.assertIsNone(self.game.board[bottom_row][x])

    def test_bomb_ability(self):
        """Bomb should clear a 3x3 radius around detonation point."""
        # Fill a 3x3 block on the board
        center_x, center_y = 5, 20
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                self.game.board[center_y + dy][center_x + dx] = {'color': '#ff4500', 'ability': ABILITY_NONE}

        cleared = execute_bomb(self.game.board, center_x, center_y, radius=1)
        self.assertEqual(len(cleared), 9)
        # All 9 cells should now be None
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                self.assertIsNone(self.game.board[center_y + dy][center_x + dx])

    def test_lightning_ability(self):
        """Lightning should clear the entire row and column."""
        lx, ly = 4, 15
        # Fill some cells in row 15 and column 4
        self.game.board[15][0] = {'color': '#00ffff', 'ability': ABILITY_NONE}
        self.game.board[15][9] = {'color': '#00ffff', 'ability': ABILITY_NONE}
        self.game.board[10][4] = {'color': '#00ffff', 'ability': ABILITY_NONE}

        cleared = execute_lightning(self.game.board, lx, ly)
        self.assertIsNone(self.game.board[15][0])
        self.assertIsNone(self.game.board[15][9])
        self.assertIsNone(self.game.board[10][4])

if __name__ == '__main__':
    unittest.main()
