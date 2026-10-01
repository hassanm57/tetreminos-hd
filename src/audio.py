# audio.py - Procedural Synthwave Web Audio Engine
# Written simply and cleanly. Generates real-time synth sounds in the browser
# without needing any external audio MP3 files or assets.

try:
    import js
    HAS_JS = True
except ImportError:
    HAS_JS = False

from config import SCALE_FREQUENCIES, ABILITY_BOMB, ABILITY_LIGHTNING, ABILITY_MAGNET, ABILITY_FREEZE, ABILITY_BURNING, ABILITY_HEAVY

class SynthwaveAudio:
    """
    Manages procedural Web Audio API synthesizers for music and sound effects.
    Gracefully disables itself when running in a desktop/offline test environment.
    """
    def __init__(self):
        self.audio_ctx = None
        self.is_muted = False
        self.has_user_interacted = False

    def init_context(self):
        """
        Initializes the browser AudioContext after user interaction
        (browsers require a user click or keypress before allowing audio).
        """
        if not HAS_JS or self.audio_ctx is not None:
            return

        try:
            AudioCtx = js.window.AudioContext or js.window.webkitAudioContext
            self.audio_ctx = AudioCtx.new()
            self.has_user_interacted = True
        except Exception as e:
            print("Web Audio not available:", e)

    def resume_if_needed(self):
        """Resumes suspended audio context if browser paused it."""
        if self.audio_ctx is not None:
            if hasattr(self.audio_ctx, 'state') and self.audio_ctx.state == 'suspended':
                self.audio_ctx.resume()

    def play_tone(self, frequency, duration, wave_type='sine', gain_level=0.1):
        """
        Plays a single synthesized tone with a smooth decay envelope.
        wave_type can be 'sine', 'square', 'sawtooth', or 'triangle'.
        """
        if not HAS_JS or self.is_muted or self.audio_ctx is None:
            return

        self.resume_if_needed()

        try:
            curr_time = self.audio_ctx.currentTime

            # Create oscillator and volume gain node
            osc = self.audio_ctx.createOscillator()
            gain = self.audio_ctx.createGain()

            osc.type = wave_type
            osc.frequency.setValueAtTime(frequency, curr_time)

            # Smooth envelope: quick attack, smooth linear decay to avoid audio clicks
            gain.gain.setValueAtTime(0.0001, curr_time)
            gain.gain.linearRampToValueAtTime(gain_level, curr_time + 0.01)
            gain.gain.exponentialRampToValueAtTime(0.0001, curr_time + duration)

            # Connect nodes: osc -> gain -> output speakers
            osc.connect(gain)
            gain.connect(self.audio_ctx.destination)

            osc.start(curr_time)
            osc.stop(curr_time + duration)
        except Exception:
            pass

    def play_chord(self, frequencies, duration, wave_type='sawtooth', gain_per_note=0.04):
        """Plays multiple notes at the same time to create a rich chord."""
        for freq in frequencies:
            self.play_tone(freq, duration, wave_type, gain_per_note)

    # Sound effects for player actions

    def play_move(self):
        """Soft short blip for moving left/right."""
        self.play_tone(587.33, 0.04, wave_type='triangle', gain_level=0.03)

    def play_rotate(self):
        """Quick rising tick for rotating pieces."""
        self.play_tone(783.99, 0.05, wave_type='sine', gain_level=0.04)

    def play_soft_drop(self):
        """Subtle low click for soft drops."""
        self.play_tone(180.0, 0.03, wave_type='sine', gain_level=0.02)

    def play_hard_drop(self):
        """
        Deep punchy 808 sub-bass kick that hits hard when dropping a piece.
        Sweeps frequency down from 130 Hz to 35 Hz.
        """
        if not HAS_JS or self.is_muted or self.audio_ctx is None:
            return

        self.resume_if_needed()

        try:
            curr_time = self.audio_ctx.currentTime
            osc = self.audio_ctx.createOscillator()
            gain = self.audio_ctx.createGain()

            osc.type = 'sine'
            osc.frequency.setValueAtTime(130.0, curr_time)
            osc.frequency.exponentialRampToValueAtTime(35.0, curr_time + 0.22)

            gain.gain.setValueAtTime(0.2, curr_time)
            gain.gain.exponentialRampToValueAtTime(0.0001, curr_time + 0.22)

            osc.connect(gain)
            gain.connect(self.audio_ctx.destination)

            osc.start(curr_time)
            osc.stop(curr_time + 0.22)
        except Exception:
            pass

    def play_line_clear(self, lines):
        """
        Plays dynamic synth chords based on how many lines were cleared:
        - 1 Line: Clean single synth note (A4)
        - 2 Lines: Harmonic dyad (A4 + E5)
        - 3 Lines: Minor triad (A4 + C5 + E5)
        - 4 Lines (TETRIS): Full 4-note chord blast (A4 + C5 + E5 + A5)
        """
        if lines == 1:
            self.play_tone(440.0, 0.2, wave_type='sawtooth', gain_level=0.08)
        elif lines == 2:
            self.play_chord([440.0, 659.25], 0.28, wave_type='sawtooth', gain_per_note=0.05)
        elif lines == 3:
            self.play_chord([440.0, 523.25, 659.25], 0.35, wave_type='sawtooth', gain_per_note=0.04)
        elif lines >= 4:
            # Tetris! Play grand resonant synth chord
            self.play_chord([220.0, 440.0, 523.25, 659.25, 880.0], 0.6, wave_type='sawtooth', gain_per_note=0.05)

    def play_ability_sfx(self, ability_type):
        """Plays custom procedural synth sounds for each tactical ability block."""
        if ability_type == ABILITY_BOMB:
            self.play_bomb_sfx()
        elif ability_type == ABILITY_LIGHTNING:
            self.play_lightning_sfx()
        elif ability_type == ABILITY_MAGNET:
            self.play_magnet_sfx()
        elif ability_type == ABILITY_FREEZE:
            self.play_freeze_sfx()
        elif ability_type == ABILITY_BURNING:
            self.play_burning_ignite_sfx()
        elif ability_type == ABILITY_HEAVY:
            self.play_heavy_sfx()

    def play_bomb_sfx(self):
        """Deep explosive rumble with sharp initial blast transient."""
        if not HAS_JS or self.is_muted or self.audio_ctx is None:
            return
        self.resume_if_needed()
        try:
            curr = self.audio_ctx.currentTime
            # 1. High transient crack
            self.play_tone(180.0, 0.08, wave_type='triangle', gain_level=0.18)
            # 2. Sub-bass downward sweep
            osc = self.audio_ctx.createOscillator()
            gain = self.audio_ctx.createGain()
            osc.type = 'sine'
            osc.frequency.setValueAtTime(120.0, curr)
            osc.frequency.exponentialRampToValueAtTime(26.0, curr + 0.45)
            gain.gain.setValueAtTime(0.3, curr)
            gain.gain.exponentialRampToValueAtTime(0.0001, curr + 0.45)
            osc.connect(gain)
            gain.connect(self.audio_ctx.destination)
            osc.start(curr)
            osc.stop(curr + 0.45)
        except Exception:
            pass

    def play_lightning_sfx(self):
        """Electric high-voltage ionization blast with dual-saw zap."""
        if not HAS_JS or self.is_muted or self.audio_ctx is None:
            return
        self.resume_if_needed()
        try:
            curr = self.audio_ctx.currentTime
            osc = self.audio_ctx.createOscillator()
            gain = self.audio_ctx.createGain()
            osc.type = 'sawtooth'
            osc.frequency.setValueAtTime(1400.0, curr)
            osc.frequency.exponentialRampToValueAtTime(180.0, curr + 0.28)
            gain.gain.setValueAtTime(0.18, curr)
            gain.gain.exponentialRampToValueAtTime(0.0001, curr + 0.28)
            osc.connect(gain)
            gain.connect(self.audio_ctx.destination)
            osc.start(curr)
            osc.stop(curr + 0.28)
            # Crackle overtone
            self.play_tone(880.0, 0.15, wave_type='square', gain_level=0.08)
        except Exception:
            pass

    def play_magnet_sfx(self):
        """Futuristic gravity flux warp with pitch sweep upward."""
        if not HAS_JS or self.is_muted or self.audio_ctx is None:
            return
        self.resume_if_needed()
        try:
            curr = self.audio_ctx.currentTime
            osc = self.audio_ctx.createOscillator()
            gain = self.audio_ctx.createGain()
            osc.type = 'triangle'
            osc.frequency.setValueAtTime(220.0, curr)
            osc.frequency.exponentialRampToValueAtTime(659.25, curr + 0.35)
            gain.gain.setValueAtTime(0.15, curr)
            gain.gain.exponentialRampToValueAtTime(0.0001, curr + 0.35)
            osc.connect(gain)
            gain.connect(self.audio_ctx.destination)
            osc.start(curr)
            osc.stop(curr + 0.35)
        except Exception:
            pass

    def play_freeze_sfx(self):
        """Glistening crystalline stasis chime chord."""
        # Arpeggiated crystal harmonic tones
        chimes = [659.25, 987.77, 1318.51, 1975.53]
        for i, freq in enumerate(chimes):
            self.play_tone(freq, 0.4 + i * 0.08, wave_type='sine', gain_level=0.06)

    def play_burning_ignite_sfx(self):
        """Sizzling thermite fuse ignition sound."""
        self.play_tone(520.0, 0.07, wave_type='square', gain_level=0.07)
        self.play_tone(840.0, 0.09, wave_type='sawtooth', gain_level=0.06)

    def play_burning_detonate_sfx(self):
        """Thermite burst detonation."""
        self.play_bomb_sfx()
        self.play_tone(440.0, 0.2, wave_type='sawtooth', gain_level=0.1)

    def play_heavy_sfx(self):
        """Massive seismic ground slam with deep industrial sub-bass impact."""
        if not HAS_JS or self.is_muted or self.audio_ctx is None:
            return
        self.resume_if_needed()
        try:
            curr = self.audio_ctx.currentTime
            # Heavy anvil thud
            self.play_tone(95.0, 0.22, wave_type='square', gain_level=0.18)
            # Seismic sub rumble
            osc = self.audio_ctx.createOscillator()
            gain = self.audio_ctx.createGain()
            osc.type = 'sine'
            osc.frequency.setValueAtTime(90.0, curr)
            osc.frequency.exponentialRampToValueAtTime(30.0, curr + 0.32)
            gain.gain.setValueAtTime(0.28, curr)
            gain.gain.exponentialRampToValueAtTime(0.0001, curr + 0.32)
            osc.connect(gain)
            gain.connect(self.audio_ctx.destination)
            osc.start(curr)
            osc.stop(curr + 0.32)
        except Exception:
            pass

    def play_power_alert(self):
        """Rising futuristic chime when a Power Piece appears."""
        self.play_tone(587.33, 0.08, wave_type='triangle', gain_level=0.06)
        self.play_tone(880.0, 0.14, wave_type='sine', gain_level=0.08)

    def play_game_over(self):
        """Descending sad synth chime."""
        notes = [440.0, 392.0, 329.63, 261.63, 220.0]
        delay = 0.0
        for n in notes:
            self.play_tone(n, 0.3, wave_type='sawtooth', gain_level=0.06)
