# renderer.py - High-DPI Cyberpunk Neon Canvas 2D Renderer
# Written straightforwardly without confusing over-abstractions.

import math
import random
import time
from config import (
    BOARD_WIDTH, BOARD_HEIGHT, HIDDEN_ROWS, TOTAL_HEIGHT,
    BLOCK_SIZE, COLORS, ABILITY_NONE, ABILITY_INFO
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

    def draw(self, ctx, offset_x, offset_y):
        if not self.is_alive():
            return
        
        px = offset_x + self.x
        py = offset_y + self.y
        alpha = max(0.0, min(1.0, self.life / self.max_life))
        
        ctx.save()
        ctx.globalAlpha = alpha

        if self.style == 'spark':
            ctx.fillStyle = self.color
            ctx.shadowColor = self.color
            ctx.shadowBlur = 8
            ctx.beginPath()
            ctx.arc(px, py, max(1.0, self.size * alpha), 0, math.pi * 2)
            ctx.fill()

        elif self.style == 'flame':
            ctx.fillStyle = self.color
            ctx.shadowColor = self.color
            ctx.shadowBlur = 14
            ctx.beginPath()
            ctx.arc(px, py, self.size, 0, math.pi * 2)
            ctx.fill()

        elif self.style == 'ice':
            ctx.translate(px, py)
            ctx.rotate(self.angle)
            ctx.fillStyle = self.color
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


class FloatingBadge:
    """
    Sleek glowing cyberpunk badge announcing ability activation and impacts.
    Floats upward with bouncy pop-in and glowing capsule border.
    """
    def __init__(self, text, subtitle='', icon='⚡', x=150, y=300, color='#00f0f0', duration=1.25):
        self.text = text
        self.subtitle = subtitle
        self.icon = icon
        self.x = x
        self.y = y
        self.color = color
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
        
        if progress < 0.15:
            scale = (progress / 0.15) * 1.18
        elif progress < 0.25:
            scale = 1.18 - ((progress - 0.15) / 0.10) * 0.18
        else:
            scale = 1.0

        y_float = -progress * 42.0

        if progress < 0.65:
            alpha = 1.0
        else:
            alpha = 1.0 - ((progress - 0.65) / 0.35)

        bx = offset_x + self.x
        by = offset_y + self.y + y_float

        pill_w = 175.0
        pill_h = 34.0 if self.subtitle else 26.0

        ctx.save()
        ctx.translate(bx, by)
        ctx.scale(scale, scale)
        ctx.globalAlpha = alpha

        # Dark glowing capsule background
        ctx.fillStyle = 'rgba(4, 7, 18, 0.94)'
        ctx.shadowColor = self.color
        ctx.shadowBlur = int(14 * alpha)
        ctx.strokeStyle = self.color
        ctx.lineWidth = 1.8

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
        ctx.shadowBlur = 6
        ctx.shadowColor = self.color
        ctx.fillStyle = '#ffffff'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'

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
        self.particles = []
        self.shockwaves = []
        self.lightning_effects = []
        self.fire_eruptions = []
        self.floating_badges = []
        self.screen_flashes = []
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

    # High-impact, pleasing power ability triggers

    def trigger_bomb_effect(self, center_x, center_y, cleared_count=9):
        """💣 Bomb Mino: Fiery expanding fireball blast, shockwave ring, embers & smoke."""
        cx = center_x * BLOCK_SIZE + (BLOCK_SIZE / 2)
        cy = (center_y - HIDDEN_ROWS) * BLOCK_SIZE + (BLOCK_SIZE / 2)
        
        self.trigger_shake(magnitude=14.0, duration=0.45)
        self.screen_flashes.append(ScreenFlash(color='#ff4500', initial_alpha=0.35, duration=0.14))
        self.shockwaves.append(ShockwaveEffect(cx, cy, max_radius=140, duration=0.5, color_outer='#ff3700', color_inner='#ffe600', ring_width=5.5))
        
        # 1. Blooming flame particles
        flame_colors = ['#ffffff', '#ffeb3b', '#ff9800', '#ff5722', '#f44336']
        for _ in range(35):
            spd = random.uniform(1.5, 4.5)
            ang = random.uniform(0, math.pi * 2)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 0.5
            col = random.choice(flame_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='flame', size=random.uniform(5.0, 9.0), life=0.65, decay=0.035, gravity=-0.08))

        # 2. Fast fiery sparks
        spark_colors = ['#ffffff', '#ffeb3b', '#ff7043']
        for _ in range(40):
            spd = random.uniform(4.0, 9.0)
            ang = random.uniform(0, math.pi * 2)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice(spark_colors)
            self.particles.append(Particle(cx, cy, col, vx=vx, vy=vy, style='spark', size=random.uniform(2.5, 4.5), life=0.8, decay=0.03, gravity=0.18))

        # 3. Drifting smoke puffs
        for _ in range(16):
            spd = random.uniform(0.6, 2.0)
            ang = random.uniform(0, math.pi * 2)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 1.2
            self.particles.append(Particle(cx, cy, '#4b5563', vx=vx, vy=vy, style='smoke', size=random.uniform(8.0, 14.0), life=0.9, decay=0.025, gravity=-0.05))

        # 4. Floating badge announcement
        sub = f"-{cleared_count} BLOCKS" if cleared_count else "3x3 CLEAR"
        self.floating_badges.append(FloatingBadge("DETONATION!", sub, icon='💣', x=cx, y=cy - 12, color='#ff4500'))

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

    def update_particles(self, delta_time):
        """Updates physics and timers for all active particles and visual effects."""
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.is_alive()]

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

        # 1. Clear background - Fully dark
        ctx.fillStyle = '#000000'
        ctx.fillRect(0, 0, 750, 720)

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

        # 2.5. Alert banner if next piece is an upcoming Power Piece!
        if len(game.next_queue) > 0 and game.next_queue[0].ability != ABILITY_NONE:
            self.draw_power_alert_banner(ctx, game.next_queue[0].ability, offset_x, offset_y - 48, board_pixel_w)

        # 3. Draw Locked Blocks on the Board
        for row in range(HIDDEN_ROWS, TOTAL_HEIGHT):
            for col in range(BOARD_WIDTH):
                cell = game.board[row][col]
                if cell is not None:
                    bx = offset_x + col * BLOCK_SIZE
                    by = offset_y + (row - HIDDEN_ROWS) * BLOCK_SIZE
                    burn_timer = cell.get('burn_timer')
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

        # 6. Draw Power Ability Visual Effects
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
            p.draw(ctx, offset_x, offset_y)

        # 6.5 Frost ambient aura while game is frozen
        if game.freeze_timer > 0.0:
            self.draw_freeze_ambient(ctx, offset_x, offset_y, board_pixel_w, board_pixel_h, game.freeze_timer)

        # 6.6 Floating combat badges (announcements floating above blocks with glowing capsule pills)
        for b in self.floating_badges:
            b.draw(ctx, offset_x, offset_y)

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

    def draw_neon_block(self, ctx, x, y, color, ability=ABILITY_NONE, burn_timer=None):
        """
        Draws a block on the grid.
        Power blocks are completely unique with high-contrast energy cores and distinct glowing rings!
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
            ctx.shadowColor = color
            ctx.shadowBlur = 6
            ctx.fillRect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)
            ctx.shadowBlur = 0

            # Subtle inner highlight
            ctx.fillStyle = 'rgba(255, 255, 255, 0.25)'
            ctx.fillRect(x + 2, y + 2, BLOCK_SIZE - 4, 3)
            ctx.fillRect(x + 2, y + 2, 3, BLOCK_SIZE - 4)

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

    def draw_mini_piece(self, ctx, piece, base_x, base_y):
        """Draws a scaled-down 4-block piece for Next and Hold previews with clear power icons."""
        mini_size = 18
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
                ctx.font = 'bold 12px sans-serif'
                ctx.textAlign = 'center'
                ctx.textBaseline = 'middle'
                ctx.fillText(info.get('symbol', '⚡'), mx + mini_size / 2, my + mini_size / 2)
                ctx.restore()
            else:
                ctx.fillStyle = piece.color
                ctx.fillRect(mx, my, mini_size - 1, mini_size - 1)

    def draw_hud(self, ctx, game, sector_mgr, game_mode, px, py):
        """Draws Score, Level, Lines, Sector progress, and Active Relics."""
        ctx.save()
        ctx.textAlign = 'left'

        # Score
        ctx.fillStyle = '#7a889b'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("SCORE", px, py)
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.score), px, py + 24)

        # Level
        ctx.fillStyle = '#7a889b'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("LEVEL", px, py + 55)
        ctx.fillStyle = '#00ff66'
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.level), px, py + 79)

        # Lines
        ctx.fillStyle = '#7a889b'
        ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText("LINES", px, py + 110)
        ctx.fillStyle = '#ffe600'
        ctx.font = 'bold 18px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(str(game.lines_cleared), px, py + 134)

        # Freeze Bar Indicator
        if game.freeze_timer > 0.0:
            ctx.fillStyle = '#87cefa'
            ctx.font = 'bold 11px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText(f"🧊 FROZEN: {game.freeze_timer:.1f}s", px, py + 165)

        # Sector Info for Rogue Mode
        if game_mode == 'ROGUE' and sector_mgr:
            sec = sector_mgr.get_current_sector()
            ctx.fillStyle = '#ff0055'
            ctx.font = 'bold 12px "Neuropol", "Orbitron", sans-serif'
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
                ctx.font = '10px "Neuropol", "Orbitron", sans-serif'
                ctx.fillText("RELICS:", px, py + 230)
                relic_icons = " ".join([r['icon'] for r in sector_mgr.acquired_relics])
                ctx.font = '16px sans-serif'
                ctx.fillText(relic_icons, px, py + 250)

        # Combo announcement
        if game.combo > 0:
            ctx.fillStyle = '#ff00ff'
            ctx.font = 'bold 13px "Neuropol", "Orbitron", sans-serif'
            ctx.fillText(f"⚡ COMBO x{game.combo}!", px, py + 285)

        ctx.restore()

    def draw_banner(self, ctx, title, subtitle, color):
        """Draws a centered pop-up banner for Game Over or Pause."""
        ctx.save()
        ctx.fillStyle = 'rgba(6, 8, 20, 0.88)'
        ctx.fillRect(140, 240, 380, 140)
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.shadowColor = color
        ctx.shadowBlur = 15
        ctx.strokeRect(140, 240, 380, 140)

        ctx.fillStyle = color
        ctx.font = 'bold 20px "Neuropol", "Orbitron", sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(title, 330, 295)

        ctx.fillStyle = '#ffffff'
        ctx.font = '12px "Neuropol", "Orbitron", sans-serif'
        ctx.fillText(subtitle, 330, 340)
        ctx.restore()
