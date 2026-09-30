# renderer.py - High-DPI Cyberpunk Neon Canvas 2D Renderer
# Written straightforwardly without confusing over-abstractions.

import math
import random
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, HIDDEN_ROWS, TOTAL_HEIGHT,
    BLOCK_SIZE, COLORS, ABILITY_NONE, ABILITY_INFO
)
from srs_tables import TETROMINO_SHAPES

class Particle:
    """A single floating neon spark produced by line clears or bomb explosions."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2.0, 7.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0  # Fades from 1.0 to 0.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.uniform(2.0, 5.0)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # Subtle gravity
        self.life -= self.decay

    def is_alive(self):
        return self.life > 0.0


class CanvasRenderer:
    """
    Renders the game onto an HTML5 2D Canvas context.
    Features vibrant cyberpunk neon glow, ghost piece, particle bursts,
    ability icons, HUD, and screen shake.
    """
    def __init__(self):
        self.particles = []
        self.screen_shake_time = 0.0
        self.shake_magnitude = 0.0

    def trigger_shake(self, magnitude=6.0, duration=0.25):
        """Applies screen shake for hard drops and explosions."""
        self.shake_magnitude = magnitude
        self.screen_shake_time = duration

    def spawn_clear_particles(self, y_row, color='#00f0f0', count=25):
        """Spawns sparks across a cleared horizontal row."""
        canvas_y = (y_row - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        for _ in range(count):
            canvas_x = random.uniform(0, BOARD_WIDTH * BLOCK_SIZE)
            self.particles.append(Particle(canvas_x, canvas_y, color))

    def spawn_explosion_particles(self, center_x, center_y, color='#ff4500', count=40):
        """Spawns an explosive circular blast of sparks for bomb blocks."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        for _ in range(count):
            self.particles.append(Particle(cx, cy, color))

    def update_particles(self, delta_time):
        """Updates physics for all active particles and screen shake."""
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.is_alive()]

        if self.screen_shake_time > 0.0:
            self.screen_shake_time -= delta_time
            if self.screen_shake_time < 0.0:
                self.screen_shake_time = 0.0

    def render(self, ctx, game, sector_mgr=None, game_mode='CLASSIC'):
        """
        Main drawing function called once per animation frame (60 FPS).
        """
        # Board dimensions on canvas
        board_pixel_w = BOARD_WIDTH * BLOCK_SIZE
        board_pixel_h = BOARD_HEIGHT * BLOCK_SIZE
        offset_x = 180  # Left margin for Hold piece panel
        offset_y = 60   # Top margin

        # Apply screen shake if active
        ctx.save()
        if self.screen_shake_time > 0.0:
            shake_offset_x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            shake_offset_y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            ctx.translate(shake_offset_x, shake_offset_y)

        # 1. Clear background
        ctx.fillStyle = '#060814'
        ctx.fillRect(0, 0, 750, 720)

        # 2. Draw Main Matrix Background & Grid Lines
        ctx.fillStyle = '#0b0f24'
        ctx.fillRect(offset_x, offset_y, board_pixel_w, board_pixel_h)

        # Subtle neon grid lines
        ctx.strokeStyle = '#161d3f'
        ctx.lineWidth = 1
        for col in range(BOARD_WIDTH + 1):
            gx = offset_x + col * BLOCK_SIZE
            ctx.beginPath()
            ctx.moveTo(gx, offset_y)
            ctx.lineTo(gx, offset_y + board_pixel_h)
            ctx.stroke()

        for row in range(BOARD_HEIGHT + 1):
            gy = offset_y + row * BLOCK_SIZE
            ctx.beginPath()
            ctx.moveTo(offset_x, gy)
            ctx.lineTo(offset_x + board_pixel_w, gy)
            ctx.stroke()

        # Board glowing border
        ctx.strokeStyle = '#00f0f0'
        ctx.shadowColor = '#00f0f0'
        ctx.shadowBlur = 10
        ctx.lineWidth = 2
        ctx.strokeRect(offset_x, offset_y, board_pixel_w, board_pixel_h)
        ctx.shadowBlur = 0  # Reset shadow blur

        # 3. Draw Locked Blocks on the Board
        for row in range(HIDDEN_ROWS, TOTAL_HEIGHT):
            for col in range(BOARD_WIDTH):
                cell = game.board[row][col]
                if cell is not None:
                    bx = offset_x + col * BLOCK_SIZE
                    by = offset_y + (row - HIDDEN_ROWS) * BLOCK_SIZE
                    self.draw_neon_block(ctx, bx, by, cell['color'], cell.get('ability', ABILITY_NONE))

        # 4. Draw Ghost Piece (Holographic landing guide)
        if game.current_piece and not game.game_over:
            ghost_y = game.get_ghost_y()
            ghost_blocks = game.current_piece.get_block_positions(offset_y=(ghost_y - game.current_piece.y))
            for gx, gy in ghost_blocks:
                if gy >= HIDDEN_ROWS:
                    bx = offset_x + gx * BLOCK_SIZE
                    by = offset_y + (gy - HIDDEN_ROWS) * BLOCK_SIZE
                    self.draw_ghost_block(ctx, bx, by, game.current_piece.color)

        # 5. Draw Active Falling Piece
        if game.current_piece and not game.game_over:
            blocks = game.current_piece.get_block_positions()
            ability = game.current_piece.ability
            ability_idx = game.current_piece.ability_block_index
            for i, (px, py) in enumerate(blocks):
                if py >= HIDDEN_ROWS:
                    bx = offset_x + px * BLOCK_SIZE
                    by = offset_y + (py - HIDDEN_ROWS) * BLOCK_SIZE
                    block_ability = ability if (i == ability_idx) else ABILITY_NONE
                    self.draw_neon_block(ctx, bx, by, game.current_piece.color, block_ability)

        # 6. Draw Line-Clear / Bomb Explosion Particles
        for p in self.particles:
            ctx.save()
            ctx.globalAlpha = max(0.0, p.life)
            ctx.fillStyle = p.color
            ctx.shadowColor = p.color
            ctx.shadowBlur = 8
            ctx.beginPath()
            ctx.arc(offset_x + p.x, offset_y + p.y, p.size, 0, math.pi * 2)
            ctx.fill()
            ctx.restore()

        # 7. Draw UI Panels: Hold Queue (Left) & Next Queue (Right)
        self.draw_hold_panel(ctx, game, offset_x - 150, offset_y)
        self.draw_next_panel(ctx, game, offset_x + board_pixel_w + 30, offset_y)

        # 8. Draw HUD: Score, Level, Lines, Sector info
        self.draw_hud(ctx, game, sector_mgr, game_mode, offset_x - 150, offset_y + 190)

        # 9. Game Over or Pause Overlay
        if game.game_over:
            self.draw_banner(ctx, "SYSTEM CORRUPTED", "PRESS R TO REBOOT", '#ff0055')
        elif game.is_paused:
            self.draw_banner(ctx, "SYSTEM PAUSED", "PRESS P TO RESUME", '#00f0f0')

        ctx.restore()

    def draw_neon_block(self, ctx, x, y, color, ability=ABILITY_NONE):
        """Draws a single block with a glowing neon border and internal gradient."""
        ctx.save()
        
        # Block inner background
        ctx.fillStyle = color
        ctx.shadowColor = color
        ctx.shadowBlur = 6
        ctx.fillRect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
        ctx.shadowBlur = 0

        # Block inner highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.25)'
        ctx.fillRect(x + 2, y + 2, BLOCK_SIZE - 4, 3)
        ctx.fillRect(x + 2, y + 2, 3, BLOCK_SIZE - 4)

        # If block has a special ability, draw its glowing icon!
        if ability != ABILITY_NONE and ability in ABILITY_INFO:
            info = ABILITY_INFO[ability]
            ctx.font = '16px sans-serif'
            ctx.textAlign = 'center'
            ctx.textBaseline = 'middle'
            ctx.fillText(info['symbol'], x + (BLOCK_SIZE / 2), y + (BLOCK_SIZE / 2))

        ctx.restore()

    def draw_ghost_block(self, ctx, x, y, color):
        """Draws a faint holographic outline representing where the piece will land."""
        ctx.save()
        ctx.strokeStyle = color
        ctx.globalAlpha = 0.35
        ctx.lineWidth = 1.5
        ctx.strokeRect(x + 2, y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4)
        ctx.restore()

    def draw_hold_panel(self, ctx, game, px, py):
        """Draws the Hold Piece panel on the left."""
        ctx.save()
        ctx.fillStyle = '#0b0f24'
        ctx.fillRect(px, py, 120, 120)
        ctx.strokeStyle = '#b000ff'
        ctx.lineWidth = 1.5
        ctx.strokeRect(px, py, 120, 120)

        # Label
        ctx.fillStyle = '#b000ff'
        ctx.font = 'bold 13px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText("HOLD [C]", px + 60, py + 20)

        if game.hold_piece:
            alpha = 1.0 if game.can_hold else 0.4
            ctx.globalAlpha = alpha
            self.draw_mini_piece(ctx, game.hold_piece, px + 25, py + 45)

        ctx.restore()

    def draw_next_panel(self, ctx, game, px, py):
        """Draws the Next Pieces preview queue on the right."""
        ctx.save()
        panel_h = 360
        ctx.fillStyle = '#0b0f24'
        ctx.fillRect(px, py, 130, panel_h)
        ctx.strokeStyle = '#00f0f0'
        ctx.lineWidth = 1.5
        ctx.strokeRect(px, py, 130, panel_h)

        # Label
        ctx.fillStyle = '#00f0f0'
        ctx.font = 'bold 13px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText("NEXT", px + 65, py + 22)

        # Preview next 4 pieces
        preview_y = py + 45
        for i in range(min(4, len(game.next_queue))):
            piece = game.next_queue[i]
            self.draw_mini_piece(ctx, piece, px + 30, preview_y)
            preview_y += 75

        ctx.restore()

    def draw_mini_piece(self, ctx, piece, base_x, base_y):
        """Draws a scaled-down 4-block piece for Next and Hold previews."""
        mini_size = 18
        shape_offsets = TETROMINO_SHAPES[piece.shape][0]
        for idx, (ox, oy) in enumerate(shape_offsets):
            mx = base_x + ox * mini_size
            my = base_y + oy * mini_size
            
            ctx.fillStyle = piece.color
            ctx.fillRect(mx, my, mini_size - 1, mini_size - 1)
            
            # Show ability icon even on preview!
            if piece.ability != ABILITY_NONE and idx == piece.ability_block_index:
                info = ABILITY_INFO.get(piece.ability)
                if info:
                    ctx.font = '10px sans-serif'
                    ctx.textAlign = 'center'
                    ctx.textBaseline = 'middle'
                    ctx.fillText(info['symbol'], mx + mini_size / 2, my + mini_size / 2)

    def draw_hud(self, ctx, game, sector_mgr, game_mode, px, py):
        """Draws Score, Level, Lines, Sector progress, and Active Relics."""
        ctx.save()
        ctx.textAlign = 'left'

        # Score
        ctx.fillStyle = '#7a889b'
        ctx.font = '11px sans-serif'
        ctx.fillText("SCORE", px, py)
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 20px sans-serif'
        ctx.fillText(str(game.score), px, py + 24)

        # Level
        ctx.fillStyle = '#7a889b'
        ctx.font = '11px sans-serif'
        ctx.fillText("LEVEL", px, py + 55)
        ctx.fillStyle = '#00ff66'
        ctx.font = 'bold 20px sans-serif'
        ctx.fillText(str(game.level), px, py + 79)

        # Lines
        ctx.fillStyle = '#7a889b'
        ctx.font = '11px sans-serif'
        ctx.fillText("LINES", px, py + 110)
        ctx.fillStyle = '#ffe600'
        ctx.font = 'bold 20px sans-serif'
        ctx.fillText(str(game.lines_cleared), px, py + 134)

        # Freeze Bar Indicator
        if game.freeze_timer > 0.0:
            ctx.fillStyle = '#87cefa'
            ctx.font = 'bold 12px sans-serif'
            ctx.fillText(f"🧊 FROZEN: {game.freeze_timer:.1f}s", px, py + 165)

        # Sector Info for Rogue Mode
        if game_mode == 'ROGUE' and sector_mgr:
            sec = sector_mgr.get_current_sector()
            ctx.fillStyle = '#ff0055'
            ctx.font = 'bold 13px sans-serif'
            ctx.fillText(f"SECTOR {sec['sector']}/5", px, py + 195)
            
            # Progress bar
            progress = min(1.0, sector_mgr.sector_lines_cleared / sec['lines_needed'])
            ctx.fillStyle = '#161d3f'
            ctx.fillRect(px, py + 205, 120, 8)
            ctx.fillStyle = '#ff0055'
            ctx.fillRect(px, py + 205, int(120 * progress), 8)

            # Acquired Relics icons
            if len(sector_mgr.acquired_relics) > 0:
                ctx.fillStyle = '#a0aec0'
                ctx.font = '10px sans-serif'
                ctx.fillText("RELICS:", px, py + 230)
                relic_icons = " ".join([r['icon'] for r in sector_mgr.acquired_relics])
                ctx.font = '16px sans-serif'
                ctx.fillText(relic_icons, px, py + 250)

        # Combo announcement
        if game.combo > 0:
            ctx.fillStyle = '#ff00ff'
            ctx.font = 'bold 14px sans-serif'
            ctx.fillText(f"⚡ COMBO x{game.combo}!", px, py + 285)

        ctx.restore()

    def draw_banner(self, ctx, title, subtitle, color):
        """Draws a centered pop-up banner for Game Over or Pause."""
        ctx.save()
        ctx.fillStyle = 'rgba(6, 8, 20, 0.85)'
        ctx.fillRect(150, 240, 360, 140)
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.shadowColor = color
        ctx.shadowBlur = 15
        ctx.strokeRect(150, 240, 360, 140)

        ctx.fillStyle = color
        ctx.font = 'bold 24px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(title, 330, 295)

        ctx.fillStyle = '#ffffff'
        ctx.font = '14px sans-serif'
        ctx.fillText(subtitle, 330, 340)
        ctx.restore()
