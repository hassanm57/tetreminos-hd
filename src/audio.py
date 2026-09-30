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
            # Deep rumbling explosion (sweeps down to 25 Hz)
            self.play_tone(90.0, 0.45, wave_type='triangle', gain_level=0.25)
        elif ability_type == ABILITY_LIGHTNING:
            # Electric high-voltage zap
            self.play_tone(1100.0, 0.2, wave_type='sawtooth', gain_level=0.1)
        elif ability_type == ABILITY_MAGNET:
            # Smooth magnetic sweep upward
            self.play_tone(329.63, 0.3, wave_type='sine', gain_level=0.08)
        elif ability_type == ABILITY_FREEZE:
            # Crystalline chime chord
            self.play_chord([587.33, 880.0, 1174.66], 0.5, wave_type='sine', gain_per_note=0.05)
        elif ability_type == ABILITY_BURNING:
            # Crackling warning tick
            self.play_tone(350.0, 0.08, wave_type='square', gain_level=0.05)
        elif ability_type == ABILITY_HEAVY:
            # Heavy metallic thud
            self.play_tone(110.0, 0.18, wave_type='square', gain_level=0.12)

    def play_game_over(self):
        """Descending sad synth chime."""
        notes = [440.0, 392.0, 329.63, 261.63, 220.0]
        delay = 0.0
        for n in notes:
            self.play_tone(n, 0.3, wave_type='sawtooth', gain_level=0.06)
