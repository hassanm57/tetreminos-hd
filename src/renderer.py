# renderer.py - High-DPI Cyberpunk Neon Canvas 2D Renderer
# Written straightforwardly without confusing over-abstractions.

import math
import random
import time
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, HIDDEN_ROWS, TOTAL_HEIGHT,
    BLOCK_SIZE, COLORS, ABILITY_NONE, ABILITY_INFO, LINE_CLEAR_DELAY
)
from srs_tables import TETROMINO_SHAPES

class Particle:
    """
    Versatile physics particle for sparks, flames, ice shards, electric arcs, and rock debris.
    """
    def __init__(self, x, y, color, vx=None, vy=None, style='spark', size=None, life=1.0, decay=None, gravity=0.15, drag=0.98):
        self.x = x
        self.y = y
        self.color = color
        self.style = style  # 'spark', 'flame', 'ice', 'electric', 'rock', 'smoke'
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.drag = drag
        self.angle = random.uniform(0, math.pi * 2)
        self.v_rot = random.uniform(-0.15, 0.15)
        
        if vx is not None and vy is not None:
            self.vx = vx
            self.vy = vy
        else:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2.0, 7.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed

        self.size = size if size is not None else random.uniform(2.5, 5.0)
        self.decay = decay if decay is not None else random.uniform(0.02, 0.05)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.drag
        self.vy *= self.drag
        self.vy += self.gravity
        self.angle += self.v_rot
        self.life -= self.decay
        
        if self.style == 'flame':
            self.size += 0.14
        elif self.style == 'smoke':
            self.size += 0.22

    def is_alive(self):
        return self.life > 0.0

    def draw(self, ctx, offset_x, offset_y, is_mobile=False):
        if not self.is_alive():
            return
        
        px = offset_x + self.x
        py = offset_y + self.y
        alpha = max(0.0, min(1.0, self.life / self.max_life))
        
        ctx.save()
        ctx.globalAlpha = alpha

        if self.style == 'spark':
            ctx.fillStyle = self.color
            if not is_mobile:
                ctx.shadowColor = self.color
                ctx.shadowBlur = 8
            ctx.beginPath()
            ctx.arc(px, py, max(1.0, self.size * alpha), 0, math.pi * 2)
            ctx.fill()

        elif self.style == 'flame':
            ctx.fillStyle = self.color
            if not is_mobile:
                ctx.shadowColor = self.color
                ctx.shadowBlur = 14
            ctx.beginPath()
            ctx.arc(px, py, self.size, 0, math.pi * 2)
            ctx.fill()

        elif self.style == 'ice':
            ctx.translate(px, py)
            ctx.rotate(self.angle)
            ctx.fillStyle = self.color
            if not is_mobile:
                ctx.shadowColor = '#38bdf8'
                ctx.shadowBlur = 8
            sz = self.size
            ctx.beginPath()
            ctx.moveTo(0, -sz)
            ctx.lineTo(sz * 0.6, 0)
            ctx.lineTo(0, sz)
            ctx.lineTo(-sz * 0.6, 0)
            ctx.closePath()
            ctx.fill()

        elif self.style == 'electric':
            jx = px + random.uniform(-3, 3)
            jy = py + random.uniform(-3, 3)
            ctx.strokeStyle = self.color
            if not is_mobile:
                ctx.shadowColor = self.color
                ctx.shadowBlur = 10
            ctx.lineWidth = 2
            ctx.beginPath()
            ctx.moveTo(px, py)
            ctx.lineTo(jx, jy)
            ctx.stroke()

        elif self.style == 'rock':
            ctx.translate(px, py)
            ctx.rotate(self.angle)
            ctx.fillStyle = self.color
            ctx.strokeStyle = '#475569'
            ctx.lineWidth = 1
            sz = self.size
            ctx.fillRect(-sz / 2, -sz / 2, sz, sz)
            ctx.strokeRect(-sz / 2, -sz / 2, sz, sz)

        elif self.style == 'smoke':
            ctx.fillStyle = 'rgba(75, 85, 99, 0.45)'
            ctx.beginPath()
            ctx.arc(px, py, self.size, 0, math.pi * 2)
            ctx.fill()

        ctx.restore()


class ShockwaveEffect:
    """Expanding energy wave / ripple ring with easing and radial glow."""
    def __init__(self, x, y, max_radius=110, duration=0.45, color_outer='#ff3b00', color_inner='#ffe600', ring_width=4.5, rings_count=1):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.duration = duration
        self.elapsed = 0.0
        self.color_outer = color_outer
        self.color_inner = color_inner
        self.ring_width = ring_width
        self.rings_count = rings_count

    def update(self, dt):
        self.elapsed += dt

    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, ctx, offset_x, offset_y):
        if not self.is_alive():
            return
        
        progress = min(1.0, self.elapsed / self.duration)
        ease = 1.0 - math.pow(1.0 - progress, 3)
        alpha = (1.0 - progress)
        cx = offset_x + self.x
        cy = offset_y + self.y

        ctx.save()
        
        for i in range(self.rings_count):
            r_delay = i * 0.14
            ring_prog = max(0.0, min(1.0, (progress - r_delay) / (1.0 - r_delay))) if r_delay < 1.0 else 0.0
            if ring_prog <= 0.0:
                continue
            r_ease = 1.0 - math.pow(1.0 - ring_prog, 3)
            r = r_ease * self.max_radius
            r_alpha = (1.0 - ring_prog) * alpha

            ctx.strokeStyle = self.color_outer
            ctx.shadowColor = self.color_outer
            ctx.shadowBlur = int(14 * r_alpha)
            ctx.lineWidth = max(1.0, self.ring_width * (1.0 - ring_prog * 0.6))
            ctx.globalAlpha = r_alpha
            ctx.beginPath()
            ctx.arc(cx, cy, r, 0, math.pi * 2)
            ctx.stroke()

        r_main = ease * self.max_radius * 0.65
        if r_main > 0:
            ctx.globalAlpha = alpha * 0.45
            grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r_main)
            grad.addColorStop(0.0, self.color_inner)
            grad.addColorStop(1.0, 'rgba(0, 0, 0, 0)')
            ctx.fillStyle = grad
            ctx.beginPath()
            ctx.arc(cx, cy, r_main, 0, math.pi * 2)
            ctx.fill()

        ctx.restore()


class LightningCrossEffect:
    """Blinding cross laser and animated high-voltage electric arcs."""
    def __init__(self, bolt_x, bolt_y, duration=0.42):
        self.bolt_x = bolt_x
        self.bolt_y = bolt_y
        self.duration = duration
        self.elapsed = 0.0
        self.jitter_offsets = [random.uniform(-7, 7) for _ in range(30)]

    def update(self, dt):
        self.elapsed += dt
        if random.random() < 0.4:
            self.jitter_offsets = [random.uniform(-7, 7) for _ in range(30)]

    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, ctx, offset_x, offset_y):
        if not self.is_alive():
            return
        
        progress = min(1.0, self.elapsed / self.duration)
        alpha = math.sin(progress * math.pi)
        
        board_w = BOARD_WIDTH * BLOCK_SIZE
        board_h = BOARD_HEIGHT * BLOCK_SIZE
        
        cx = offset_x + self.bolt_x * BLOCK_SIZE + BLOCK_SIZE / 2
        cy = offset_y + (self.bolt_y - HIDDEN_ROWS) * BLOCK_SIZE + BLOCK_SIZE / 2

        ctx.save()

        # Broad electric ambient glow
        ctx.globalAlpha = alpha * 0.5
        ctx.strokeStyle = '#00f0f0'
        ctx.shadowColor = '#00f0f0'
        ctx.shadowBlur = 24
        ctx.lineWidth = max(2.0, 28 * (1.0 - progress))
        ctx.beginPath()
        ctx.moveTo(offset_x, cy)
        ctx.lineTo(offset_x + board_w, cy)
        ctx.moveTo(cx, offset_y)
        ctx.lineTo(cx, offset_y + board_h)
        ctx.stroke()

        # Vivid neon beam
        ctx.globalAlpha = alpha * 0.85
        ctx.strokeStyle = '#38bdf8'
        ctx.shadowBlur = 12
        ctx.lineWidth = max(1.5, 11 * (1.0 - progress))
        ctx.beginPath()
        ctx.moveTo(offset_x, cy)
        ctx.lineTo(offset_x + board_w, cy)
        ctx.moveTo(cx, offset_y)
        ctx.lineTo(cx, offset_y + board_h)
        ctx.stroke()

        # Blinding white laser core
        ctx.globalAlpha = alpha
        ctx.strokeStyle = '#ffffff'
        ctx.shadowColor = '#ffffff'
        ctx.shadowBlur = 8
        ctx.lineWidth = max(1.0, 3.5 * (1.0 - progress))
        ctx.beginPath()
        ctx.moveTo(offset_x, cy)
        ctx.lineTo(offset_x + board_w, cy)
        ctx.moveTo(cx, offset_y)
        ctx.lineTo(cx, offset_y + board_h)
        ctx.stroke()

        # Crackling electric zigzag arcs branching along row and column
        ctx.lineWidth = 1.8
        ctx.strokeStyle = '#a5f3fc'
        ctx.beginPath()
        for i in range(10):
            seg_x = offset_x + i * (board_w / 10.0)
            jit = self.jitter_offsets[i]
            if i == 0:
                ctx.moveTo(seg_x, cy + jit)
            else:
                ctx.lineTo(seg_x, cy + jit)
        ctx.stroke()

        ctx.beginPath()
        for j in range(12):
            seg_y = offset_y + j * (board_h / 12.0)
            jit = self.jitter_offsets[10 + j]
            if j == 0:
                ctx.moveTo(cx + jit, seg_y)
            else:
                ctx.lineTo(cx + jit, seg_y)
        ctx.stroke()

        # Intersection star flare
        ctx.fillStyle = '#ffffff'
        ctx.shadowColor = '#00f0f0'
        ctx.shadowBlur = 20
        flare_sz = max(4.0, 24 * (1.0 - progress))
        ctx.beginPath()
        ctx.arc(cx, cy, flare_sz, 0, math.pi * 2)
        ctx.fill()

        ctx.restore()


class FireEruptionEffect:
    """Thermite cross explosion blooming over center and orthogonal neighbor cells."""
    def __init__(self, center_x, center_y, duration=0.5):
        self.center_x = center_x
        self.center_y = center_y
        self.duration = duration
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, ctx, offset_x, offset_y):
        if not self.is_alive():
            return
        
        progress = min(1.0, self.elapsed / self.duration)
        alpha = 1.0 - progress
        ease = 1.0 - math.pow(1.0 - progress, 2)
        
        cx = offset_x + self.center_x * BLOCK_SIZE + BLOCK_SIZE / 2
        cy = offset_y + (self.center_y - HIDDEN_ROWS) * BLOCK_SIZE + BLOCK_SIZE / 2

        ctx.save()

        offsets = [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]
        for dx, dy in offsets:
            fx = cx + dx * BLOCK_SIZE * ease * 1.15
            fy = cy + dy * BLOCK_SIZE * ease * 1.15
            r = (BLOCK_SIZE * 0.85) * (1.0 - progress * 0.35)

            ctx.globalAlpha = alpha * 0.75
            ctx.fillStyle = '#ff4500'
            ctx.shadowColor = '#ff4500'
            ctx.shadowBlur = 18
            ctx.beginPath()
            ctx.arc(fx, fy, r, 0, math.pi * 2)
            ctx.fill()

            ctx.globalAlpha = alpha * 0.95
            ctx.fillStyle = '#ffeb3b'
            ctx.shadowColor = '#ffeb3b'
            ctx.shadowBlur = 8
            ctx.beginPath()
            ctx.arc(fx, fy, r * 0.5, 0, math.pi * 2)
            ctx.fill()

        ctx.restore()


class LineBreakExplosionEffect:
    """
    Cutting-edge, smooth, immersive horizontal line detonation.
    Combines an intense glowing row flash, explosive center-outward laser blade,
    pulsing plasma beam, and cutting-edge starburst flares.
    Strictly contained to the cleared row boundaries to guarantee zero overlap.
    """
    def __init__(self, row_y, mid_x, cy, board_w, duration=LINE_CLEAR_DELAY, color='#00f0f0'):
        self.row_y = row_y
        self.mid_x = mid_x
        self.cy = cy
        self.board_w = board_w
        self.duration = duration
        self.elapsed = 0.0
        self.color = color

    def update(self, dt):
        self.elapsed += dt

    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, ctx, offset_x, offset_y, is_mobile=False):
        if not self.is_alive():
            return

        progress = min(1.0, max(0.0, self.elapsed / self.duration))
        alpha = max(0.0, 1.0 - progress)

        # Ultra-smooth laser sweep from center outward to walls in the first 45% of animation
        sweep_prog = min(1.0, progress / 0.45)
        sweep_ease = 1.0 - math.pow(1.0 - sweep_prog, 4)
        half_w = (self.board_w / 2.0) * sweep_ease

        x1 = offset_x + self.mid_x - half_w
        x2 = offset_x + self.mid_x + half_w
        cy = offset_y + self.cy
        top_y = cy - (BLOCK_SIZE / 2.0)
        beam_w = max(0.0, x2 - x1)

        ctx.save()

        # 1. Intense luminous plasma cylinder fill across the row (strictly contained inside row)
        if beam_w > 0 and alpha > 0.01:
            grad = ctx.createLinearGradient(x1, top_y, x1, top_y + BLOCK_SIZE)
            grad.addColorStop(0.0, 'rgba(255, 255, 255, 0)')
            grad.addColorStop(0.2, self.color)
            grad.addColorStop(0.5, '#ffffff')
            grad.addColorStop(0.8, self.color)
            grad.addColorStop(1.0, 'rgba(255, 255, 255, 0)')

            ctx.globalAlpha = min(0.95, alpha * 1.3)
            ctx.fillStyle = grad
            ctx.fillRect(x1, top_y, beam_w, BLOCK_SIZE)

        # 2. Searing outer neon laser beam
        ctx.globalAlpha = min(1.0, alpha * 1.1)
        ctx.strokeStyle = self.color
        if not is_mobile:
            ctx.shadowColor = self.color
            ctx.shadowBlur = int(14 * alpha)
        ctx.lineWidth = max(2.0, 8.0 * (1.0 - progress))
        ctx.beginPath()
        ctx.moveTo(x1, cy)
        ctx.lineTo(x2, cy)
        ctx.stroke()

        # 3. Razor-sharp white laser core
        ctx.globalAlpha = alpha
        ctx.strokeStyle = '#ffffff'
        if not is_mobile:
            ctx.shadowColor = '#ffffff'
            ctx.shadowBlur = 8
        ctx.lineWidth = max(1.5, 3.5 * (1.0 - progress))
        ctx.beginPath()
        ctx.moveTo(x1, cy)
        ctx.lineTo(x2, cy)
        ctx.stroke()

        # 4. Energy grid discharge needles at block seams
        if beam_w > 10:
            ctx.strokeStyle = '#ffffff'
            if not is_mobile:
                ctx.shadowColor = self.color
                ctx.shadowBlur = 6
            ctx.lineWidth = 1.5
            tick_h = min(BLOCK_SIZE * 0.45, max(2.0, 10.0 * (1.0 - progress)))
            ctx.globalAlpha = alpha * 0.85
            ctx.beginPath()
            for col in range(1, 10):
                cx_col = offset_x + col * BLOCK_SIZE
                if x1 <= cx_col <= x2:
                    ctx.moveTo(cx_col, cy - tick_h)
                    ctx.lineTo(cx_col, cy + tick_h)
            ctx.stroke()

        # 5. Cutting edge diamond starburst flares & horizontal anamorphic streaks
        flare_r = max(2.5, 7.5 * (1.0 - progress))
        ctx.globalAlpha = alpha
        ctx.fillStyle = '#ffffff'
        if not is_mobile:
            ctx.shadowColor = self.color
            ctx.shadowBlur = 10
        ctx.beginPath()
        ctx.arc(x1, cy, flare_r, 0, math.pi * 2)
        ctx.arc(x2, cy, flare_r, 0, math.pi * 2)
        ctx.fill()

        # Outer flare ring
        ctx.strokeStyle = self.color
        ctx.lineWidth = 1.8
        ctx.beginPath()
        ctx.arc(x1, cy, flare_r * 1.5, 0, math.pi * 2)
        ctx.arc(x2, cy, flare_r * 1.5, 0, math.pi * 2)
        ctx.stroke()

        # Anamorphic horizontal cutting needle streaks
        streak_len = max(4.0, 14.0 * (1.0 - progress))
        ctx.strokeStyle = '#ffffff'
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.moveTo(max(offset_x, x1 - streak_len), cy)
        ctx.lineTo(x1, cy)
        ctx.moveTo(x2, cy)
        ctx.lineTo(min(offset_x + self.board_w, x2 + streak_len), cy)
        ctx.stroke()

        # 6. Wall impact vertical energy flare when wavefront strikes the matrix boundaries
        if sweep_prog >= 0.85:
            impact_prog = (sweep_prog - 0.85) / 0.15
            impact_alpha = (1.0 - progress) * impact_prog
            wall_h = min(BLOCK_SIZE * 0.48, BLOCK_SIZE * 0.48 * (1.0 - progress))
            ctx.globalAlpha = max(0.0, min(1.0, impact_alpha))
            ctx.strokeStyle = '#ffffff'
            ctx.lineWidth = 2.5
            ctx.beginPath()
            ctx.moveTo(offset_x, cy - wall_h)
            ctx.lineTo(offset_x, cy + wall_h)
            ctx.moveTo(offset_x + self.board_w, cy - wall_h)
            ctx.lineTo(offset_x + self.board_w, cy + wall_h)
            ctx.stroke()

        ctx.restore()


class FloatingBadge:
    """
    Sleek glowing cyberpunk badge announcing ability activation, impacts, or incoming powerups.
    Floats upward with bouncy pop-in and glowing capsule border.
    """
    def __init__(self, text, subtitle='', icon='⚡', x=150, y=300, color='#00f0f0', duration=1.25, is_large=False):
        self.text = text
        self.subtitle = subtitle
        self.icon = icon
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.is_large = is_large
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, ctx, offset_x, offset_y, is_mobile=False):
        if not self.is_alive():
            return
        
        progress = min(1.0, self.elapsed / self.duration)
        
        if progress < 0.15:
            scale = (progress / 0.15) * 1.18
        elif progress < 0.25:
            scale = 1.18 - ((progress - 0.15) / 0.10) * 0.18
        else:
            scale = 1.0

        if self.is_large:
            # Gentle pulsing breathing effect while active
            pulse = math.sin(self.elapsed * 8.0) * 0.05
            scale *= (1.0 + pulse)
            y_float = -progress * 26.0
            pill_w = 240.0 if is_mobile else 260.0
            pill_h = 58.0
        else:
            y_float = -progress * 42.0
            pill_w = 175.0
            pill_h = 34.0 if self.subtitle else 26.0

        if progress < 0.65:
            alpha = 1.0
        else:
            alpha = 1.0 - ((progress - 0.65) / 0.35)

        bx = offset_x + self.x
        by = offset_y + self.y + y_float

        ctx.save()
        ctx.translate(bx, by)
        ctx.scale(scale, scale)
        ctx.globalAlpha = alpha

        # Dark glowing capsule background
        ctx.fillStyle = 'rgba(4, 7, 20, 0.95)'
        if not is_mobile:
            ctx.shadowColor = self.color
            ctx.shadowBlur = int((20 if self.is_large else 14) * alpha)
        ctx.strokeStyle = self.color
        ctx.lineWidth = 2.6 if self.is_large else 1.8

        hw = pill_w / 2.0
        hh = pill_h / 2.0
        r = hh
        ctx.beginPath()
        ctx.moveTo(-hw + r, -hh)
        ctx.lineTo(hw - r, -hh)
        ctx.arc(hw - r, 0, r, -math.pi / 2, math.pi / 2)
        ctx.lineTo(-hw + r, hh)
        ctx.arc(-hw + r, 0, r, math.pi / 2, -math.pi / 2)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()

        # Text typography
        if not is_mobile:
            ctx.shadowBlur = 8 if self.is_large else 6
            ctx.shadowColor = self.color
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'

        if self.is_large:
            # Big prominent announcement in middle of screen
            # Icon on left
            icon_x = -hw + 30.0
            ctx.font = 'bold 28px sans-serif'
            ctx.fillStyle = '#ffffff'
            ctx.fillText(self.icon, icon_x, 1)

            # Text content in remaining space
            content_x = 16.0
            ctx.font = 'bold 12.5px "Neuropol", "Orbitron", sans-serif'
            ctx.fillStyle = '#ffffff'
            ctx.fillText(self.text, content_x, -8)

            if self.subtitle:
                ctx.font = 'bold 9.5px "Neuropol", "Orbitron", sans-serif'
                ctx.fillStyle = self.color
                ctx.fillText(self.subtitle, content_x, 12)
        else:
            ctx.fillStyle = '#ffffff'
            if self.subtitle:
                ctx.font = 'bold 11px "Neuropol", "Orbitron", sans-serif'
                ctx.fillText(f"{self.icon} {self.text}", 0, -5)
                ctx.font = 'bold 9px "Neuropol", "Orbitron", sans-serif'
                ctx.fillStyle = self.color
                ctx.fillText(self.subtitle, 0, 8)
            else:
                ctx.font = 'bold 12px "Neuropol", "Orbitron", sans-serif'
                ctx.fillText(f"{self.icon} {self.text}", 0, 1)

        ctx.restore()


class ScreenFlash:
    """Brief whole-matrix flash for high-impact detonations."""
    def __init__(self, color='#ffffff', initial_alpha=0.35, duration=0.12):
        self.color = color
        self.initial_alpha = initial_alpha
        self.duration = duration
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, ctx, offset_x, offset_y, w, h):
        if not self.is_alive():
            return
        progress = min(1.0, self.elapsed / self.duration)
        alpha = self.initial_alpha * (1.0 - progress)
        ctx.save()
        ctx.globalAlpha = alpha
        ctx.fillStyle = self.color
        ctx.fillRect(offset_x, offset_y, w, h)
        ctx.restore()


class CanvasRenderer:
    """
    Renders the game onto an HTML5 2D Canvas context.
    Features vibrant cyberpunk neon glow, ghost piece, high-impact power animations,
    particle bursts, ability icons, HUD, and screen shake.
    """
    def __init__(self):
        self.is_mobile = False
        self.particles = []
        self.shockwaves = []
        self.lightning_effects = []
        self.fire_eruptions = []
        self.floating_badges = []
        self.screen_flashes = []
        self.line_breaks = []
        self.screen_shake_time = 0.0
        self.shake_magnitude = 0.0

    def trigger_shake(self, magnitude=6.0, duration=0.25):
        """Applies screen shake for hard drops, powers, and explosions."""
        self.shake_magnitude = magnitude
        self.screen_shake_time = duration

    def spawn_clear_particles(self, y_row, color='#00f0f0', count=25):
        """Spawns sparks across a cleared horizontal row."""
        canvas_y = (y_row - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        for _ in range(count):
            canvas_x = random.uniform(0, BOARD_WIDTH * BLOCK_SIZE)
            self.particles.append(Particle(canvas_x, canvas_y, color, style='spark', size=random.uniform(2.0, 4.5)))

    def spawn_explosion_particles(self, center_x, center_y, color='#ff4500', count=40):
        """Spawns an explosive circular blast of sparks for bomb blocks."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        for _ in range(count):
            self.particles.append(Particle(cx, cy, color, style='spark', size=random.uniform(2.5, 5.0)))

    def trigger_line_clear_effect(self, cleared_rows, lines=1):
        """
        Dazzling, high-impact line explosion animation with outward plasma slice,
        full-row particle bursts, expanding shockwave rings, and screen shake.
        """
        board_pixel_w = BOARD_WIDTH * BLOCK_SIZE
        mid_x = board_pixel_w / 2.0

        # Dynamic aesthetic palette and impact scaling based on cleared line count
        if lines == 1:
            accent_color = '#00f0ff'
            particle_colors = ['#ffffff', '#00f0ff', '#7df9ff', '#38bdf8']
            shake_base = 5.0
            flash_alpha = 0.26
            flash_dur = 0.12
            sw_radius = 95
        elif lines == 2:
            accent_color = '#00ffcc'
            particle_colors = ['#ffffff', '#00ffcc', '#00f0ff', '#39ff14']
            shake_base = 7.5
            flash_alpha = 0.32
            flash_dur = 0.15
            sw_radius = 110
        elif lines == 3:
            accent_color = '#ff00aa'
            particle_colors = ['#ffffff', '#ff00aa', '#e056fd', '#00f0ff']
            shake_base = 10.0
            flash_alpha = 0.38
            flash_dur = 0.18
            sw_radius = 125
        else:  # lines >= 4 (TETRIS!)
            accent_color = '#ffd700'
            particle_colors = ['#ffffff', '#ffd700', '#ffaa00', '#00ffff', '#ff3366']
            shake_base = 14.0
            flash_alpha = 0.48
            flash_dur = 0.24
            sw_radius = 150

        # 1. Punchy screen shake (calibrated for mobile)
        shake_mag = shake_base if not self.is_mobile else shake_base * 0.55
        self.trigger_shake(magnitude=shake_mag, duration=0.14 + lines * 0.04)

        # 2. Energetic matrix flash
        self.screen_flashes.append(ScreenFlash(color=accent_color, initial_alpha=flash_alpha, duration=flash_dur))

        # Fallback if row indices not passed
        if not cleared_rows:
            cleared_rows = [23 - i for i in range(lines)]

        for row_y in cleared_rows:
            cy = (row_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2.0)

            # Expanding ripple shockwave ring
            self.shockwaves.append(ShockwaveEffect(
                mid_x, cy, max_radius=sw_radius, duration=0.20,
                color_outer=accent_color, color_inner='#ffffff', ring_width=3.5
            ))

            # Flashy outward laser blade explosion
            self.line_breaks.append(LineBreakExplosionEffect(
                row_y, mid_x, cy, board_pixel_w, duration=LINE_CLEAR_DELAY, color=accent_color
            ))

            # Spreading explosion particles across the ENTIRE row width
            if self.is_mobile:
                # Streamlined yet punchy for 60fps on mobile (~10-12 particles per row)
                for col in range(0, 10, 2):
                    col_x = (col + 0.5) * BLOCK_SIZE
                    dist_ratio = (col_x - mid_x) / mid_x
                    self.particles.append(Particle(
                        col_x, cy, random.choice(particle_colors),
                        vx=dist_ratio * random.uniform(3.0, 7.0) + random.uniform(-1.0, 1.0),
                        vy=random.uniform(-3.5, 3.0),
                        style='spark', size=random.uniform(2.5, 4.0), life=0.20, decay=0.06
                    ))
                # Central high-velocity ejection sparks
                for _ in range(3):
                    self.particles.append(Particle(
                        mid_x, cy, random.choice(particle_colors),
                        vx=-random.uniform(8.0, 14.0), vy=random.uniform(-1.2, 1.2),
                        style='spark', size=random.uniform(2.5, 4.0), life=0.20, decay=0.065
                    ))
                    self.particles.append(Particle(
                        mid_x, cy, random.choice(particle_colors),
                        vx=random.uniform(8.0, 14.0), vy=random.uniform(-1.2, 1.2),
                        style='spark', size=random.uniform(2.5, 4.0), life=0.20, decay=0.065
                    ))
            else:
                # Full arcade explosion for desktop (~24-28 particles per row)
                for col in range(10):
                    col_x = (col + 0.5) * BLOCK_SIZE
                    dist_ratio = (col_x - mid_x) / mid_x
                    # Spark flying outward with vertical arc
                    self.particles.append(Particle(
                        col_x, cy, random.choice(particle_colors),
                        vx=dist_ratio * random.uniform(3.5, 8.0) + random.uniform(-1.2, 1.2),
                        vy=random.uniform(-4.5, 3.5),
                        style='spark', size=random.uniform(2.5, 4.5), life=0.22, decay=0.055, gravity=0.12
                    ))
                    # Blooming flame puff near center
                    if 3 <= col <= 6:
                        self.particles.append(Particle(
                            col_x, cy, random.choice(particle_colors),
                            vx=random.uniform(-1.8, 1.8), vy=random.uniform(-2.5, 1.5),
                            style='flame', size=random.uniform(3.5, 6.0), life=0.20, decay=0.06, gravity=-0.04
                        ))
                # Fast central ejection sparks
                for _ in range(4):
                    self.particles.append(Particle(
                        mid_x, cy, '#ffffff',
                        vx=-random.uniform(9.0, 15.0), vy=random.uniform(-1.2, 1.2),
                        style='spark', size=random.uniform(2.5, 4.2), life=0.20, decay=0.065
                    ))
                    self.particles.append(Particle(
                        mid_x, cy, '#ffffff',
                        vx=random.uniform(9.0, 15.0), vy=random.uniform(-1.2, 1.2),
                        style='spark', size=random.uniform(2.5, 4.2), life=0.20, decay=0.065
                    ))

    # High-impact, pleasing power ability triggers

    def trigger_bomb_effect(self, center_x, center_y, cleared_count=9):
        """💣 Bomb Mino: Fiery expanding fireball blast, shockwave ring, embers & smoke (3-block radius)."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=14.0 if not self.is_mobile else 7.0, duration=0.45)
        self.screen_flashes.append(ScreenFlash(color='#ff4500', initial_alpha=0.35, duration=0.14))
        # 3 blocks in each direction = ~180px radius blast
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=180, duration=0.52, color_outer='#ff3700', color_inner='#ffe600', ring_width=5.5))
        
        # 1. Blooming flame particles (streamlined on mobile for smooth 60fps)
        flame_colors = ['#ffffff', '#ffeb3b', '#ff9800', '#ff5722', '#f44336']
        flame_count = 10 if self.is_mobile else 35
        for _ in range(flame_count):
            spd = random.uniform(1.8, 5.0)
            ang = random.uniform(0, math.pi * 2)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 0.5
            col = random.choice(flame_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='flame', size=random.uniform(5.0, 9.0), life=0.65, decay=0.035, gravity=-0.08))

        # 2. Fast fiery sparks (streamlined on mobile)
        spark_colors = ['#ffffff', '#ffeb3b', '#ff7043']
        spark_count = 12 if self.is_mobile else 40
        for _ in range(spark_count):
            spd = random.uniform(4.0, 9.0)
            ang = random.uniform(0, math.pi * 2)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice(spark_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='spark', size=random.uniform(2.5, 4.5), life=0.8, decay=0.03, gravity=0.18))

        # 3. Drifting smoke puffs
        smoke_count = 4 if self.is_mobile else 16
        for _ in range(smoke_count):
            spd = random.uniform(0.6, 2.0)
            ang = random.uniform(0, math.pi * 2)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 1.2
            self.particles.append(Particle(cx, cy, '#4b5563', vx=vx, vy=vy, style='smoke', size=random.uniform(8.0, 14.0), life=0.9, decay=0.025, gravity=-0.05))

        # 4. Floating badge announcement
        sub = f"-{cleared_count} BLOCKS" if cleared_count else "3-BLOCK RADIUS"
        self.floating_badges.append(FloatingBadge("MEGA DETONATION!", sub, icon='💣', x=cx, y=cy - 12, color='#ff4500'))

    def trigger_lightning_effect(self, bolt_x, bolt_y, cleared_count=19):
        """⚡ Lightning Mino: Dual cross laser, branching electric arcs, cyan sparks."""
        cx = bolt_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (bolt_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=9.0, duration=0.35)
        self.screen_flashes.append(ScreenFlash(color='#00f0f0', initial_alpha=0.32, duration=0.12))
        self.lightning_effects.append(LightningCrossEffect(bolt_x, bolt_y, duration=0.42))
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=85, duration=0.35, color_outer='#00f0f0', color_inner='#ffffff', ring_width=3.5))

        # Electric sparks sprayed along the cleared row & column
        elec_colors = ['#00f0f0', '#7df9ff', '#ffffff', '#38bdf8']
        for _ in range(30):
            # Spray along horizontal row
            rx = random.uniform(0, BOARD_WIDTH * BLOCK_SIZE)
            col = random.choice(elec_colors)
            self.particles.append(Particle(rx, cy, col, vx=random.uniform(-3, 3), vy=random.uniform(-4, 4), style='electric', size=random.uniform(2, 4), life=0.5, decay=0.04))
        for _ in range(25):
            # Spray along vertical col
            ry = random.uniform(0, BOARD_HEIGHT * BLOCK_SIZE)
            col = random.choice(elec_colors)
            self.particles.append(Particle(cx, ry, col, vx=random.uniform(-4, 4), vy=random.uniform(-3, 3), style='electric', size=random.uniform(2, 4), life=0.5, decay=0.04))

        sub = f"-{cleared_count} BLOCKS" if cleared_count else "ROW+COL CLEAR"
        self.floating_badges.append(FloatingBadge("IONIC CROSS!", sub, icon='⚡', x=cx, y=cy - 12, color='#00f0f0'))

    def trigger_magnet_effect(self, center_x, center_y, moved_count=0):
        """🧲 Magnet Mino: Concentric gravitational flux rings and suction particles."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=5.0, duration=0.25)
        # 3 concentric magnetic flux rings
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=115, duration=0.6, color_outer='#d946ef', color_inner='#a855f7', ring_width=3.5, rings_count=3))
        
        # Suction particles drawn toward magnet
        mag_colors = ['#d946ef', '#c084fc', '#38bdf8', '#ffffff']
        for _ in range(35):
            ang = random.uniform(0, math.pi * 2)
            dist = random.uniform(40, 110)
            sx = cx + math.cos(ang) * dist
            sy = cy + math.sin(ang) * dist
            spd = random.uniform(3.0, 6.0)
            vx = -math.cos(ang) * spd
            vy = -math.sin(ang) * spd
            col = random.choice(mag_colors)
            self.particles.append(Particle(sx, sy, col, vx=vx, vy=vy, style='spark', size=random.uniform(2.0, 4.0), life=0.45, decay=0.035, drag=1.02))

        sub = f"+{moved_count} CONDENSED" if moved_count > 0 else "GAPS CLOSED"
        self.floating_badges.append(FloatingBadge("GRAVITY PULL!", sub, icon='🧲', x=cx, y=cy - 12, color='#d946ef'))

    def trigger_freeze_effect(self, center_x, center_y, duration=8.0):
        """🧊 Freeze Mino: Crystalline ice nova shockwave and spinning diamond crystals."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=4.0, duration=0.2)
        self.screen_flashes.append(ScreenFlash(color='#38bdf8', initial_alpha=0.3, duration=0.15))
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=150, duration=0.55, color_outer='#38bdf8', color_inner='#e0f2fe', ring_width=4.0))

        # Diamond ice shards radiating outwards
        ice_colors = ['#ffffff', '#e0f2fe', '#a5f3fc', '#38bdf8']
        for _ in range(40):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.0, 8.0)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice(ice_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='ice', size=random.uniform(3.5, 7.0), life=0.75, decay=0.025, drag=0.96))

        self.floating_badges.append(FloatingBadge("TIME STASIS!", f"{duration:.1f}s FROZEN", icon='🧊', x=cx, y=cy - 12, color='#38bdf8'))

    def trigger_burning_placed_effect(self, center_x, center_y):
        """🔥 Burning Mino (Placed): Thermite fuse armed, rising sizzling fire & spark aura."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=50, duration=0.3, color_outer='#ff5500', color_inner='#ffcc00', ring_width=3.0))
        
        # Rising flame sparks
        flame_colors = ['#ffeb3b', '#ff7043', '#f44336']
        for _ in range(25):
            vx = random.uniform(-2.0, 2.0)
            vy = random.uniform(-4.5, -1.2)
            col = random.choice(flame_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='flame', size=random.uniform(4.0, 7.0), life=0.6, decay=0.035, gravity=-0.1))

        self.floating_badges.append(FloatingBadge("FUSE ARMED!", "3.0s COUNTDOWN", icon='🔥', x=cx, y=cy - 12, color='#ff5500'))

    def trigger_burning_exploded_effect(self, center_x, center_y, cleared_count=5):
        """🔥 Burning Mino (Detonated): Cross-flame thermite eruption & flying embers."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=11.0, duration=0.4)
        self.screen_flashes.append(ScreenFlash(color='#ff3700', initial_alpha=0.35, duration=0.12))
        self.fire_eruptions.append(FireEruptionEffect(center_x, center_y, duration=0.5))
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=105, duration=0.45, color_outer='#ff2200', color_inner='#ffe600', ring_width=4.5))

        # Flame & ember particles
        flame_colors = ['#ffeb3b', '#ff9800', '#ff5722', '#f44336']
        for _ in range(45):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(2.5, 6.5)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 0.5
            col = random.choice(flame_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='flame', size=random.uniform(5.0, 8.5), life=0.7, decay=0.03, gravity=-0.05))

        sub = f"-{cleared_count} BLOCKS" if cleared_count else "THERMITE CROSS"
        self.floating_badges.append(FloatingBadge("THERMITE BURST!", sub, icon='🔥', x=cx, y=cy - 12, color='#ff3300'))

    def trigger_heavy_landed_effect(self, center_x, center_y):
        """🪨 Heavy Mino: Seismic ground slam, dust & obsidian debris blast."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=13.0, duration=0.32)
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=90, duration=0.38, color_outer='#f59e0b', color_inner='#d97706', ring_width=5.0))

        # Heavy obsidian rock debris kicking up
        rock_colors = ['#64748b', '#475569', '#334155', '#f59e0b']
        for _ in range(35):
            vx = random.uniform(-5.0, 5.0)
            vy = random.uniform(-6.5, -2.0)
            col = random.choice(rock_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='rock', size=random.uniform(4.0, 7.5), life=0.8, decay=0.03, gravity=0.38))

        self.floating_badges.append(FloatingBadge("SEISMIC SLAM!", "DENSE OBSIDIAN", icon='🪨', x=cx, y=cy - 12, color='#f59e0b'))

    def trigger_powerup_incoming_alert(self, ability):
        """
        Displays a big, flashy, unmissable announcement in the middle of the screen
        whenever a tactical power piece is incoming.
        """
        info = ABILITY_INFO.get(ability, {})
        if not info:
            return

        icon = info.get('symbol', '⚡')
        name = info.get('name', 'POWER').upper()
        color = info.get('color', '#00f0ff')
        desc = info.get('desc', 'SPECIAL TACTICAL MINO').upper()

        mid_x = (BOARD_WIDTH * BLOCK_SIZE) / 2.0  # 150 (horizontal center of board)
        mid_y = 280  # Vertical center of visible board

        # 1. Big glowing cyberpunk alert banner in center of screen
        self.floating_badges.append(FloatingBadge(
            text=f"{name} MINO INCOMING!",
            subtitle=f"{desc}",
            icon=icon,
            x=mid_x,
            y=mid_y,
            color=color,
            duration=1.85,
            is_large=True
        ))

        # 2. Expanding radial energy shockwave ring from center
        self.shockwaves.append(ShockwaveEffect(
            x=mid_x,
            y=mid_y,
            max_radius=115,
            duration=0.48,
            color_outer=color,
            color_inner='#ffffff',
            ring_width=4.0
        ))

        # 3. Soft ambient matrix flash in the ability's signature color
        self.screen_flashes.append(ScreenFlash(
            color=color,
            initial_alpha=0.22,
            duration=0.20
        ))

        # 4. Radiant burst of energy sparks around the incoming alert
        spark_count = 8 if self.is_mobile else 18
        for _ in range(spark_count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(2.5, 6.0)
            self.particles.append(Particle(
                mid_x, mid_y, color,
                vx=math.cos(ang) * spd,
                vy=math.sin(ang) * spd,
                style='spark',
                size=random.uniform(2.5, 4.5),
                life=0.45,
                decay=0.035
            ))

    def update_particles(self, delta_time):
        """Updates physics and timers for all active particles and visual effects."""
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.is_alive()]
        if self.is_mobile and len(self.particles) > 35:
            self.particles = self.particles[-35:]

        for s in self.shockwaves:
            s.update(delta_time)
        self.shockwaves = [s for s in self.shockwaves if s.is_alive()]

        for l in self.lightning_effects:
            l.update(delta_time)
        self.lightning_effects = [l for l in self.lightning_effects if l.is_alive()]

        for f in self.fire_eruptions:
            f.update(delta_time)
        self.fire_eruptions = [f for f in self.fire_eruptions if f.is_alive()]

        for b in self.floating_badges:
            b.update(delta_time)
        self.floating_badges = [b for b in self.floating_badges if b.is_alive()]

        for sf in self.screen_flashes:
            sf.update(delta_time)
        self.screen_flashes = [sf for sf in self.screen_flashes if sf.is_alive()]

        for lb in self.line_breaks:
            lb.update(delta_time)
        self.line_breaks = [lb for lb in self.line_breaks if lb.is_alive()]

        if self.screen_shake_time > 0.0:
            self.screen_shake_time -= delta_time
            if self.screen_shake_time < 0.0:
                self.screen_shake_time = 0.0

    def render(self, ctx, game, sector_mgr=None, game_mode='CLASSIC', high_score=0):
        """
        Main drawing function called once per animation frame (60 FPS).
        Dynamically adapts between Mobile Portrait (360x720) and Desktop (750x720).
        """
        canvas_w = ctx.canvas.width if hasattr(ctx, 'canvas') and ctx.canvas else 750
        canvas_h = ctx.canvas.height if hasattr(ctx, 'canvas') and ctx.canvas else 720
        is_mobile = (canvas_w < 550)
        self.is_mobile = is_mobile

        board_pixel_w = BOARD_WIDTH * BLOCK_SIZE   # 300
        board_pixel_h = BOARD_HEIGHT * BLOCK_SIZE  # 600

        if is_mobile:
            offset_x = int((canvas_w - board_pixel_w) / 2)  # 30px on 360w
            offset_y = 78
        else:
            offset_x = 180  # Left margin for Hold piece panel on desktop
            offset_y = 60   # Top margin on desktop

        # Apply screen shake if active
        ctx.save()
        if self.screen_shake_time > 0.0:
            shake_offset_x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            shake_offset_y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            ctx.translate(shake_offset_x, shake_offset_y)

        # 1. Clear background - Fully dark
        ctx.fillStyle = '#000000'
        ctx.fillRect(0, 0, canvas_w, canvas_h)

        # 2. Draw Main Matrix Background & Grid Lines
        ctx.fillStyle = '#050505'
        ctx.fillRect(offset_x, offset_y, board_pixel_w, board_pixel_h)

        # 2.1 Draw Screen Flashes for high-impact detonations
        for sf in self.screen_flashes:
            sf.draw(ctx, offset_x, offset_y, board_pixel_w, board_pixel_h)

        # Subtle dark grid lines
        ctx.strokeStyle = '#141414'
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

        # Board border - Clean dark titanium
        ctx.strokeStyle = '#262626'
        ctx.shadowColor = 'transparent'
        ctx.shadowBlur = 0
        ctx.lineWidth = 1.5
        ctx.strokeRect(offset_x, offset_y, board_pixel_w, board_pixel_h)

        # 2.5. Alert banner if next piece is an upcoming Power Piece (Desktop only)
        if not is_mobile and len(game.next_queue) > 0 and game.next_queue[0].ability != ABILITY_NONE:
            self.draw_power_alert_banner(ctx, game.next_queue[0].ability, offset_x, offset_y - 48, board_pixel_w)

        # 3. Draw Locked Blocks on the Board
        clearing_rows = getattr(game, 'clearing_rows', [])
        clear_timer = getattr(game, 'line_clear_timer', 0.0)

        for row in range(HIDDEN_ROWS, TOTAL_HEIGHT):
            is_row_clearing = (row in clearing_rows and clear_timer > 0.0)
            for col in range(BOARD_WIDTH):
                cell = game.board[row][col]
                if cell is not None:
                    bx = offset_x + col * BLOCK_SIZE
                    by = offset_y + (row - HIDDEN_ROWS) * BLOCK_SIZE
                    burn_timer = cell.get('burn_timer')
                    if is_row_clearing:
                        self.draw_clearing_block(ctx, bx, by, cell['color'], clear_timer, LINE_CLEAR_DELAY)
                    else:
                        self.draw_neon_block(ctx, bx, by, cell['color'], cell.get('ability', ABILITY_NONE), burn_timer)

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

        # 6. Draw Visual Effects
        # 6.0 Line break outward explosion effects
        for lb in self.line_breaks:
            lb.draw(ctx, offset_x, offset_y, is_mobile=is_mobile)

        # 6.1 Lightning cross lasers and electric arcs
        for l in self.lightning_effects:
            l.draw(ctx, offset_x, offset_y)

        # 6.2 Thermite fire explosions
        for f in self.fire_eruptions:
            f.draw(ctx, offset_x, offset_y)

        # 6.3 Expanding shockwaves & magnetic pulse rings
        for s in self.shockwaves:
            s.draw(ctx, offset_x, offset_y)

        # 6.4 Enhanced physics particles (sparks, flames, ice crystals, electric arcs, rock debris)
        for p in self.particles:
            p.draw(ctx, offset_x, offset_y, is_mobile=is_mobile)

        # 6.5 Frost ambient aura while game is frozen
        if game.freeze_timer > 0.0:
            self.draw_freeze_ambient(ctx, offset_x, offset_y, board_pixel_w, board_pixel_h, game.freeze_timer)

        # 6.6 Floating combat badges (announcements floating above blocks with glowing capsule pills)
        for b in self.floating_badges:
            b.draw(ctx, offset_x, offset_y, is_mobile=is_mobile)

        # 7. UI Panels: Mobile Mode vs Desktop Side Panels
        if is_mobile:
            self.draw_mobile_top_bar(ctx, game, high_score, canvas_w, bar_h=74)
            self.draw_mobile_bottom_bar(ctx, game, sector_mgr, game_mode, canvas_w, y_start=682)
        else:
            self.draw_hold_panel(ctx, game, offset_x - 150, offset_y)
            self.draw_next_panel(ctx, game, offset_x + board_pixel_w + 30, offset_y)
            self.draw_hud(ctx, game, sector_mgr, game_mode, offset_x - 150, offset_y + 175, high_score)

        # 8. Game Over or Pause Overlay
        if game.game_over:
            sub = f"SCORE: {game.score} // BEST: {high_score}"
            if is_mobile:
                sub += " // TAP TO RESTART"
            self.draw_banner(ctx, "SYSTEM CORRUPTED", sub, '#ff0055', canvas_w, canvas_h)
        elif game.is_paused:
            sub = "TAP TO RESUME" if is_mobile else "PRESS P TO RESUME"
            self.draw_banner(ctx, "SYSTEM PAUSED", sub, '#00f0f0', canvas_w, canvas_h)

        ctx.restore()

    def draw_power_alert_banner(self, ctx, ability, bx, by, bw):
        """Draws an unmissable tactical alert warning the player about the upcoming Power Piece."""
        info = ABILITY_INFO.get(ability)
        if not info:
            return

        pulse = (math.sin(time.time() * 8.0) + 1.0) / 2.0  # Fast flashing pulse
        color = info['color']

        ctx.save()
        # Glowing dark background
        ctx.fillStyle = 'rgba(6, 10, 26, 0.95)'
        ctx.fillRect(bx, by, bw, 38)

        # Pulsating neon alert border
        ctx.strokeStyle = color
        ctx.shadowColor = color
        ctx.shadowBlur = int(10 + 10 * pulse)
        ctx.lineWidth = 2.5
        ctx.strokeRect(bx, by, bw, 38)

        # Warning text
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.font = 'bold 12px "Neuropol", "Orbitron", sans-serif'
        ctx.fillStyle = color
        symbol = info['symbol']
        name = info['name'].upper()
        ctx.fillText(f"⚡ INCOMING: [{symbol} {name}] ⚡", bx + (bw / 2), by + 19)
        ctx.restore()

    def draw_freeze_ambient(self, ctx, ox, oy, bw, bh, freeze_timer):
        """Draws an ambient pulsating frost vignette around the matrix during stasis."""
        pulse = (math.sin(time.time() * 5.0) + 1.0) / 2.0
        ctx.save()
        # Icy outer border halo
        ctx.strokeStyle = '#38bdf8'
        ctx.shadowColor = '#38bdf8'
        ctx.shadowBlur = int(12 + 10 * pulse)
        ctx.lineWidth = 2.5
        ctx.strokeRect(ox, oy, bw, bh)

        # Top and bottom subtle frost mist
        ctx.globalAlpha = 0.15 + 0.1 * pulse
        grad_top = ctx.createLinearGradient(ox, oy, ox, oy + 45)
        grad_top.addColorStop(0.0, '#38bdf8')
        grad_top.addColorStop(1.0, 'rgba(0,0,0,0)')
        ctx.fillStyle = grad_top
        ctx.fillRect(ox, oy, bw, 45)

        grad_bot = ctx.createLinearGradient(ox, oy + bh, ox, oy + bh - 45)
        grad_bot.addColorStop(0.0, '#38bdf8')
        grad_bot.addColorStop(1.0, 'rgba(0,0,0,0)')
        ctx.fillStyle = grad_bot
        ctx.fillRect(ox, oy + bh - 45, bw, 45)
        ctx.restore()

    def draw_clearing_block(self, ctx, x, y, color, timer, duration):
        """
        Renders a block that is actively being cleared during the line clear delay.
        Flashing neon energy overdrive in stage 1, then smooth crystalline dissolve in stage 2.
        """
        prog = min(1.0, max(0.0, 1.0 - (timer / max(0.001, duration))))
        ctx.save()
        if prog < 0.35:
            # Stage 1: Intense radiant overload flash (brilliant white + neon rim)
            ctx.fillStyle = '#ffffff'
            ctx.globalAlpha = 0.95
            ctx.fillRect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
            ctx.strokeStyle = color
            ctx.lineWidth = 2.5
            ctx.strokeRect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
        else:
            # Stage 2: Crystalline dissolution & lattice vaporization
            dissolve_prog = (prog - 0.35) / 0.65
            alpha = max(0.0, 1.0 - dissolve_prog)
            shrink = dissolve_prog * 4.0
            ctx.globalAlpha = alpha * 0.90
            ctx.fillStyle = '#ffffff'
            ctx.fillRect(x + 1 + shrink, y + 1 + shrink, BLOCK_SIZE - 2 - (shrink * 2), BLOCK_SIZE - 2 - (shrink * 2))
            ctx.strokeStyle = color
            ctx.lineWidth = max(1.0, 2.0 * (1.0 - dissolve_prog))
            ctx.strokeRect(x + 1 + shrink, y + 1 + shrink, BLOCK_SIZE - 2 - (shrink * 2), BLOCK_SIZE - 2 - (shrink * 2))
        ctx.restore()

    def draw_neon_block(self, ctx, x, y, color, ability=ABILITY_NONE, burn_timer=None):
        """
        Draws a block on the grid.
        Power blocks are completely unique with high-contrast energy cores and distinct glowing rings!
        On mobile, shadowBlur is bypassed to deliver 60 FPS performance.
        """
        ctx.save()

        if ability != ABILITY_NONE and ability in ABILITY_INFO:
            info = ABILITY_INFO[ability]
            ability_color = info['color']
            pulse = (math.sin(time.time() * 6.0) + 1.0) / 2.0  # 0.0 to 1.0

            # 1. Dark high-contrast energy core
            ctx.fillStyle = '#02040a'
            ctx.fillRect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)

            # 2. Glowing animated outer neon halo
            ctx.strokeStyle = ability_color
            if not self.is_mobile:
                ctx.shadowColor = ability_color
                ctx.shadowBlur = int(8 + 8 * pulse)
            ctx.lineWidth = 2.5
            ctx.strokeRect(x + 1.5, y + 1.5, BLOCK_SIZE - 3, BLOCK_SIZE - 3)

            # 3. Inner circular energy core
            cx = x + (BLOCK_SIZE / 2)
            cy = y + (BLOCK_SIZE / 2)
            ctx.beginPath()
            ctx.arc(cx, cy, (BLOCK_SIZE / 2) - 3, 0, math.pi * 2)
            ctx.fillStyle = f"rgba(255, 255, 255, {0.12 + 0.12 * pulse})"
            ctx.fill()
            ctx.strokeStyle = ability_color
            ctx.lineWidth = 1.5
            ctx.stroke()

            # 4. CRISP, 100% OPACITY, BOLD ICON
            if not self.is_mobile:
                ctx.shadowBlur = 4
                ctx.shadowColor = '#ffffff'
            ctx.font = 'bold 18px sans-serif'
            ctx.textAlign = 'center'
            ctx.textBaseline = 'middle'
            ctx.fillText(info['symbol'], cx, cy + 1)

            # 5. If burning block has active fuse, draw fuse progress indicator
            if burn_timer is not None:
                fuse_pct = max(0.0, min(1.0, burn_timer / 3.0))
                ctx.fillStyle = '#ff2200'
                ctx.fillRect(x + 3, y + BLOCK_SIZE - 5, int((BLOCK_SIZE - 6) * fuse_pct), 3)

        else:
            # Standard structural block
            ctx.fillStyle = color
            if not self.is_mobile:
                ctx.shadowColor = color
                ctx.shadowBlur = 6
            ctx.fillRect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
            if not self.is_mobile:
                ctx.shadowBlur = 0

            # Subtle inner highlight
            ctx.fillStyle = 'rgba(255, 255, 255, 0.25)'
            ctx.fillRect(x + 2, y + 2, BLOCK_SIZE - 4, 3)
            ctx.fillRect(x + 2, y + 2, 3, BLOCK_SIZE - 4)

        ctx.restore()

    def draw_ghost_block(self, ctx, x, y, color):
        """Draws a bright, prominent holographic guide representing where the piece will land."""
        ctx.save()
        # Luminous semi-transparent inner tint for high visibility
        ctx.fillStyle = color
        ctx.globalAlpha = 0.22
        ctx.fillRect(x + 2, y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4)
        # Crisp, vivid outer outline
        ctx.strokeStyle = color
        ctx.globalAlpha = 0.88
        ctx.lineWidth = 2.0
        ctx.strokeRect(x + 2, y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4)
        ctx.restore()

    def draw_hold_panel(self, ctx, game, px, py):
        """Draws the Hold Piece panel on the left."""
        ctx.save()
        ctx.fillStyle = '#080808'
        ctx.fillRect(px, py, 120, 120)
        ctx.strokeStyle = '#262626'
        ctx.lineWidth = 1.5
        ctx.strokeRect(px, py, 120, 120)

        # Label in Neuropol - Clean titanium white
        ctx.fillStyle = '#cbd5e1'
        ctx.font = 'bold 11px "Neuropol", "Orbitron", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText("HOLD [C]", px + 60, py + 20)

        if game.hold_piece:
            alpha = 1.0 if game.can_hold else 0.4
            ctx.globalAlpha = alpha
            self.draw_mini_piece(ctx, game.hold_piece, px + 25, py + 45)

        ctx.restore()

    def draw_next_panel(self, ctx, game, px, py):
        """Draws the Next Pieces preview queue on the right with power alerts."""
        ctx.save()
        panel_h = 360
        ctx.fillStyle = '#080808'
        ctx.fillRect(px, py, 130, panel_h)
        ctx.strokeStyle = '#262626'
        ctx.lineWidth = 1.5
        ctx.strokeRect(px, py, 130, panel_h)

        # Label in Neuropol - Clean titanium white
        ctx.fillStyle = '#cbd5e1'
        ctx.font = 'bold 11px "Neuropol", "Orbitron", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText("NEXT", px + 65, py + 22)

        # If the top piece in queue is a Power Piece, highlight it prominently!
        if len(game.next_queue) > 0 and game.next_queue[0].ability != ABILITY_NONE:
            info = ABILITY_INFO.get(game.next_queue[0].ability)
            if info:
                ctx.save()
                pulse = (math.sin(time.time() * 6.0) + 1.0) / 2.0
                ctx.strokeStyle = info['color']
                ctx.lineWidth = 2
                ctx.shadowColor = info['color']
                ctx.shadowBlur = int(8 + 8 * pulse)
                ctx.strokeRect(px + 8, py + 36, 114, 68)
                ctx.font = 'bold 9px "Neuropol", "Orbitron", sans-serif'
                ctx.fillStyle = info['color']
                ctx.fillText(f"⚡ {info['name'].upper()} ⚡", px + 65, py + 98)
                ctx.restore()

        # Preview next 4 pieces
        preview_y = py + 45
        for i in range(min(4, len(game.next_queue))):
            piece = game.next_queue[i]
            self.draw_mini_piece(ctx, piece, px + 30, preview_y)
            preview_y += 75

        ctx.restore()

    def draw_mini_piece(self, ctx, piece, base_x, base_y, mini_size=18):
        """Draws a scaled-down 4-block piece for Next and Hold previews with clear power icons."""
        shape_offsets = TETROMINO_SHAPES[piece.shape][0]
        has_ability = (piece.ability != ABILITY_NONE)

        for idx, (ox, oy) in enumerate(shape_offsets):
            mx = base_x + ox * mini_size
            my = base_y + oy * mini_size
            
            is_ability_block = (has_ability and idx == piece.ability_block_index)
            
            if is_ability_block:
                info = ABILITY_INFO.get(piece.ability, {})
                acolor = info.get('color', '#ff0055')
                # Completely unique mini power block
                ctx.save()
                ctx.fillStyle = '#02040a'
                ctx.fillRect(mx, my, mini_size - 1, mini_size - 1)
                ctx.strokeStyle = acolor
                ctx.shadowColor = acolor
                ctx.shadowBlur = 6
                ctx.lineWidth = 1.5
                ctx.strokeRect(mx + 0.5, my + 0.5, mini_size - 2, mini_size - 2)
                
                # Crisp bold icon
                icon_sz = 10 if mini_size < 15 else 12
                ctx.font = f'bold {icon_sz}px sans-serif'
                ctx.textAlign = 'center'
                ctx.textBaseline = 'middle'
                ctx.fillText(info.get('symbol', '⚡'), mx + mini_size / 2, my + mini_size / 2)
                ctx.restore()
            else:
                ctx.fillStyle = piece.color
                ctx.fillRect(mx, my, mini_size - 1, mini_size - 1)

    def draw_mobile_top_bar(self, ctx, game, high_score, canvas_w, bar_h=74):
        """Renders compact top bar for mobile portrait view: Hold (left), HUD (center), Next (right)."""
        ctx.save()
        # Pitch-black top header with subtle neon border line
        ctx.fillStyle = '#06070a'
        ctx.fillRect(0, 0, canvas_w, bar_h)
        ctx.strokeStyle = '#1a1f2c'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(0, bar_h)
        ctx.lineTo(canvas_w, bar_h)
        ctx.stroke()

        # 1. HOLD Box (Top-Left: x=8, y=6, w=60, h=62)
        hx, hy, hw, hh = 8, 6, 60, 62
        ctx.fillStyle = '#0c0e14'
        ctx.fillRect(hx, hy, hw, hh)
        hold_active = (game.hold_piece and game.can_hold)
        ctx.strokeStyle = '#00f0f0' if hold_active else '#252a36'
        ctx.lineWidth = 1.5
        ctx.strokeRect(hx, hy, hw, hh)

        ctx.fillStyle = '#94a3b8'
        ctx.font = 'bold 8.5px "Neuropol", "Orbitron", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText("HOLD", hx + hw / 2, hy + 13)

        if game.hold_piece:
            alpha = 1.0 if game.can_hold else 0.4
            ctx.globalAlpha = alpha
            self.draw_mini_piece(ctx, game.hold_piece, hx + 8, hy + 20, mini_size=11)
            ctx.globalAlpha = 1.0
        else:
            ctx.fillStyle = '#334155'
            ctx.font = '7.5px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText("[SWIPE ↑]", hx + hw / 2, hy + 38)

        # 2. NEXT Box (Top-Right: x=canvas_w - 68, y=6, w=60, h=62)
        nx, ny, nw, nh = canvas_w - 68, 6, 60, 62
        ctx.fillStyle = '#0c0e14'
        ctx.fillRect(nx, ny, nw, nh)

        has_power_next = (len(game.next_queue) > 0 and game.next_queue[0].ability != ABILITY_NONE)
        if has_power_next:
            info = ABILITY_INFO.get(game.next_queue[0].ability, {})
            p_color = info.get('color', '#ff0055')
            ctx.strokeStyle = p_color
            ctx.shadowColor = p_color
            ctx.shadowBlur = 8
            ctx.lineWidth = 1.5
        else:
            ctx.strokeStyle = '#252a36'
            ctx.lineWidth = 1.2
            ctx.shadowBlur = 0

        ctx.strokeRect(nx, ny, nw, nh)
        ctx.shadowBlur = 0

        ctx.fillStyle = '#94a3b8'
        ctx.font = 'bold 8.5px "Neuropol", "Orbitron", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText("NEXT", nx + nw / 2, ny + 13)

        if len(game.next_queue) > 0:
            self.draw_mini_piece(ctx, game.next_queue[0], nx + 8, ny + 20, mini_size=11)

        # 3. Center HUD: High Score, Score, Level & Lines
        mid_x = canvas_w / 2.0

        # High Score (Gold)
        ctx.textAlign = 'center'
        ctx.fillStyle = '#ffb703'
        ctx.shadowColor = '#ffb703'
        ctx.shadowBlur = 4
        ctx.font = 'bold 9px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(f"HIGH: {high_score}", mid_x, 15)
        ctx.shadowBlur = 0

        # Current Score (Large White)
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 19px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.score), mid_x, 37)

        # Level & Lines
        ctx.font = 'bold 9.5px "Neuropol", "Orbitron", sans-serif'
        ctx.fillStyle = '#00ff66'
        ctx.fillText(f"LVL {game.level}", mid_x - 34, 57)
        ctx.fillStyle = '#ffe600'
        ctx.fillText(f"LINES {game.lines_cleared}", mid_x + 34, 57)

        # Tactical Power piece upcoming banner indicator
        if has_power_next:
            info = ABILITY_INFO.get(game.next_queue[0].ability, {})
            ctx.fillStyle = info.get('color', '#ff0055')
            ctx.font = 'bold 8px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText(f"⚡ INCOMING: {info.get('name', '').upper()}", mid_x, 69)

        ctx.restore()

    def draw_mobile_bottom_bar(self, ctx, game, sector_mgr, game_mode, canvas_w, y_start=682):
        """Renders subtle status bar at the bottom of mobile screen."""
        ctx.save()
        mid_x = canvas_w / 2.0

        if game.freeze_timer > 0.0:
            ctx.fillStyle = '#38bdf8'
            ctx.font = 'bold 11px "Neuropol", "Orbitron", sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText(f"🧊 TIME STASIS: {game.freeze_timer:.1f}s", mid_x, y_start + 20)
        elif game.combo > 0:
            ctx.fillStyle = '#ff00ff'
            ctx.font = 'bold 12px "Neuropol", "Orbitron", sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText(f"⚡ COMBO x{game.combo}!", mid_x, y_start + 20)
        elif game_mode == 'ROGUE' and sector_mgr:
            sec = sector_mgr.get_current_sector()
            ctx.fillStyle = '#ff0055'
            ctx.font = 'bold 9.5px "Neuropol", "Orbitron", sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText(f"SECTOR {sec['sector']}/5", mid_x - 60, y_start + 20)

            # Progress bar
            progress = min(1.0, sector_mgr.sector_lines_cleared / max(1, sec['lines_needed']))
            ctx.fillStyle = '#161d3f'
            ctx.fillRect(mid_x - 20, y_start + 12, 80, 10)
            ctx.fillStyle = '#ff0055'
            ctx.fillRect(mid_x - 20, y_start + 12, int(80 * progress), 10)

            # Relics
            if len(sector_mgr.acquired_relics) > 0:
                relic_icons = "".join([r['icon'] for r in sector_mgr.acquired_relics])
                ctx.font = '12px sans-serif'
                ctx.fillText(relic_icons, mid_x + 95, y_start + 21)
        else:
            ctx.fillStyle = '#475569'
            ctx.font = '8.5px "Neuropol", "Orbitron", sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText("SWIPE TO PLAY // TAP TO ROTATE", mid_x, y_start + 20)

        ctx.restore()

    def draw_hud(self, ctx, game, sector_mgr, game_mode, px, py, high_score=0):
        """Draws High Score, Score, Level, Lines, Sector progress, and Active Relics."""
        ctx.save()
        ctx.textAlign = 'left'

        # High Score (Golden Cyberpunk glow)
        ctx.fillStyle = '#94a3b8'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("HIGH SCORE", px, py)
        ctx.fillStyle = '#ffb703'
        ctx.shadowColor = '#ffb703'
        ctx.shadowBlur = 8
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(high_score), px, py + 22)
        ctx.shadowBlur = 0

        # Score
        ctx.fillStyle = '#94a3b8'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("SCORE", px, py + 52)
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.score), px, py + 74)

        # Level
        ctx.fillStyle = '#94a3b8'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("LEVEL", px, py + 104)
        ctx.fillStyle = '#00ff66'
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.level), px, py + 126)

        # Lines
        ctx.fillStyle = '#94a3b8'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("LINES", px, py + 156)
        ctx.fillStyle = '#ffe600'
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.lines_cleared), px, py + 178)

        # Freeze Bar Indicator
        if game.freeze_timer > 0.0:
            ctx.fillStyle = '#87cefa'
            ctx.font = 'bold 11px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText(f"🧊 FROZEN: {game.freeze_timer:.1f}s", px, py + 206)

        # Sector Info for Rogue Mode
        if game_mode == 'ROGUE' and sector_mgr:
            sec = sector_mgr.get_current_sector()
            ctx.fillStyle = '#ff0055'
            ctx.font = 'bold 12px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText(f"SECTOR {sec['sector']}/5", px, py + 232)
            
            # Progress bar
            progress = min(1.0, sector_mgr.sector_lines_cleared / sec['lines_needed'])
            ctx.fillStyle = '#161d3f'
            ctx.fillRect(px, py + 242, 120, 8)
            ctx.fillStyle = '#ff0055'
            ctx.fillRect(px, py + 242, int(120 * progress), 8)

            # Acquired Relics icons
            if len(sector_mgr.acquired_relics) > 0:
                ctx.fillStyle = '#a0aec0'
                ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
                ctx.fillText("RELICS:", px, py + 266)
                relic_icons = " ".join([r['icon'] for r in sector_mgr.acquired_relics])
                ctx.font = '16px sans-serif'
                ctx.fillText(relic_icons, px, py + 286)

        # Combo announcement
        if game.combo > 0:
            ctx.fillStyle = '#ff00ff'
            ctx.font = 'bold 13px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText(f"⚡ COMBO x{game.combo}!", px, py + 316)

        ctx.restore()

    def draw_banner(self, ctx, title, subtitle, color, canvas_w=750, canvas_h=720):
        """Draws a centered pop-up banner for Game Over or Pause."""
        ctx.save()
        bw = min(360, canvas_w - 24)
        bh = 135
        bx = int((canvas_w - bw) / 2)
        by = int((canvas_h - bh) / 2)
        mid_x = bx + bw / 2

        ctx.fillStyle = 'rgba(6, 8, 20, 0.94)'
        ctx.fillRect(bx, by, bw, bh)
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.shadowColor = color
        ctx.shadowBlur = 15
        ctx.strokeRect(bx, by, bw, bh)

        ctx.fillStyle = color
        font_sz = 16 if canvas_w < 500 else 20
        ctx.font = f'bold {font_sz}px "Neuropol", "Orbitron", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(title, mid_x, by + 50)

        ctx.fillStyle = '#ffffff'
        sub_sz = 9.5 if canvas_w < 500 else 12
        ctx.font = f'bold {sub_sz}px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(subtitle, mid_x, by + 90)
        ctx.restore()
