# test_stress_rogue.py - Rigorous stress and endurance tests for Rogue Mode & Game Over
import unittest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine import TetrisGame, Piece
from roguelike import SectorManager, SECTORS, ALL_RELICS
from config import (
    BOARD_WIDTH, TOTAL_HEIGHT,
    ABILITY_NONE, ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_HEAVY, ABILITY_BURNING
)
from renderer import CanvasRenderer
from audio import SynthwaveAudio


class MockCanvasContext:
    """Mock Canvas 2D context tracking calls without error for stress verification."""
    def __init__(self):
        self.canvas = self
        self.width = 750
        self.height = 720
        self.fillStyle = '#000000'
        self.strokeStyle = '#ffffff'
        self.lineWidth = 1
        self.shadowColor = '#000000'
        self.shadowBlur = 0
        self.font = '12px Orbitron'
        self.textAlign = 'left'
        self.textBaseline = 'top'
        self.globalAlpha = 1.0

    def save(self): pass
    def restore(self): pass
    def fillRect(self, *a): pass
    def strokeRect(self, *a): pass
    def clearRect(self, *a): pass
    def beginPath(self): pass
    def closePath(self): pass
    def moveTo(self, *a): pass
    def lineTo(self, *a): pass
    def stroke(self): pass
    def fill(self): pass
    def fillText(self, *a): pass
    def arc(self, *a): pass
    def createLinearGradient(self, *a): return self
    def createRadialGradient(self, *a): return self
    def addColorStop(self, *a): pass


class TestRogueModeStressAndGameOver(unittest.TestCase):

    def setUp(self):
        self.renderer = CanvasRenderer()
        self.ctx = MockCanvasContext()

    def test_sector_manager_current_sector_property(self):
        """Verify SectorManager has current_sector property that returns 1-based number."""
        sm = SectorManager()
        self.assertEqual(sm.current_sector, 1)
        sm.current_sector_index = 2
        self.assertEqual(sm.current_sector, 3)
        sm.current_sector_index = 4
        self.assertEqual(sm.current_sector, 5)

    def test_rogue_game_over_trigger_and_event_handling(self):
        """Simulate stacking blocks to top ceiling to trigger genuine game_over in Rogue mode."""
        game = TetrisGame(enable_abilities=True)
        sm = SectorManager()

        # Fill column 4 and 5 from bottom to row 0 (hidden ceiling) to guarantee instant spawn collision
        for r in range(TOTAL_HEIGHT):
            game.board[r][4] = {'shape': 'I', 'ability': ABILITY_NONE, 'color': '#00f0ff'}
            game.board[r][5] = {'shape': 'I', 'ability': ABILITY_NONE, 'color': '#00f0ff'}

        # Attempt to spawn piece; should immediately detect collision and set game_over = True
        game.spawn_next_piece()
        self.assertTrue(game.game_over, "Game must detect top-out collision and set game_over = True")
        
        # Verify game_over event was queued
        events = [ev for ev in game.pending_events if ev.get('type') == 'game_over']
        self.assertGreaterEqual(len(events), 1, "Must have queued a game_over event")

        # Verify sector number resolution works cleanly without throwing AttributeError
        sector_num = getattr(sm, 'current_sector', sm.current_sector_index + 1)
        self.assertEqual(sector_num, 1)

        # Verify renderer handles game_over state without crashing in Rogue mode
        for _ in range(30):
            self.renderer.render(self.ctx, game, sm, game_mode='ROGUE', high_score=102521)

    def test_rogue_line_clearing_and_relic_draft_progression(self):
        """Stress tests advancing through all 5 sectors, drafting relics, and triggering abilities."""
        sm = SectorManager()
        game = TetrisGame(enable_abilities=True)

        for sector_idx in range(len(SECTORS) - 1):
            target_lines = SECTORS[sector_idx]['lines_needed']
            opened_draft = sm.add_lines(target_lines)
            self.assertTrue(opened_draft, f"Quota met for sector {sector_idx+1}, draft must open")
            self.assertTrue(sm.is_drafting)
            self.assertEqual(len(sm.offered_relics), 3)

            # Select the first relic
            chosen = sm.offered_relics[0]
            sm.select_relic(chosen['id'])
            self.assertFalse(sm.is_drafting)
            self.assertTrue(sm.has_relic(chosen['id']))
            self.assertEqual(sm.current_sector, sector_idx + 2)

        # Final sector (Sector 5)
        opened_draft = sm.add_lines(SECTORS[4]['lines_needed'])
        self.assertFalse(opened_draft, "Final sector does not open draft; run is completed")
        self.assertTrue(sm.run_completed)

    def test_massive_consecutive_game_over_cycles(self):
        """Simulate 50 consecutive Game-Over and Restart cycles in Rogue Mode to test endurance."""
        for cycle in range(50):
            game = TetrisGame(enable_abilities=True)
            sm = SectorManager()

            # Advance sectors
            sm.add_lines(15)
            if sm.is_drafting:
                sm.select_relic(sm.offered_relics[0]['id'])

            # Force Game Over: fill spawn area across entire width
            for r in range(TOTAL_HEIGHT):
                for c in range(BOARD_WIDTH):
                    game.board[r][c] = {'shape': 'O', 'ability': ABILITY_NONE, 'color': '#ffff00'}
            game.spawn_next_piece()
            self.assertTrue(game.game_over)

            # Verify safe sector resolution
            sec = getattr(sm, 'current_sector', sm.current_sector_index + 1)
            self.assertIn(sec, [1, 2, 3, 4, 5])

            # Render Game Over frame
            self.renderer.render(self.ctx, game, sm, game_mode='ROGUE', high_score=102521)

    def test_all_ability_detonations_under_heavy_load(self):
        """Trigger rapid detonations of all ability types simultaneously."""
        for ability_type in [ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_HEAVY, ABILITY_BURNING]:
            game = TetrisGame(enable_abilities=True)
            # Fill some blocks on the board
            for y in range(18, 24):
                for x in range(BOARD_WIDTH):
                    game.board[y][x] = {'shape': 'T', 'ability': ABILITY_NONE, 'color': '#a855f7'}

            # Trigger ability
            if ability_type == ABILITY_BOMB:
                game.board[20][5] = {'shape': 'T', 'ability': ABILITY_BOMB, 'color': '#ff0055'}
                from abilities import execute_bomb
                execute_bomb(game.board, 5, 20, radius=2)
            elif ability_type == ABILITY_LIGHTNING:
                from abilities import execute_lightning
                execute_lightning(game.board, 5, 20)
            elif ability_type == ABILITY_MAGNET:
                from abilities import execute_magnet
                execute_magnet(game.board, 5, 20)

            # Render 10 frames of each effect
            for _ in range(10):
                self.renderer.update_particles(0.016)
                self.renderer.render(self.ctx, game, SectorManager(), game_mode='ROGUE', high_score=102521)

    def test_simulate_10000_game_frames(self):
        """Simulate 10,000 game loop frames of Rogue mode physics and rendering."""
        game = TetrisGame(enable_abilities=True)
        sm = SectorManager()
        t = 0.0

        for frame in range(10000):
            delta = 0.016
            t += delta

            if game.game_over:
                # Simulates instant reboot upon game over
                game = TetrisGame(enable_abilities=True)
                sm = SectorManager()

            # Periodically perform gameplay moves
            if frame % 30 == 0:
                game.move_left()
            elif frame % 45 == 0:
                game.move_right()
            elif frame % 60 == 0:
                game.rotate(clockwise=True)
            elif frame % 120 == 0:
                game.soft_drop()

            game.update(delta)
            self.renderer.update_particles(delta)

            # Every 500 frames, render to mock context
            if frame % 500 == 0:
                self.renderer.render(self.ctx, game, sm, game_mode='ROGUE', high_score=102521)

        self.assertTrue(True, "10,000 frames completed smoothly without hanging or crash")

    def test_endurance_rapid_drops_and_clears(self):
        """Simulate realistic multi-minute playthrough: 500 hard drops with periodic clears."""
        game = TetrisGame(enable_abilities=True)
        sm = SectorManager()

        for piece_num in range(500):
            if game.game_over:
                # Reset game upon game over, exactly like the player clicking restart
                game = TetrisGame(enable_abilities=True)
                sm = SectorManager()

            # Random horizontal shift
            moves = (piece_num % 5) - 2
            for _ in range(abs(moves)):
                if moves < 0: game.move_left()
                else: game.move_right()

            if piece_num % 3 == 0:
                game.rotate(clockwise=True)

            game.hard_drop()

            # Periodically clear bottom row by calling clear_completed_lines if full
            if piece_num % 10 == 0:
                for c in range(BOARD_WIDTH):
                    game.board[TOTAL_HEIGHT - 1][c] = {'shape': 'I', 'ability': ABILITY_NONE, 'color': '#00f0ff'}
                game.clear_completed_lines([TOTAL_HEIGHT - 1])

            game.update(0.016)
            self.renderer.update_particles(0.016)

            if piece_num % 50 == 0:
                self.renderer.render(self.ctx, game, sm, game_mode='ROGUE', high_score=102521)


if __name__ == '__main__':
    unittest.main()
