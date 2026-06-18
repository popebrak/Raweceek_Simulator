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
    status = ""            # a human hint when audio ISN'T happening (set by backends)

    def speak(self, role, text):
        """Read one line aloud, blocking until finished. Return True if real sound was
        produced (so the caller knows the speech consumed the beat), else False."""
        return False

    def to_wav(self, role, text, path):
        """Render one line to a WAV file at `path`. Return True on success."""
        return False

    def warm_up(self):
        """Do any slow one-time setup up front (e.g. a first-run model download), with
        visible feedback, so it doesn't stall silently mid-race. No-op by default."""
        return None


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
        self.status = "" if self.available else (
            "espeak not found -- install espeak-ng for voices; running silent")

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


# --- live playback for file-based backends -------------------------------------
# espeak speaks straight to the sound card; Piper and Kokoro only make WAV bytes, so
# they need a player to be heard live. We shell out to whatever the OS already has --
# paplay/aplay on Linux, afplay on macOS, sox's `play` as a catch-all -- and detect it
# at call time so it keeps working if PATH changes (and so tests can drop a fake in).
_PLAYERS = (["paplay"], ["aplay", "-q"], ["afplay"], ["play", "-q"])


def _find_player():
    for p in _PLAYERS:
        if shutil.which(p[0]):
            return p
    return None


def _play_wav(path):
    """Play a WAV file through the system player, blocking until done. True if played."""
    player = _find_player()
    if player is None:
        return False
    subprocess.run(player + [path], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=False)
    return True


def _speak_via_wav(narrator, role, text):
    """Render one line to a temp WAV (via the narrator's own to_wav) and play it.
    The shared live-speak path for every file-based backend."""
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        return _play_wav(tmp) if narrator.to_wav(role, text, tmp) else False
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# --- Piper: fast, local, neural; a clear step up from espeak, still CPU-only ---------
# Voices are ONNX packs (an .onnx + matching .onnx.json) downloaded from the Piper
# voices repo; point PIPER_VOICE_DIR at wherever you keep them. The role->voice map is
# the same idea as espeak's: a distinct pack for Vale and for Benny.
PIPER_VOICE_DIR = os.environ.get("PIPER_VOICE_DIR") or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "voices")
PIPER_VOICE = {
    "pbp":    "en_GB-alan-medium.onnx",                  # Vale -- the lap caller
    "colour": "en_GB-northern_english_male-medium.onnx", # Benny -- the colour man
}
PIPER_DEFAULT = "en_US-ryan-high.onnx"                    # a third voice (podium, etc.)


class PiperNarrator(Narrator):
    """Shells out to the `piper` CLI, one process per line, text on stdin -> WAV.
    `available` needs both the binary AND the two booth voice files present;
    `audible` additionally needs a system player for live sound (export to WAV works
    without one). Missing pieces are explained in `status`."""

    def __init__(self, binary=None, voice_dir=None):
        self.binary = binary or shutil.which("piper")
        self.voice_dir = voice_dir or PIPER_VOICE_DIR
        booth_models = [self._model(r) for r in ("pbp", "colour")]
        have_voices = all(os.path.exists(m) for m in booth_models)
        self.available = bool(self.binary) and have_voices
        self.audible = bool(self.available and _find_player())
        if not self.binary:
            self.status = "piper not found -- `pip install piper-tts`; running silent"
        elif not have_voices:
            self.status = (f"piper is installed but no voice packs in {self.voice_dir} -- "
                           "download en_GB voices; running silent")
        elif not self.audible:
            self.status = ("piper ready but no audio player found (paplay/aplay/afplay) "
                           "-- live sound off; render_weekend_audio() still exports WAV")
        else:
            self.status = ""

    def _model(self, role):
        """Path to the ONNX voice for a role, falling back to the lap-caller's voice
        for any role without its own pack (so a podium quote still gets spoken)."""
        name = PIPER_VOICE.get(role) or PIPER_VOICE["pbp"]
        path = os.path.join(self.voice_dir, name)
        if not os.path.exists(path) and role != "pbp":
            path = os.path.join(self.voice_dir, PIPER_VOICE["pbp"])
        return path

    def command(self, role, wav_path):
        """The exact argument list run for a line -- exposed for inspection/tuning.
        (Flag spellings have shifted across piper versions; -m/-f are the stable ones.)"""
        return [self.binary or "piper", "-m", self._model(role), "-f", wav_path]

    def to_wav(self, role, text, path):
        if not self.binary or not os.path.exists(self._model(role)):
            return False
        r = subprocess.run(self.command(role, path), input=text, text=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 44

    def speak(self, role, text):
        return _speak_via_wav(self, role, text) if self.available else False


# --- Kokoro: ~82M-param neural voice; the biggest quality jump at this size ----------
# Pure-Python package (`pip install kokoro soundfile`); first run downloads the model.
# lang_code 'b' is British English, 'a' American; voices like bm_* / am_* pick the
# speaker. Output is float audio at 24 kHz, which we pack to 16-bit PCM and write out.
KOKORO_VOICE = {
    "pbp":    ("b", "bm_george"),   # Vale -- British male
    "colour": ("b", "bm_lewis"),    # Benny -- a different British male
}
KOKORO_DEFAULT = ("a", "am_michael")
KOKORO_RATE = 24000


class KokoroNarrator(Narrator):
    """Uses the `kokoro` Python package (StyleTTS2-based). Lazily builds one pipeline
    per language and caches it. `available` means the package imports; `audible` also
    needs a system player. WAV export works whenever the package is present."""

    def __init__(self):
        self._KPipeline = None
        self._pipelines = {}
        try:
            from kokoro import KPipeline
            self._KPipeline = KPipeline
            self.available = True
        except Exception:
            self.available = False
        self.audible = bool(self.available and _find_player())
        if not self.available:
            self.status = "kokoro not installed -- `pip install kokoro soundfile`; running silent"
        elif not self.audible:
            self.status = ("kokoro ready but no audio player found -- live sound off; "
                           "render_weekend_audio() still exports WAV")
        else:
            self.status = ""

    def _pipeline(self, lang):
        if lang not in self._pipelines:
            self._pipelines[lang] = self._KPipeline(lang_code=lang)
        return self._pipelines[lang]

    def warm_up(self):
        """First run pulls the ~82M-param model and each voicepack from Hugging Face.
        We do it here, before the green flag, with a clear message and one throwaway
        line per voice -- so the download (with its own progress bars) finishes up
        front instead of stalling silently on the first spoken call."""
        if not self.available:
            return
        print("  [kokoro: first run downloads the voice model (a few hundred MB) from")
        print("   Hugging Face -- this happens ONCE, then it's cached. Please wait...]")
        done = set()
        for role in ("pbp", "colour", None):       # the two booth voices + the fallback
            lang, voice = KOKORO_VOICE.get(role, KOKORO_DEFAULT)
            if voice in done:
                continue
            done.add(voice)
            try:
                list(self._pipeline(lang)("Warming up.", voice=voice))
            except Exception as e:
                print(f"  [kokoro warm-up note for {voice}: {e}]")
        print("  [kokoro: ready]")

    def _pcm(self, role, text):
        """Synthesize one line to 16-bit little-endian PCM bytes (mono, 24 kHz)."""
        lang, voice = KOKORO_VOICE.get(role, KOKORO_DEFAULT)
        out = []
        for chunk in self._pipeline(lang)(text, voice=voice):
            audio = chunk[-1]                       # (graphemes, phonemes, audio)
            if hasattr(audio, "detach"):            # torch tensor -> numpy
                audio = audio.detach().cpu().numpy()
            try:
                import numpy as np
                out.append((np.clip(np.asarray(audio, dtype="float32"), -1, 1)
                            * 32767).astype("<i2").tobytes())
            except Exception:
                import array
                out.append(array.array("h", (int(max(-1.0, min(1.0, float(s))) * 32767)
                                             for s in audio)).tobytes())
        return b"".join(out)

    def to_wav(self, role, text, path):
        if not self.available:
            return False
        try:
            pcm = self._pcm(role, text)
        except Exception:
            return False
        if not pcm:
            return False
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(KOKORO_RATE)
            w.writeframes(pcm)
        return True

    def speak(self, role, text):
        return _speak_via_wav(self, role, text) if self.available else False


def make_narrator(kind="espeak"):
    """Build a narrator by name: 'espeak', 'piper', and 'kokoro' are the real voices;
    'silent' forces no audio; 'capture' is the record-only export head. The real
    backends all degrade gracefully on their own (speak/to_wav return False when not
    set up), so we hand the real object back even when it isn't ready -- it carries a
    `status` explaining why, and the engine treats a silent line exactly as before."""
    if kind in (None, "none", "silent"):
        return SilentNarrator()
    if kind == "capture":
        return CaptureNarrator()
    if kind == "espeak":
        return EspeakNarrator()
    if kind == "piper":
        return PiperNarrator()
    if kind == "kokoro":
        return KokoroNarrator()
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
