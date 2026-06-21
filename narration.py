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
import re
import shutil
import subprocess
import tempfile
import wave

from drivers import GRID


# --- casting the podium ------------------------------------------------------
# In the post-race show the booth tags every driver's answer with that driver's
# NAME as the role (not "pbp"). There are twenty of them, so rather than a clip
# each, every driver is cast -- by gender, read from the grid -- into one of a few
# same-gender voices. The assignment is stable per name (a name always maps to the
# same slot), so whoever reaches the podium speaks in a consistent, gender-correct
# voice. Suze, the pit reporter, is the role "report" and has her own voice.
_DRIVER_GENDER = {d.name: getattr(d, "gender", "m") for d in GRID}


def _build_driver_slots(n):
    """Assign each driver a 0..n-1 voice slot, round-robin within their gender in grid
    order -- so the n same-gender voices get used EVENLY (not clumped, as a hash would),
    and a given driver always lands on the same slot."""
    slots, seen = {}, {}
    for d in GRID:
        g = getattr(d, "gender", "m")
        i = seen.get(g, 0)
        slots[d.name] = i % n
        seen[g] = i + 1
    return slots


_DRIVER_SLOTS = _build_driver_slots(3)       # three voices per gender


def _is_driver(role):
    """True if this role is a driver speaking (a podium quote), not a booth voice."""
    return role in _DRIVER_GENDER


def _cast_driver(name, pools, default):
    """Pick a voice for a driver from a {'m': [...], 'f': [...]} map of same-gender
    voices, by their grid gender and their fixed, evenly-spread slot. Falls back to
    `default` if that gender's pool is empty."""
    pool = pools.get(_DRIVER_GENDER.get(name, "m")) or []
    if not pool:
        return default
    return pool[_DRIVER_SLOTS.get(name, 0) % len(pool)]


# Per-role espeak settings, tuned for contrast inside espeak's narrow range. `voice`
# is an espeak voice + variant (en-gb male variants m1..m7); speed is words/min;
# pitch and amplitude are 0-99 / 0-200. Roles other than the booth voices (a driver's
# podium quote) are cast by gender from ESPEAK_DRIVER, falling back to DEFAULT_VOICE.
ESPEAK_VOICE = {
    "pbp":    {"voice": "en-gb+m3", "speed": 178, "pitch": 64, "amplitude": 135},
    "colour": {"voice": "en-gb+m5", "speed": 150, "pitch": 32, "amplitude": 120},
    "report": {"voice": "en-gb+f3", "speed": 170, "pitch": 58, "amplitude": 130},  # Suze, the pit-lane reporter -- a third, distinct voice
}
DEFAULT_VOICE = {"voice": "en-gb+m2", "speed": 165, "pitch": 50, "amplitude": 125}

# Podium voices, by gender -- three each, free (espeak's own variants, no files). A
# driver is cast into one of their gender's three, stable per name.
ESPEAK_DRIVER = {
    "m": [{"voice": "en-gb+m1", "speed": 168, "pitch": 46, "amplitude": 128},
          {"voice": "en-gb+m4", "speed": 160, "pitch": 54, "amplitude": 128},
          {"voice": "en-gb+m6", "speed": 172, "pitch": 40, "amplitude": 128}],
    "f": [{"voice": "en-gb+f1", "speed": 168, "pitch": 60, "amplitude": 128},
          {"voice": "en-gb+f2", "speed": 162, "pitch": 66, "amplitude": 128},
          {"voice": "en-gb+f4", "speed": 174, "pitch": 54, "amplitude": 128}],
}

ESPEAK_BIN = shutil.which("espeak-ng") or shutil.which("espeak")


# Paralinguistic performance tags. Chatterbox Turbo acts on these (it'll actually
# laugh, sigh, etc.); every other engine -- espeak, Piper, Kokoro, and even Chatterbox
# Original -- would read them out as literal words, so those strip them before synthesis
# (see Narrator._voiceable). The tags stay in the on-screen feed as stage directions; we
# only clean them off the audio path. Keep this list to the tags Turbo recognises.
PARALINGUISTIC_TAGS = ("laugh", "sigh", "chuckle", "cough",
                       "gasp", "groan", "sniff", "shush", "clear throat")
_TAG_RE = re.compile(r"\[(?:" + "|".join(PARALINGUISTIC_TAGS) + r")\]", re.IGNORECASE)


def strip_tags(text):
    """Remove paralinguistic tags from a line and tidy the whitespace/punctuation they
    leave behind, so a stripped line reads as clean prose ('...well. [sigh]' -> '...well.')."""
    out = _TAG_RE.sub("", text)
    out = re.sub(r"\s+([,.!?;:])", r"\1", out)   # close up a space left before punctuation
    out = re.sub(r"\s{2,}", " ", out)            # collapse any doubled spaces
    return out.strip()


class Narrator:
    """The interface the engine talks to. A backend need only implement speak() (play
    aloud, blocking until done) and to_wav() (render one line to a WAV file).

    `audible`  -- can this narrator actually make live sound? When False, the caller
                  keeps its own visual pacing (the old time.sleep beats); when True,
                  the spoken line IS the pacing, so the race runs at talking speed.
    `capture`  -- is this a record-only narrator (no live sound, no screen)? Used by
                  the audio-export path so it can replay the race silently and collect
                  the script without spamming the terminal.
    `keeps_tags` -- does this engine ACT on paralinguistic tags like [sigh]/[laugh]?
                  Only Chatterbox Turbo does. Everything else strips them before
                  synthesis (via _voiceable) so they aren't read aloud literally. The
                  tags always remain in the on-screen feed as stage directions -- the
                  stripping happens only on the audio path.
    """
    audible = False
    capture = False
    keeps_tags = False
    status = ""            # a human hint when audio ISN'T happening (set by backends)

    def _voiceable(self, text):
        """The text actually handed to the synth: paralinguistic tags are kept only by
        an engine that understands them, otherwise stripped so they aren't spoken."""
        return text if self.keeps_tags else strip_tags(text)

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
        """The -v/-s/-p/-a flags for a role -- a booth voice, a podium driver cast
        by gender (ESPEAK_DRIVER), or the plain default."""
        v = (ESPEAK_VOICE.get(role)
             or (_cast_driver(role, ESPEAK_DRIVER, DEFAULT_VOICE)
                 if _is_driver(role) else DEFAULT_VOICE))
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
        subprocess.run(self.command(role), input=self._voiceable(text), text=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True

    def to_wav(self, role, text, path):
        if not self.available:
            return False
        r = subprocess.run(self.command(role, wav_path=path), input=self._voiceable(text), text=True,
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
# the same idea as espeak's: a distinct pack for Phill and for Benny.
PIPER_VOICE_DIR = os.environ.get("PIPER_VOICE_DIR") or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "voices")
PIPER_VOICE = {
    "pbp":    "en_GB-alan-medium.onnx",                  # Phill -- the lap caller
    "colour": "en_GB-northern_english_male-medium.onnx", # Benny -- the colour man
    "report": "en_US-ryan-high.onnx",                    # Suze -- the pit-lane reporter (the third voice in voices/README)
}
PIPER_DEFAULT = "en_US-ryan-high.onnx"                    # a third voice (podium, etc.)

# Podium voices by gender. Piper needs a file per voice, so these are OPTIONAL: drop
# the packs in to use them; any that are missing fall back to PIPER_DEFAULT, so the
# drivers still get a non-Phill voice even with no extra packs installed.
PIPER_DRIVER = {
    "m": ["en_US-ryan-high.onnx", "en_GB-alan-low.onnx", "en_US-joe-medium.onnx"],
    "f": ["en_US-amy-medium.onnx", "en_GB-jenny_dioco-medium.onnx", "en_US-kristin-medium.onnx"],
}


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
        """Path to the ONNX voice for a role. Booth roles map directly; a podium driver
        is cast by gender (PIPER_DRIVER); anything else, or any missing non-booth pack,
        falls back to PIPER_DEFAULT -- the podium voice, NOT Phill, so a driver never
        ends up sounding like the lap caller (which was the old bug)."""
        if role in PIPER_VOICE:
            name = PIPER_VOICE[role]
        elif _is_driver(role):
            name = _cast_driver(role, PIPER_DRIVER, PIPER_DEFAULT)
        else:
            name = PIPER_DEFAULT
        path = os.path.join(self.voice_dir, name)
        if not os.path.exists(path) and role not in ("pbp", "colour"):
            path = os.path.join(self.voice_dir, PIPER_DEFAULT)
        return path

    def command(self, role, wav_path):
        """The exact argument list run for a line -- exposed for inspection/tuning.
        (Flag spellings have shifted across piper versions; -m/-f are the stable ones.)"""
        return [self.binary or "piper", "-m", self._model(role), "-f", wav_path]

    def to_wav(self, role, text, path):
        if not self.binary or not os.path.exists(self._model(role)):
            return False
        r = subprocess.run(self.command(role, path), input=self._voiceable(text), text=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 44

    def speak(self, role, text):
        return _speak_via_wav(self, role, text) if self.available else False


# --- Kokoro: ~82M-param neural voice; the biggest quality jump at this size ----------
# Pure-Python package (`pip install kokoro soundfile`); first run downloads the model.
# lang_code 'b' is British English, 'a' American; voices like bm_* / am_* pick the
# speaker. Output is float audio at 24 kHz, which we pack to 16-bit PCM and write out.
KOKORO_VOICE = {
    "pbp":    ("b", "bm_george"),   # Phill -- British male
    "colour": ("b", "bm_lewis"),    # Benny -- a different British male
}
KOKORO_DEFAULT = ("a", "am_michael")
KOKORO_RATE = 24000

# Podium voices by gender (free -- Kokoro's own speakers, no files needed).
KOKORO_DRIVER = {
    "m": [("a", "am_michael"), ("a", "am_adam"), ("b", "bm_daniel")],
    "f": [("b", "bf_emma"), ("a", "af_heart"), ("a", "af_bella")],
}


def _kokoro_voice(role):
    """(lang, voice) for a role -- a booth voice, a podium driver cast by gender, or
    the default. Keeps drivers off the booth voices and gives them their own."""
    if role in KOKORO_VOICE:
        return KOKORO_VOICE[role]
    if _is_driver(role):
        return _cast_driver(role, KOKORO_DRIVER, KOKORO_DEFAULT)
    return KOKORO_DEFAULT


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
        lang, voice = _kokoro_voice(role)
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
            pcm = self._pcm(role, self._voiceable(text))
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


def _tensor_to_pcm16(x):
    """Convert a torch tensor / numpy array / nested list of float samples (mono, in
    [-1, 1]) to 16-bit little-endian PCM bytes, flattening to mono. The lingua franca
    for getting model audio into a stdlib WAV without a torchaudio dependency."""
    try:
        if hasattr(x, "detach"):                 # torch tensor -> numpy
            x = x.detach().cpu().numpy()
        import numpy as np
        a = np.asarray(x, dtype="float32").reshape(-1)
        return (np.clip(a, -1, 1) * 32767).astype("<i2").tobytes()
    except Exception:
        try:
            import array
            flat = []
            for v in x:
                try:
                    flat.extend(v)
                except TypeError:
                    flat.append(v)
            return array.array("h", (int(max(-1.0, min(1.0, float(s))) * 32767)
                                     for s in flat)).tobytes()
        except Exception:
            return b""


# --- Chatterbox: Resemble AI's expressive, voice-cloning model -- the quality tier ----
# Needs a CUDA GPU (it runs on CPU but painfully slowly). `pip install chatterbox-tts`,
# and use Python 3.10 -- it's the version with prebuilt wheels for all the deps. The
# "turbo" variant (~350M, ~4.5 GB VRAM) fits a 6 GB card; "original" (~500M) wants
# ~6-7 GB. Voices come from short reference clips: drop a clean ~10-30 s WAV per role
# in CHATTERBOX_REF_DIR and Phill/Benny become those voices; with no clip, the model's
# built-in default voice is used (so both would sound alike). `exaggeration` dials
# expressiveness: 0 flat, ~1 natural, >1 animated.
CHATTERBOX_REF_DIR = os.environ.get("CHATTERBOX_REF_DIR") or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs")
CHATTERBOX_VARIANT = (os.environ.get("CHATTERBOX_VARIANT") or "turbo").lower()
CHATTERBOX_VOICE = {
    "pbp":    {"ref": "phill.wav",  "exaggeration": 1.15},   # Phill -- a touch animated
    "colour": {"ref": "benny.wav", "exaggeration": 0.7},    # Benny -- dry and level
    "report": {"ref": "suze.wav",  "exaggeration": 0.9},    # Suze -- the pit-lane reporter
}
# Podium voices, by gender: three each. A driver is cast into one of their gender's
# three (stable per name), so whoever reaches the podium speaks in a consistent,
# gender-correct voice instead of all twenty collapsing to the model default. Drop the
# six clips in refs/ (driver_m1..3.wav, driver_f1..3.wav); any missing clip falls back
# to the model's built-in voice for that line.
CHATTERBOX_DRIVER = {
    "m": [{"ref": "driver_m1.wav", "exaggeration": 0.9},
          {"ref": "driver_m2.wav", "exaggeration": 0.9},
          {"ref": "driver_m3.wav", "exaggeration": 0.9}],
    "f": [{"ref": "driver_f1.wav", "exaggeration": 0.9},
          {"ref": "driver_f2.wav", "exaggeration": 0.9},
          {"ref": "driver_f3.wav", "exaggeration": 0.9}],
}
CHATTERBOX_DEFAULT = {"ref": None, "exaggeration": 1.0}


class ChatterboxNarrator(Narrator):
    """Loads a Chatterbox model once (in warm_up) and reuses it. `available` means the
    package and torch import; `device` is cuda when a GPU is present, else cpu (with a
    warning, since CPU is far too slow for a live race -- export to WAV instead).
    Distinct voices come from per-role reference clips in CHATTERBOX_REF_DIR."""

    def __init__(self, ref_dir=None, variant=None):
        self.ref_dir = ref_dir or CHATTERBOX_REF_DIR
        self.variant = (variant or CHATTERBOX_VARIANT)
        # Only Turbo understands paralinguistic tags; Original would read them aloud, so
        # it strips them like the other engines do.
        self.keeps_tags = (self.variant != "original")
        self._cls = None
        self._model = None
        self.device = "cpu"
        self.available = False
        try:
            import torch
            if self.variant == "original":
                from chatterbox.tts import ChatterboxTTS as C
            else:
                from chatterbox.tts_turbo import ChatterboxTurboTTS as C
            self._cls = C
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.available = True
        except Exception:
            self.available = False
        self.audible = bool(self.available and self.device == "cuda" and _find_player())
        if not self.available:
            self.status = ("chatterbox not installed -- `pip install chatterbox-tts` "
                           "(Python 3.10 + CUDA torch); running silent")
        elif self.device == "cpu":
            self.status = ("chatterbox found but no CUDA GPU -- CPU is too slow for a "
                           "live race; use render_weekend_audio() to export a WAV")
        elif not _find_player():
            self.status = ("chatterbox ready but no audio player found -- live sound "
                           "off; render_weekend_audio() still exports WAV")
        else:
            self.status = ""

    def _ensure_model(self):
        if self._model is None:
            self._neutralise_watermarker()
            self._model = self._cls.from_pretrained(device=self.device)
        return self._model

    @staticmethod
    def _neutralise_watermarker():
        """Chatterbox calls `perth.PerthImplicitWatermarker()` while loading the model.
        That watermarker is a fragile optional dependency: if perth's own internal
        import fails it silently becomes None, and constructing it then takes the whole
        load down with 'NoneType' object is not callable. The watermark is just an
        inaudible provenance stamp we don't need for local playback, so when it's
        unavailable we slot in a no-op and let the model load regardless. (No effect on
        the other backends -- this only runs on the chatterbox load path.)"""
        try:
            import perth
        except Exception:
            return                                  # perth absent entirely -- let load proceed/fail as it would
        if getattr(perth, "PerthImplicitWatermarker", None) is None:
            class _NoWatermark:
                def apply_watermark(self, wav, *args, **kwargs):
                    return wav                      # return the audio untouched
                def get_watermark(self, *args, **kwargs):
                    return 0.0                      # "no watermark present"
            perth.PerthImplicitWatermarker = _NoWatermark

    def warm_up(self):
        """First run downloads the model (~1 GB) and loads it onto the GPU; both take a
        moment. Do it up front so it doesn't stall on the first spoken line."""
        if not self.available:
            return
        print(f"  [chatterbox ({self.variant}): first run downloads the model (~1 GB) and")
        print(f"   loads it onto the {self.device.upper()} -- this can take a minute...]")
        try:
            self._ensure_model()
        except Exception as e:
            print(f"  [chatterbox load failed: {e}]")
            self.available = self.audible = False
            return
        print("  [chatterbox: ready]")

    def _cfg(self, role):
        """Voice config for a role: a booth voice, Suze ('report'), a podium driver
        cast by gender (CHATTERBOX_DRIVER), or the built-in default."""
        if role in CHATTERBOX_VOICE:
            return CHATTERBOX_VOICE[role]
        if _is_driver(role):
            return _cast_driver(role, CHATTERBOX_DRIVER, CHATTERBOX_DEFAULT)
        return CHATTERBOX_DEFAULT

    def _ref(self, role):
        """The reference-clip path for a role, or None (built-in voice) if there's no
        configured clip or the file is missing."""
        name = self._cfg(role).get("ref")
        if not name:
            return None
        path = os.path.join(self.ref_dir, name)
        return path if os.path.exists(path) else None

    def to_wav(self, role, text, path):
        if not self.available:
            return False
        try:
            model = self._ensure_model()
        except Exception:
            return False
        cfg = self._cfg(role)
        kwargs = {}
        ref = self._ref(role)
        if ref:
            kwargs["audio_prompt_path"] = ref
        # exaggeration only does anything on the Original variant. Turbo doesn't
        # support it -- it accepts the kwarg but ignores it and logs a warning on every
        # line -- so we simply don't pass it there.
        if self.variant == "original":
            kwargs["exaggeration"] = cfg.get("exaggeration", 1.0)
        spoken = self._voiceable(text)   # Turbo keeps [sigh]/[laugh]; Original strips them
        try:
            try:
                wav = model.generate(spoken, **kwargs)
            except TypeError:
                kwargs.pop("exaggeration", None)   # a build that rejects it outright
                wav = model.generate(spoken, **kwargs)
        except Exception:
            return False
        pcm = _tensor_to_pcm16(wav)
        if not pcm:
            return False
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(int(getattr(model, "sr", 24000)))
            w.writeframes(pcm)
        return True

    def speak(self, role, text):
        return _speak_via_wav(self, role, text) if self.available else False


def make_narrator(kind="espeak", variant=None):
    """Build a narrator by name: 'espeak', 'piper', 'kokoro', and 'chatterbox' are the
    real voices;
    'silent' forces no audio; 'capture' is the record-only export head. The real
    backends all degrade gracefully on their own (speak/to_wav return False when not
    set up), so we hand the real object back even when it isn't ready -- it carries a
    `status` explaining why, and the engine treats a silent line exactly as before.

    `variant` only applies to chatterbox: 'turbo' or 'original'. None lets the engine
    pick its own default (the CHATTERBOX_VARIANT env var, which is Turbo unless set)."""
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
    if kind == "chatterbox":
        return ChatterboxNarrator(variant=variant)
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
