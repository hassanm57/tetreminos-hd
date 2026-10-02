# test_renderer.py - Unit tests for responsive rendering pipeline and mobile layout
import unittest
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from engine import TetrisGame, Piece
from renderer import CanvasRenderer
from roguelike import SectorManager
from config import ABILITY_BOMB, ABILITY_NONE


class MockCanvas:
    def __init__(self, width=750, height=720):
        self.width = width
        self.height = height


class MockContext:
    def __init__(self, width=750, height=720):
        self.canvas = MockCanvas(width, height)
        self.fillStyle = '#000000'
        self.strokeStyle = '#000000'
        self.lineWidth = 1
        self.shadowBlur = 0
        self.shadowColor = 'transparent'
        self.globalAlpha = 1.0
        self.font = ''
        self.textAlign = 'left'
        self.textBaseline = 'top'

    def save(self):
        pass

    def restore(self):
        pass

    def translate(self, x, y):
        pass

    def fillRect(self, x, y, w, h):
        pass

    def strokeRect(self, x, y, w, h):
        pass

    def beginPath(self):
        pass

    def closePath(self):
        pass

    def moveTo(self, x, y):
        pass

    def lineTo(self, x, y):
        pass

    def arc(self, x, y, r, sa, ea):
        pass

    def fill(self):
        pass

    def stroke(self):
        pass

    def fillText(self, text, x, y):
        pass

    def createLinearGradient(self, x0, y0, x1, y1):
        class MockGradient:
            def addColorStop(self, offset, color):
                pass
        return MockGradient()

    def createRadialGradient(self, x0, y0, r0, x1, y1, r1):
        class MockGradient:
            def addColorStop(self, offset, color):
                pass
        return MockGradient()


class TestResponsiveRenderer(unittest.TestCase):

    def setUp(self):
        self.renderer = CanvasRenderer()
        self.game = TetrisGame(enable_abilities=True)
        self.sector_mgr = SectorManager()

    def test_desktop_rendering_pipeline(self):
        """Renderer should execute all drawing operations for desktop 750x720 layout without errors."""
        desktop_ctx = MockContext(width=750, height=720)
        # Should execute cleanly
        self.renderer.render(desktop_ctx, self.game, self.sector_mgr, game_mode='ROGUE', high_score=5000)

    def test_mobile_rendering_pipeline(self):
        """Renderer should dynamically switch to mobile layout when canvas width is < 550."""
        mobile_ctx = MockContext(width=360, height=720)
        # Should execute cleanly with mobile top bar and mobile bottom bar
        self.renderer.render(mobile_ctx, self.game, self.sector_mgr, game_mode='ROGUE', high_score=5000)

    def test_mobile_classic_mode(self):
        """Renderer should execute cleanly for mobile in CLASSIC mode (no sector manager)."""
        mobile_ctx = MockContext(width=360, height=720)
        classic_game = TetrisGame(enable_abilities=False)
        self.renderer.render(mobile_ctx, classic_game, None, game_mode='CLASSIC', high_score=12000)

    def test_mini_piece_custom_size(self):
        """draw_mini_piece should accept and scale according to mini_size parameter."""
        ctx = MockContext(width=360, height=720)
        piece = Piece('T', ability=ABILITY_BOMB)
        # Should render without exception with 11px blocks on mobile
        self.renderer.draw_mini_piece(ctx, piece, base_x=10, base_y=10, mini_size=11)

    def test_banner_dimensions_mobile_and_desktop(self):
        """draw_banner should scale cleanly for both mobile (360) and desktop (750)."""
        mobile_ctx = MockContext(width=360, height=720)
        desktop_ctx = MockContext(width=750, height=720)
        self.renderer.draw_banner(mobile_ctx, "SYSTEM CORRUPTED", "SCORE: 100 // TAP TO RESTART", '#ff0055', 360, 720)
        self.renderer.draw_banner(desktop_ctx, "SYSTEM PAUSED", "PRESS P TO RESUME", '#00f0f0', 750, 720)

    def test_powerup_block_glow_rendering(self):
        """draw_neon_block with ability should execute cleanly with radiant glow halo on both desktop and mobile."""
        from config import ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_BURNING, ABILITY_HEAVY
        ctx = MockContext(width=750, height=720)
        abilities = [ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_BURNING, ABILITY_HEAVY]
        for ab in abilities:
            self.renderer.draw_neon_block(ctx, x=50, y=100, color='#00f0f0', ability=ab)

    def test_floating_powerup_icon_rendering(self):
        """draw_floating_powerup_icon should render above the block with dark backing and pointer beacon."""
        from config import ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_BURNING, ABILITY_HEAVY
        ctx_desktop = MockContext(width=750, height=720)
        ctx_mobile = MockContext(width=360, height=720)
        self.renderer.is_mobile = False
        self.renderer.draw_floating_powerup_icon(ctx_desktop, x=60, y=120, ability=ABILITY_BOMB)
        self.renderer.is_mobile = True
        self.renderer.draw_floating_powerup_icon(ctx_mobile, x=60, y=120, ability=ABILITY_LIGHTNING)

if __name__ == '__main__':
    unittest.main()

