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

    def test_burning_block_detonation(self):
        """Burning mino should countdown and detonate surrounding 4 neighbors."""
        from abilities import update_burning_blocks
        from config import ABILITY_BURNING
        
        # Place burning block at (5, 18)
        self.game.board[18][5] = {'color': '#ff4500', 'ability': ABILITY_BURNING, 'burn_timer': 1.0}
        # Place neighbors
        self.game.board[17][5] = {'color': '#00ffff', 'ability': ABILITY_NONE}
        self.game.board[19][5] = {'color': '#00ffff', 'ability': ABILITY_NONE}
        self.game.board[18][4] = {'color': '#00ffff', 'ability': ABILITY_NONE}
        self.game.board[18][6] = {'color': '#00ffff', 'ability': ABILITY_NONE}

        # Tick 0.5s -> shouldn't detonate yet
        dets = update_burning_blocks(self.game.board, 0.5)
        self.assertEqual(len(dets), 0)
        self.assertAlmostEqual(self.game.board[18][5]['burn_timer'], 0.5)

        # Tick another 0.6s -> should detonate!
        dets = update_burning_blocks(self.game.board, 0.6)
        self.assertEqual(len(dets), 1)
        self.assertEqual(dets[0]['x'], 5)
        self.assertEqual(dets[0]['y'], 18)
        # All 5 cells (center + 4 orthogonal) should now be None
        self.assertIsNone(self.game.board[18][5])
        self.assertIsNone(self.game.board[17][5])
        self.assertIsNone(self.game.board[19][5])
        self.assertIsNone(self.game.board[18][4])
        self.assertIsNone(self.game.board[18][6])

    def test_heavy_rotation_restriction(self):
        """Heavy block should not be able to rotate."""
        from config import ABILITY_HEAVY
        self.game.current_piece = Piece('T', ABILITY_HEAVY)
        initial_rot = self.game.current_piece.rotation
        rotated = self.game.rotate(clockwise=True)
        self.assertFalse(rotated)
        self.assertEqual(self.game.current_piece.rotation, initial_rot)

    def test_renderer_effect_triggers(self):
        """Renderer triggers should populate shockwaves, particles, and badges without error."""
        from renderer import CanvasRenderer
        renderer = CanvasRenderer()
        renderer.trigger_bomb_effect(5, 15, cleared_count=9)
        self.assertGreater(len(renderer.particles), 0)
        self.assertGreater(len(renderer.shockwaves), 0)
        self.assertGreater(len(renderer.floating_badges), 0)
        self.assertGreater(len(renderer.screen_flashes), 0)

        renderer.trigger_lightning_effect(4, 12, cleared_count=18)
        self.assertGreater(len(renderer.lightning_effects), 0)

        renderer.trigger_freeze_effect(5, 10, duration=8.0)
        renderer.trigger_magnet_effect(5, 10, moved_count=3)
        renderer.trigger_burning_placed_effect(5, 10)
        renderer.trigger_burning_exploded_effect(5, 10, cleared_count=5)
        renderer.trigger_heavy_landed_effect(5, 10)

        # Update all effects by delta_time
        renderer.update_particles(0.1)
        self.assertGreater(len(renderer.particles), 0)

if __name__ == '__main__':
    unittest.main()
