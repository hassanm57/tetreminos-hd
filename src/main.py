# main.py - Main entry point and browser game loop coordinator
# Written in clean, readable Python for PyScript / Pyodide WebAssembly execution.

import time
import math
from config import (
    ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE,
    ABILITY_BURNING, ABILITY_HEAVY,
    DAS_DELAY, ARR_RATE, SOFT_DROP_SPEED
)
from engine import TetrisGame
from audio import SynthwaveAudio
from renderer import CanvasRenderer, FloatingBadge
from roguelike import SectorManager

try:
    import js
    from pyodide.ffi import create_proxy
    HAS_BROWSER_ENV = True
except ImportError:
    HAS_BROWSER_ENV = False

class GameApp:
    """
    Main application coordinator.
    Connects HTML5 Canvas, Keyboard Events, Web Audio, and the Game Engine.
    """
    def __init__(self):
        self.game_mode = 'ROGUE'  # 'CLASSIC' or 'ROGUE'
        self.game = TetrisGame(enable_abilities=(self.game_mode == 'ROGUE'))
        self.sector_mgr = SectorManager() if self.game_mode == 'ROGUE' else None
        self.audio = SynthwaveAudio()
        self.renderer = CanvasRenderer()
        
        # Snappy key hold state (DAS & ARR)
        self.left_held = False
        self.right_held = False
        self.down_held = False
        self.hold_timer = 0.0
        self.repeat_timer = 0.0
        self.down_timer = 0.0

        # Mode Selection Modal state
        self.selected_modal_mode = self.game_mode

        self.last_frame_time = time.time()
        self.canvas = None
        self.ctx = None

    def start(self):
        """Initializes canvas and attaches browser event listeners."""
        if not HAS_BROWSER_ENV:
            print("Running in desktop test mode (no browser environment).")
            return

        self.canvas = js.document.getElementById("gameCanvas")
        self.ctx = self.canvas.getContext("2d")

        # Set canvas internal resolution to 750x720
        self.canvas.width = 750
        self.canvas.height = 720

        # Bind keyboard events
        keydown_proxy = create_proxy(self.on_keydown)
        js.window.addEventListener("keydown", keydown_proxy)
        keyup_proxy = create_proxy(self.on_keyup)
        js.window.addEventListener("keyup", keyup_proxy)

        # Bind touch/mouse UI button events
        self.setup_ui_buttons()
        self.setup_touch_controls()
        self.update_mode_ui_elements()

        # Start 60 FPS animation loop
        self.last_frame_time = time.time()
        loop_proxy = create_proxy(self.game_loop)
        js.window.requestAnimationFrame(loop_proxy)

    def on_keydown(self, event):
        """Handles player keyboard controls."""
        # Initialize Web Audio on first user interaction
        self.audio.init_context()

        key = event.key

        # If relic drafting is active in Rogue Mode, numbers 1, 2, 3 pick relics
        if self.sector_mgr and self.sector_mgr.is_drafting:
            if key in ['1', '2', '3']:
                idx = int(key) - 1
                if idx < len(self.sector_mgr.offered_relics):
                    chosen = self.sector_mgr.offered_relics[idx]
                    self.sector_mgr.select_relic(chosen['id'])
                    self.update_relic_modal_ui()
            return

        # Restart game if game over
        if self.game.game_over:
            if key.lower() == 'r':
                self.restart_game()
            return

        # Movement with snappy in-engine DAS hold
        if key in ["ArrowLeft", "a", "A"]:
            event.preventDefault()
            if not self.left_held:
                self.left_held = True
                self.right_held = False
                self.hold_timer = 0.0
                self.repeat_timer = 0.0
                self.game.move_left()
        elif key in ["ArrowRight", "d", "D"]:
            event.preventDefault()
            if not self.right_held:
                self.right_held = True
                self.left_held = False
                self.hold_timer = 0.0
                self.repeat_timer = 0.0
                self.game.move_right()
        elif key in ["ArrowUp", "w", "W", "x", "X"]:
            event.preventDefault()
            self.game.rotate(clockwise=True)
        elif key in ["z", "Z", "Control"]:
            event.preventDefault()
            self.game.rotate(clockwise=False)
        elif key in ["ArrowDown", "s", "S"]:
            event.preventDefault()
            if not self.down_held:
                self.down_held = True
                self.down_timer = 0.0
                self.game.soft_drop()
                self.audio.play_soft_drop()
        elif key == " ":
            event.preventDefault()
            self.game.hard_drop()
        elif key in ["c", "C", "Shift"]:
            event.preventDefault()
            self.game.hold()
        elif key in ['?', '/']:
            event.preventDefault()
            controls_modal = js.document.getElementById("controlsModal")
            if controls_modal and controls_modal.style.display == "flex":
                self.close_controls_modal()
            else:
                self.open_controls_modal()
        elif key in ["p", "P", "Escape"]:
            event.preventDefault()
            controls_modal = js.document.getElementById("controlsModal")
            mode_modal = js.document.getElementById("modeModal")
            if controls_modal and controls_modal.style.display == "flex":
                self.close_controls_modal()
            elif mode_modal and mode_modal.style.display == "flex":
                self.close_mode_modal()
            else:
                self.game.is_paused = not self.game.is_paused

    def on_keyup(self, event):
        """Releases held keys to stop auto-repeat immediately."""
        key = event.key
        if key in ["ArrowLeft", "a", "A"]:
            self.left_held = False
            self.hold_timer = 0.0
            self.repeat_timer = 0.0
        elif key in ["ArrowRight", "d", "D"]:
            self.right_held = False
            self.hold_timer = 0.0
            self.repeat_timer = 0.0
        elif key in ["ArrowDown", "s", "S"]:
            self.down_held = False
            self.down_timer = 0.0

    def setup_ui_buttons(self):
        """Attaches click listeners to header buttons, drawers, and modals."""
        button_actions = {
            "btn-controls": lambda: self.open_controls_modal(),
            "btn-controls-close": lambda: self.close_controls_modal(),
            "btn-toggle-drawer": lambda: self.toggle_power_drawer(),
            "btn-restart": lambda: self.restart_game(),
            "btn-mode": lambda: self.open_mode_modal(),
            "card-rogue": lambda: self.select_modal_mode('ROGUE'),
            "card-classic": lambda: self.select_modal_mode('CLASSIC'),
            "btn-mode-deploy": lambda: self.deploy_selected_mode(),
            "btn-mode-cancel": lambda: self.close_mode_modal()
        }

        for btn_id, action in button_actions.items():
            btn = js.document.getElementById(btn_id)
            if btn:
                def make_handler(act):
                    def handler(evt):
                        evt.preventDefault()
                        self.audio.init_context()
                        act()
                    return handler
                proxy = create_proxy(make_handler(action))
                btn.addEventListener("click", proxy)

    def setup_touch_controls(self):
        """Attaches low-latency touch and pointer listeners for mobile controls and canvas gestures."""
        if not HAS_BROWSER_ENV:
            return

        # 1. Left button (move left + DAS hold)
        btn_left = js.document.getElementById("touch-left")
        if btn_left:
            def on_left_start(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                self.left_held = True
                self.right_held = False
                self.hold_timer = 0.0
                self.repeat_timer = 0.0
                self.game.move_left()
                self.vibrate(12)

            def on_left_end(evt):
                evt.preventDefault()
                self.left_held = False
                self.hold_timer = 0.0
                self.repeat_timer = 0.0

            btn_left.addEventListener("touchstart", create_proxy(on_left_start))
            btn_left.addEventListener("touchend", create_proxy(on_left_end))
            btn_left.addEventListener("touchcancel", create_proxy(on_left_end))
            btn_left.addEventListener("mousedown", create_proxy(on_left_start))
            btn_left.addEventListener("mouseup", create_proxy(on_left_end))
            btn_left.addEventListener("mouseleave", create_proxy(on_left_end))

        # 2. Right button (move right + DAS hold)
        btn_right = js.document.getElementById("touch-right")
        if btn_right:
            def on_right_start(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                self.right_held = True
                self.left_held = False
                self.hold_timer = 0.0
                self.repeat_timer = 0.0
                self.game.move_right()
                self.vibrate(12)

            def on_right_end(evt):
                evt.preventDefault()
                self.right_held = False
                self.hold_timer = 0.0
                self.repeat_timer = 0.0

            btn_right.addEventListener("touchstart", create_proxy(on_right_start))
            btn_right.addEventListener("touchend", create_proxy(on_right_end))
            btn_right.addEventListener("touchcancel", create_proxy(on_right_end))
            btn_right.addEventListener("mousedown", create_proxy(on_right_start))
            btn_right.addEventListener("mouseup", create_proxy(on_right_end))
            btn_right.addEventListener("mouseleave", create_proxy(on_right_end))

        # 3. Soft drop (move down + continuous drop)
        btn_down = js.document.getElementById("touch-down")
        if btn_down:
            def on_down_start(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                self.down_held = True
                self.down_timer = 0.0
                self.game.soft_drop()
                self.audio.play_soft_drop()
                self.vibrate(10)

            def on_down_end(evt):
                evt.preventDefault()
                self.down_held = False
                self.down_timer = 0.0

            btn_down.addEventListener("touchstart", create_proxy(on_down_start))
            btn_down.addEventListener("touchend", create_proxy(on_down_end))
            btn_down.addEventListener("touchcancel", create_proxy(on_down_end))
            btn_down.addEventListener("mousedown", create_proxy(on_down_start))
            btn_down.addEventListener("mouseup", create_proxy(on_down_end))
            btn_down.addEventListener("mouseleave", create_proxy(on_down_end))

        # 4. Rotate Clockwise (CW)
        btn_cw = js.document.getElementById("touch-rot-cw")
        if btn_cw:
            def on_cw_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                self.game.rotate(clockwise=True)
                self.vibrate(15)

            btn_cw.addEventListener("touchstart", create_proxy(on_cw_press))
            btn_cw.addEventListener("mousedown", create_proxy(on_cw_press))

        # 5. Rotate Counter-Clockwise (CCW)
        btn_ccw = js.document.getElementById("touch-rot-ccw")
        if btn_ccw:
            def on_ccw_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                self.game.rotate(clockwise=False)
                self.vibrate(15)

            btn_ccw.addEventListener("touchstart", create_proxy(on_ccw_press))
            btn_ccw.addEventListener("mousedown", create_proxy(on_ccw_press))

        # 6. Hard Drop / Slam
        btn_slam = js.document.getElementById("touch-hard-drop")
        if btn_slam:
            def on_slam_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                self.game.hard_drop()
                self.vibrate(25)

            btn_slam.addEventListener("touchstart", create_proxy(on_slam_press))
            btn_slam.addEventListener("mousedown", create_proxy(on_slam_press))

        # 7. Hold Piece
        btn_hold = js.document.getElementById("touch-hold")
        if btn_hold:
            def on_hold_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                self.game.hold()
                self.vibrate(15)

            btn_hold.addEventListener("touchstart", create_proxy(on_hold_press))
            btn_hold.addEventListener("click", create_proxy(on_hold_press))

        # 8. Pause / Resume
        btn_pause = js.document.getElementById("touch-pause")
        if btn_pause:
            def on_pause_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                self.game.is_paused = not self.game.is_paused

            btn_pause.addEventListener("touchstart", create_proxy(on_pause_press))
            btn_pause.addEventListener("click", create_proxy(on_pause_press))

        # 9. Power Arsenal Drawer
        btn_intel = js.document.getElementById("touch-intel")
        if btn_intel:
            def on_intel_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                self.toggle_power_drawer()

            btn_intel.addEventListener("touchstart", create_proxy(on_intel_press))
            btn_intel.addEventListener("click", create_proxy(on_intel_press))

        # 10. Reboot
        btn_restart = js.document.getElementById("touch-restart")
        if btn_restart:
            def on_restart_press(evt):
                evt.preventDefault()
                self.audio.init_context()
                self.restart_game()

            btn_restart.addEventListener("touchstart", create_proxy(on_restart_press))
            btn_restart.addEventListener("click", create_proxy(on_restart_press))

        # 11. Canvas Direct Touch Gestures
        if self.canvas:
            self.touch_start_x = 0
            self.touch_start_y = 0
            self.touch_last_x = 0
            self.touch_last_y = 0
            self.touch_start_time = 0

            def on_canvas_touchstart(evt):
                evt.preventDefault()
                self.audio.init_context()
                if self.game.game_over:
                    self.restart_game()
                    return
                touch = evt.touches[0]
                self.touch_start_x = touch.clientX
                self.touch_start_y = touch.clientY
                self.touch_last_x = touch.clientX
                self.touch_last_y = touch.clientY
                self.touch_start_time = time.time()

            def on_canvas_touchmove(evt):
                evt.preventDefault()
                if len(evt.touches) == 0:
                    return
                touch = evt.touches[0]
                dx = touch.clientX - self.touch_last_x
                dy = touch.clientY - self.touch_last_y

                # Horizontal cell shift
                if abs(dx) >= 26:
                    if dx > 0:
                        self.game.move_right()
                    else:
                        self.game.move_left()
                    self.touch_last_x = touch.clientX
                    self.vibrate(8)

                # Vertical drag down for soft drop
                if dy >= 26:
                    self.game.soft_drop()
                    self.audio.play_soft_drop()
                    self.touch_last_y = touch.clientY

            def on_canvas_touchend(evt):
                evt.preventDefault()
                dt = time.time() - self.touch_start_time
                total_dx = self.touch_last_x - self.touch_start_x
                total_dy = self.touch_last_y - self.touch_start_y

                # Quick tap on board -> Rotate CW
                if abs(total_dx) < 18 and abs(total_dy) < 18 and dt < 0.25:
                    self.game.rotate(clockwise=True)
                    self.vibrate(12)
                # Swipe Up -> Hold
                elif total_dy < -40 and dt < 0.35:
                    self.game.hold()
                    self.vibrate(15)
                # Fast Flick Down -> Hard Drop
                elif total_dy > 70 and dt < 0.22:
                    self.game.hard_drop()
                    self.vibrate(25)

            self.canvas.addEventListener("touchstart", create_proxy(on_canvas_touchstart))
            self.canvas.addEventListener("touchmove", create_proxy(on_canvas_touchmove))
            self.canvas.addEventListener("touchend", create_proxy(on_canvas_touchend))
            self.canvas.addEventListener("touchcancel", create_proxy(on_canvas_touchend))

    def vibrate(self, duration_ms):
        """Haptic feedback on mobile if device supports it."""
        try:
            if hasattr(js.window.navigator, 'vibrate'):
                js.window.navigator.vibrate(duration_ms)
        except Exception:
            pass

    def open_controls_modal(self):
        """Opens the Operational Controls modal and pauses gameplay."""
        modal = js.document.getElementById("controlsModal")
        if modal:
            self.game.is_paused = True
            modal.style.display = "flex"

    def close_controls_modal(self):
        """Closes the Operational Controls modal and resumes gameplay."""
        modal = js.document.getElementById("controlsModal")
        if modal:
            modal.style.display = "none"
            self.game.is_paused = False

    def toggle_power_drawer(self):
        """Expands or collapses the right-side tactical power drawer."""
        drawer = js.document.getElementById("powerDrawer")
        if drawer:
            if drawer.classList.contains("collapsed"):
                drawer.classList.remove("collapsed")
            else:
                drawer.classList.add("collapsed")

    def open_mode_modal(self):
        """Opens the Mode Selection Modal and pauses gameplay."""
        modal = js.document.getElementById("modeModal")
        if modal:
            self.game.is_paused = True
            self.selected_modal_mode = self.game_mode
            self.update_mode_modal_selection()
            modal.style.display = "flex"

    def close_mode_modal(self):
        """Closes the Mode Selection Modal without changing mode."""
        modal = js.document.getElementById("modeModal")
        if modal:
            modal.style.display = "none"
            self.game.is_paused = False

    def select_modal_mode(self, mode):
        """Highlights the selected mode card inside the modal."""
        self.selected_modal_mode = mode
        self.update_mode_modal_selection()

    def update_mode_modal_selection(self):
        """Updates CSS classes on the mode cards in the modal."""
        card_rogue = js.document.getElementById("card-rogue")
        card_classic = js.document.getElementById("card-classic")
        if card_rogue and card_classic:
            if self.selected_modal_mode == 'ROGUE':
                card_rogue.classList.add("active")
                card_classic.classList.remove("active")
            else:
                card_classic.classList.add("active")
                card_rogue.classList.remove("active")

    def deploy_selected_mode(self):
        """Confirms the selected mode, updates button label, and restarts run."""
        mode_btn = js.document.getElementById("btn-mode")
        if self.selected_modal_mode != self.game_mode:
            self.game_mode = self.selected_modal_mode
            if self.game_mode == 'ROGUE':
                self.sector_mgr = SectorManager()
                if mode_btn:
                    mode_btn.innerText = "MODE: ROGUE"
            else:
                self.sector_mgr = None
                if mode_btn:
                    mode_btn.innerText = "MODE: CLASSIC"
            self.restart_game()
        
        modal = js.document.getElementById("modeModal")
        if modal:
            modal.style.display = "none"
        self.game.is_paused = False

    def restart_game(self):
        """Reboots the game state."""
        # Pure classic mode has zero powerups (pure Guideline Tetris)
        enable_abilities = (self.game_mode == 'ROGUE')
        self.game = TetrisGame(enable_abilities=enable_abilities)
        if self.game_mode == 'ROGUE':
            self.sector_mgr = SectorManager()
        else:
            self.sector_mgr = None

        self.left_held = False
        self.right_held = False
        self.down_held = False
        self.hold_timer = 0.0
        self.repeat_timer = 0.0
        self.down_timer = 0.0
        self.update_relic_modal_ui()
        self.update_mode_ui_elements()

    def update_mode_ui_elements(self):
        """Hides tactical power drawer and arsenal buttons in Classic mode for a pure distraction-free experience."""
        if not HAS_BROWSER_ENV:
            return
        power_drawer = js.document.getElementById("powerDrawer")
        touch_intel = js.document.getElementById("touch-intel")
        if self.game_mode == 'CLASSIC':
            if power_drawer:
                power_drawer.style.display = "none"
            if touch_intel:
                touch_intel.style.display = "none"
        else:
            if power_drawer:
                power_drawer.style.display = "flex"
            if touch_intel:
                touch_intel.style.display = "flex"

    def process_events(self):
        """Consumes pending game events and triggers audio and visual effects."""
        events = list(self.game.pending_events)
        self.game.pending_events.clear()

        for ev in events:
            etype = ev.get('type')
            if etype == 'move':
                self.audio.play_move()
            elif etype == 'rotate':
                self.audio.play_rotate()
            elif etype == 'hard_drop':
                self.audio.play_hard_drop()
                self.renderer.trigger_shake(magnitude=5.0, duration=0.2)
                
                # Check for Graviton Condenser relic in Rogue mode
                if self.sector_mgr and self.sector_mgr.has_relic('GRAVITON_CONDENSER'):
                    # Pull down blocks under gaps
                    for col in range(10):
                        for row in range(23, 4, -1):
                            if self.game.board[row][col] is None and self.game.board[row-1][col] is not None:
                                self.game.board[row][col] = self.game.board[row-1][col]
                                self.game.board[row-1][col] = None

            elif etype == 'line_clear':
                lines = ev.get('lines', 1)
                self.audio.play_line_clear(lines)
                self.renderer.trigger_shake(magnitude=lines * 3.0, duration=0.25)
                
                # Spawn spark particles
                for row_idx in range(lines):
                    self.renderer.spawn_clear_particles(23 - row_idx, color='#00f0f0', count=25)

                # Juicy badge for Tetris (4-line clear)
                if lines >= 4:
                    self.renderer.floating_badges.append(FloatingBadge("TETRIS!", "4-LINE CLEAR", icon='⚡', x=150, y=300, color='#00f0f0'))

                # Combo announcement badge
                combo_val = ev.get('combo', 0)
                if combo_val > 1:
                    self.renderer.floating_badges.append(FloatingBadge(f"COMBO x{combo_val}!", "+SCORE MULTIPLIER", icon='🔥', x=150, y=260, color='#ff00ff'))

                # Check Rogue Mode progression
                if self.sector_mgr:
                    if self.sector_mgr.has_relic('RESONANCE_CASCADE') and ev.get('combo', 0) > 0:
                        self.game.score += 200 * ev['combo'] * self.game.level

                    draft_opened = self.sector_mgr.add_lines(lines)
                    if draft_opened:
                        self.update_relic_modal_ui()

            elif etype == 'ability_bomb':
                self.audio.play_ability_sfx(ABILITY_BOMB)
                bx, by = ev.get('x', 5), ev.get('y', 15)
                cleared_count = len(ev.get('cleared', []))
                self.renderer.trigger_bomb_effect(bx, by, cleared_count)

            elif etype == 'ability_lightning':
                self.audio.play_ability_sfx(ABILITY_LIGHTNING)
                lx, ly = ev.get('x', 5), ev.get('y', 15)
                cleared_count = len(ev.get('cleared', []))
                self.renderer.trigger_lightning_effect(lx, ly, cleared_count)
                if self.sector_mgr and self.sector_mgr.has_relic('SUPERCONDUCTOR'):
                    self.game.score += 1000

            elif etype == 'ability_magnet':
                self.audio.play_ability_sfx(ABILITY_MAGNET)
                mx, my = ev.get('x', 5), ev.get('y', 15)
                moved = ev.get('moved', 0)
                self.renderer.trigger_magnet_effect(mx, my, moved)
                if self.sector_mgr and self.sector_mgr.has_relic('FLUX_CAPACITOR'):
                    self.game.score += moved * 200

            elif etype == 'ability_freeze':
                self.audio.play_ability_sfx(ABILITY_FREEZE)
                fx, fy = ev.get('x', 5), ev.get('y', 15)
                duration = ev.get('duration', 8.0)
                if self.sector_mgr and self.sector_mgr.has_relic('CHRONO_OVERCLOCK'):
                    self.game.freeze_timer = 14.0
                    duration = 14.0
                self.renderer.trigger_freeze_effect(fx, fy, duration)

            elif etype == 'ability_burning_placed':
                self.audio.play_burning_ignite_sfx()
                bx, by = ev.get('x', 5), ev.get('y', 15)
                self.renderer.trigger_burning_placed_effect(bx, by)

            elif etype == 'ability_burning_exploded':
                self.audio.play_burning_detonate_sfx()
                bx, by = ev.get('x', 5), ev.get('y', 15)
                cleared_count = len(ev.get('cleared', []))
                self.renderer.trigger_burning_exploded_effect(bx, by, cleared_count)

            elif etype == 'ability_heavy_landed':
                self.audio.play_heavy_sfx()
                hx, hy = ev.get('x', 5), ev.get('y', 15)
                self.renderer.trigger_heavy_landed_effect(hx, hy)

            elif etype == 'power_spawn':
                self.audio.play_power_alert()

            elif etype == 'game_over':
                self.audio.play_game_over()

    def update_relic_modal_ui(self):
        """Displays or hides the 3-relic draft screen in HTML."""
        modal = js.document.getElementById("relicModal")
        cards_container = js.document.getElementById("relicCards")
        if not modal or not cards_container:
            return

        if self.sector_mgr and self.sector_mgr.is_drafting:
            modal.style.display = "flex"
            cards_container.innerHTML = ""

            for i, relic in enumerate(self.sector_mgr.offered_relics):
                card = js.document.createElement("div")
                card.className = "relic-card"
                card.innerHTML = f"""
                    <div class="relic-icon">{relic['icon']}</div>
                    <div class="relic-title">{relic['name']}</div>
                    <div class="relic-rarity">{relic['rarity']}</div>
                    <div class="relic-desc">{relic['desc']}</div>
                    <button class="relic-btn">SELECT [{i+1}]</button>
                """
                
                def make_pick(rid):
                    def pick_handler(evt):
                        self.sector_mgr.select_relic(rid)
                        self.update_relic_modal_ui()
                    return pick_handler

                pick_proxy = create_proxy(make_pick(relic['id']))
                card.addEventListener("click", pick_proxy)
                cards_container.appendChild(card)
        else:
            modal.style.display = "none"

    def game_loop(self, timestamp):
        """Main 60 FPS animation frame."""
        now = time.time()
        delta_time = min(0.1, now - self.last_frame_time)
        self.last_frame_time = now

        # Only update game physics if not drafting relics
        if not (self.sector_mgr and self.sector_mgr.is_drafting):
            # Snappy in-engine DAS (Delayed Auto Shift) and ARR (Auto Repeat Rate)
            if not self.game.game_over and not self.game.is_paused:
                if self.left_held or self.right_held:
                    self.hold_timer += delta_time
                    if self.hold_timer >= DAS_DELAY:
                        self.repeat_timer += delta_time
                        if self.repeat_timer >= ARR_RATE:
                            self.repeat_timer = 0.0
                            if self.left_held:
                                self.game.move_left()
                            elif self.right_held:
                                self.game.move_right()

                if self.down_held:
                    self.down_timer += delta_time
                    if self.down_timer >= SOFT_DROP_SPEED:
                        self.down_timer = 0.0
                        self.game.soft_drop()
                        self.audio.play_soft_drop()

            self.game.update(delta_time)
            self.process_events()

        self.renderer.update_particles(delta_time)
        self.renderer.render(self.ctx, self.game, self.sector_mgr, self.game_mode)

        # Request next frame
        loop_proxy = create_proxy(self.game_loop)
        js.window.requestAnimationFrame(loop_proxy)


# Start the application when script is loaded by PyScript / Pyodide
app = GameApp()
app.start()
