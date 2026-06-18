"""Narration -- the optional spoken-voice layer (text-to-speech).

The commentary was built for this from the very start: every line is already a
(role, text) pair of clean, numberless prose, so giving it a voice is only a matter
of mapping each role to a synthesized speaker and reading the line aloud.

The synth sits behind a small Narrator interface, so the race engine never needs to
know WHICH text-to-speech is in use. The first backend shells out to espeak / espeak-ng
-- a robotic but instant, offline, no-cost voice present on most Linux/macOS systems
(`sudo apt install espeak-ng`, or `brew install espeak`). Swapping in a neural voice
later (Piper, a cloud API) means writing one more Narrator subclass and changing
nothing in the race or the booth.

Two personas, two voices: VALE the lap-caller sits a touch higher and quicker (the
excitable one); BENNY the colour man sits lower and slower (the dry one). The contrast
is about all espeak can give us, but it's enough to tell them apart. Anyone else who
speaks -- a driver on the podium -- gets a third, plainer voice.

Beyond live playback, the module can render a whole race's commentary to a single WAV
file (render_script_to_wav), which is how you'd export "the Belgian Grand Prix" as
audio -- and how this is tested where no speakers (or no espeak) exist.
"""

import os
import shutil
import subprocess
import tempfile
import wave


# Per-role espeak settings, tuned for contrast inside espeak's narrow range. `voice`
# is an espeak voice + variant (en-gb male variants m1..m7); speed is words/min;
# pitch and amplitude are 0-99 / 0-200. Roles other than the two booth voices (e.g. a
# driver's podium quote) fall back to DEFAULT_VOICE.
ESPEAK_VOICE = {
    "pbp":    {"voice": "en-gb+m3", "speed": 178, "pitch": 64, "amplitude": 135},
    "colour": {"voice": "en-gb+m5", "speed": 150, "pitch": 32, "amplitude": 120},
}
DEFAULT_VOICE = {"voice": "en-gb+m2", "speed": 165, "pitch": 50, "amplitude": 125}

ESPEAK_BIN = shutil.which("espeak-ng") or shutil.which("espeak")


class Narrator:
    """The interface the engine talks to. A backend need only implement speak() (play
    aloud, blocking until done) and to_wav() (render one line to a WAV file).

    `audible`  -- can this narrator actually make live sound? When False, the caller
                  keeps its own visual pacing (the old time.sleep beats); when True,
                  the spoken line IS the pacing, so the race runs at talking speed.
    `capture`  -- is this a record-only narrator (no live sound, no screen)? Used by
                  the audio-export path so it can replay the race silently and collect
                  the script without spamming the terminal.
    """
    audible = False
    capture = False

    def speak(self, role, text):
        """Read one line aloud, blocking until finished. Return True if real sound was
        produced (so the caller knows the speech consumed the beat), else False."""
        return False

    def to_wav(self, role, text, path):
        """Render one line to a WAV file at `path`. Return True on success."""
        return False


class SilentNarrator(Narrator):
    """A no-op narrator. Used when no synth is available, so everything runs exactly
    as it did before TTS existed -- the engine never has to special-case 'no audio'."""
    audible = False

    def speak(self, role, text):
        return False

    def to_wav(self, role, text, path):
        return False


class CaptureNarrator(Narrator):
    """Record-only: speaks nothing, draws nothing, just collects every (role, text)
    line in order. The audio-export path replays a whole weekend through one of these
    to gather the script, then hands that script to render_script_to_wav."""
    audible = False
    capture = True

    def __init__(self):
        self.script = []        # the (role, text) lines, in the order they were said

    def speak(self, role, text):
        self.script.append((role, text))
        return False            # nothing was voiced live, so the caller keeps its pacing

    def to_wav(self, role, text, path):
        return False


class EspeakNarrator(Narrator):
    """The real voice. Shells out to espeak / espeak-ng -- one process per line, text
    fed on stdin (so quotes and apostrophes in 'de Beauvoir's' never need escaping).
    `available` is False if no espeak binary was found, which lets make_narrator fall
    back to silence cleanly."""

    def __init__(self, binary=ESPEAK_BIN):
        self.binary = binary
        self.available = binary is not None
        self.audible = self.available

    def _opts(self, role):
        """The -v/-s/-p/-a flags for a role (booth voice, or the plain default)."""
        v = ESPEAK_VOICE.get(role, DEFAULT_VOICE)
        return ["-v", v["voice"], "-s", str(v["speed"]),
                "-p", str(v["pitch"]), "-a", str(v["amplitude"])]

    def command(self, role, wav_path=None):
        """The exact argument list this narrator would run for a line -- exposed so it
        can be printed/inspected without speaking (handy when espeak isn't installed
        here but you want to see what WILL run on your machine)."""
        cmd = [self.binary or "espeak-ng"] + self._opts(role)
        if wav_path is not None:
            cmd += ["-w", wav_path]
        return cmd

    def speak(self, role, text):
        if not self.available:
            return False
        # input= feeds the line on stdin; espeak speaks it and the call blocks until
        # the audio has finished, which is what paces a live race at talking speed.
        subprocess.run(self.command(role), input=text, text=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True

    def to_wav(self, role, text, path):
        if not self.available:
            return False
        r = subprocess.run(self.command(role, wav_path=path), input=text, text=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return r.returncode == 0 and os.path.exists(path)


def make_narrator(kind="espeak"):
    """Build a narrator by name. 'espeak' is the real voice, falling back to silence
    if no binary is installed (so callers can always just narrate and let this sort
    out the rest); 'silent' forces no audio; 'capture' is the record-only export head."""
    if kind in (None, "none", "silent"):
        return SilentNarrator()
    if kind == "capture":
        return CaptureNarrator()
    if kind == "espeak":
        n = EspeakNarrator()
        return n if n.available else SilentNarrator()
    raise ValueError(f"unknown narrator: {kind!r}")


def render_script_to_wav(narrator, script, path, gap=0.35):
    """Render a list of (role, text) lines to ONE WAV file, with a short silence
    between lines. Returns True on success. The per-line clips come from the
    narrator's to_wav; this just stitches them (same format throughout) and inserts
    the gaps -- the basis of exporting a whole race as a single audio file."""
    frames, params = [], None
    for role, text in script:
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            if narrator.to_wav(role, text, tmp) and os.path.getsize(tmp) > 44:
                with wave.open(tmp, "rb") as w:
                    if params is None:
                        params = w.getparams()
                    frames.append(w.readframes(w.getnframes()))
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    if params is None:
        return False
    quiet = b"\x00" * int(params.framerate * params.sampwidth * params.nchannels * gap)
    with wave.open(path, "wb") as out:
        out.setparams(params)
        for i, fr in enumerate(frames):
            out.writeframes(fr)
            if i != len(frames) - 1:
                out.writeframes(quiet)
    return True
