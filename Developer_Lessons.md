# Developer Lessons — RaWeCeEk Simulator

*A personal learning companion. Not the README, not for the repo.*

The README answers **"how do I run this?"** This document answers **"why is each
piece built the way it is, and what did I actually learn doing it?"** It's organised
so you can come back in six months, having forgotten everything, and rebuild your
understanding from the concepts up. Commands are included throughout as worked
examples, but the point of each section is the *idea* behind the command.

---

## 0. What this project actually is

A terminal Formula 1 race-weekend simulator where the grid is 20 radical political
philosophers across 10 teams, racing on real circuits, with a two-person commentary
booth that calls the race — optionally out loud, in synthesised voices.

It has **two honest purposes that pull in the same direction:**

1. **A structured Python learning exercise** — "by the most absurd means possible."
2. **An entertainment / audio product** — the synthesised commentary is the payoff.

Keeping both purposes in view explains a lot of the design choices below. When a
decision had to be made, "which option teaches me more?" and "which option sounds
better in the listener's ears?" were both legitimate tie-breakers.

---

## 1. The single most important idea: layered responsibility

Everything in the codebase obeys one rule, and internalising this rule is worth more
than any individual command in this document:

> **The engine reasons. The data describes. The display speaks. The narration gives
> it a voice.**

Each layer is only allowed to do its own job, and information flows in one direction.
Concretely:

| Layer | File(s) | Its job | What it is *not* allowed to do |
|---|---|---|---|
| **Engine** | `simulation.py` | Decide what *happens* — quali, the race loop, tyre wear, strategy, crashes, DNFs | Decide what's *interesting* or how to phrase anything |
| **Data** | `drivers.py`, `tracks.py`, `weather.py` | Describe the world (the grid, the circuits, conditions) | Contain behaviour or opinions |
| **Director** | `director.py` | Decide what's *worth saying* and *when* — salience, pacing, memory, arcs | Choose the actual words |
| **Booth** | `colour.py`, `lore.py` | Choose the *words* — Phill & Benny, the banter, the shows, the lines | Decide what happened or what matters |
| **Display** | `display.py` | Put it on screen — standings board, commentary feed, telemetry | Generate any content |
| **Narration** | `narration.py` | Turn the words into sound | Generate any content |

**Why this matters as a lesson:** every time you're tempted to let one layer reach
into another's job — to let the engine emit a nicely-worded sentence, or the booth
decide a pass was important — you create a knot that's painful to untangle later. The
discipline of "engine reasons, data describes, display speaks" is *separation of
concerns*, and this project is a long, concrete demonstration of why it pays off. The
clearest example is the director/booth split: deciding a retirement deserves airtime
(a **narrative judgement**, director's job) is a genuinely different question from
deciding how Phill phrases it (a **wording judgement**, booth's job). Splitting them
meant either could be rewritten without touching the other.

### The director/booth split, in detail

- The **director** owns the `RaceMemory` and the story **arcs**. It gathers every
  event in a lap, scores them all on one *salience* scale, always voices the
  mandatory tier (a retirement, the lead change, contact, a stewards' verdict, an
  undercut, a real weather shift) and lets everything else compete for the lap's
  **airtime budget**. It hands back ordered "Beats" — biggest story first.
- The **booth** receives those Beats and turns them into Phill-and-Benny banter. A
  single "Bit" can be a whole exchange (Phill calls it, Benny reacts). On quiet laps
  the booth runs an ongoing **discussion** a beat at a time, so a topic unfolds
  across the green-flag spell instead of a one-liner being fired and forgotten — and
  that discussion *pauses* when racing interrupts and *resumes* afterwards.
- `RaceMemory` survives the race and feeds the **post-race debrief**, so the debrief
  is the *payoff* of the arcs tracked live, not a fresh summary.

### The non-negotiable rule: TTS-readiness

The spoken stream **never contains engineering jargon or numbers.** Telemetry (the
actual figures) is a *separate* channel that's shown on screen but never spoken. The
commentary is written for *ears* from the very start.

The lesson: if you bolt audio on at the end, you discover your text is full of things
that sound terrible read aloud ("P6", "lap 11", "+0.068"). Designing for the ear from
line one is far cheaper than retrofitting it.

---

## 2. Python environments — the lesson that unlocks everything else

This is the part that most reliably trips people up, so understand the *why*, not just
the incantation.

### Why virtual environments exist at all

On a modern Linux (your Mint box) or macOS, `pip install something` into the system
Python fails with `error: externally-managed-environment`. **This is the OS protecting
itself** — system tools depend on specific Python package versions, and letting you
overwrite them with `sudo pip` is how you brick parts of your OS. The correct response
is **never `sudo pip`**; it's to make a *virtual environment* — a private, disposable
Python that belongs to one project and can't hurt anything else.

### Why this project has *several* environments

Different tools demand different, mutually-incompatible Python versions and dependency
sets. You cannot satisfy them all in one venv. So the project keeps them apart:

| Environment | For | Python | Why separate |
|---|---|---|---|
| *(none)* | the simulator itself | any | **It's pure stdlib** — `python main.py` just works |
| `.venv` | Piper / Kokoro voices | modern (3.12+) | ordinary pip packages |
| `.venv-cb` | Chatterbox | **3.10 / 3.11** | its old pinned NumPy needs `distutils`, removed in 3.12 |
| a fresh venv | WhisperX + Demucs | 3.10–3.13 | drags in its own torch/pyannote; keep it away from the others |

**Only one venv is active in a shell at a time.** To switch, you `deactivate` the
current one and `source` the other. That's the whole mental model.

### Why `uv` is the tool we settled on

The painful classic problem: "Chatterbox needs Python 3.11, but my system has 3.12 —
how do I get 3.11 without wrecking my system Python?" The old answer was the
`deadsnakes` PPA and a lot of faff. **`uv` removes the problem entirely:** it fetches
its *own* standalone build of whatever Python version you ask for and builds the venv
from that, never touching the system interpreter.

```bash
# The one command that used to be a whole ordeal:
uv venv --python 3.11        # uv downloads a standalone 3.11 and makes a venv from it
source .venv/bin/activate
uv pip install <packages>    # use `uv pip install`, not bare pip, inside a uv venv
deactivate                   # when done
```

The lesson: **environment problems are version-and-isolation problems.** `uv` is worth
learning because it solves both at once — version fetching and venv creation — without
system-level changes.

### Setting up each environment (worked examples)

**Simulator** — nothing to do:
```bash
python main.py
```

**Piper / Kokoro** (a normal venv):
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install piper-tts          # + download voice packs into voices/ (see README)
uv pip install kokoro soundfile
```

**Chatterbox** (its own 3.11 venv, CUDA build of torch first):
```bash
uv venv --python 3.11 .venv-cb
source .venv-cb/bin/activate
uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
uv pip install chatterbox-tts
python -c "import torch; print('CUDA:', torch.cuda.is_available())"   # want: True
```

---

## 3. The TTS pipeline — turning words into a voice

`narration.py` is the optional spoken layer. It offers four engines on a deliberate
**quality-vs-cost ladder**, so you can develop fast and render nicely:

| Engine | Sounds like | Cost | Use it when |
|---|---|---|---|
| **espeak** | robotic, instant | system package, no GPU | sanity-checking that lines *play* at all |
| **piper** | clearer, still synthetic | CPU, voice packs | quick listenable previews |
| **kokoro** | noticeably natural | CPU, ~few-hundred-MB model | a good CPU-only render |
| **chatterbox** | best; *clones* voices | a CUDA GPU + fussy install | the real product output |

### Key TTS concepts

- **Reference clips (voice cloning).** Chatterbox clones a voice from a short, clean
  WAV per role dropped into `refs/` (`phill.wav`, `benny.wav`). No clips → a default
  voice. The *quality of the clone is only as good as the cleanliness of the
  reference clip* — which is exactly why Demucs (§5) matters for your sampling.
- **Paralinguistic tags.** Lines can carry `[laugh]`, `[sigh]`, `[chuckle]`. On
  screen they render as stage directions; before synthesis every engine strips them
  *except* Chatterbox Turbo, which actually performs them.
- **Render-to-WAV vs live playback.** A live run paces itself to the speech (you
  can't out-talk a voice). For a heavyweight model, **rendering to a file is the
  reliable path** — it replays the exact same line logic through a record-only
  narrator, gathers the whole script, and stitches the clips together.

### Running it

```bash
python main.py                                   # text only
python main.py --voice piper --track Spa         # read aloud, CPU
python main.py --voice chatterbox --chatterbox original --render spa.wav   # export
```

The CLI surface worth remembering: `--voice {silent,espeak,piper,kokoro,chatterbox}`,
`--chatterbox {turbo,original}`, `--track NAME`, `--laps N`, `--speed N`,
`--render FILE`.

### Chatterbox gotchas (each one cost real time once)

- **VRAM on a 6 GB card (your RTX 2060).** Chatterbox wants ~5–7 GB. The **Turbo**
  variant (~4.5 GB) is the safe default on 6 GB; `original` is the higher-quality
  model but tighter on memory.
- **The watermarker.** Chatterbox normally stamps an inaudible Resemble "Perth"
  watermark. In a `uv`-managed venv that component silently fails to load (it imports
  `pkg_resources`, which recent setuptools dropped) and sets itself to `None`, which
  breaks loading. The fix is a `_neutralise_watermarker()` shim that swaps in a no-op
  so the model loads. Nothing to install; the watermark just isn't applied, which is
  fine for local use.
- **Turbo doesn't accept `exaggeration`.** The Original variant takes an
  `exaggeration` kwarg; Turbo doesn't. Branch on the variant.

---

## 4. The reverse pipeline — analysing *real* audio to learn from it

§3 is about *producing* audio. This section (the most recent work) is about *taking
real broadcasts apart* so we can study how a genuine race broadcast is structured and
feed those lessons back into the director/booth — and, as a bonus, clean up our own
voice samples. Two tools.

### 4a. WhisperX — speech-to-text *with speaker tagging*

The job: take an mp3 of a real race broadcast and get back a transcript where **each
segment is labelled by who said it.** That labelling — knowing *who spoke when* — is
called **speaker diarization**, and it's the part we actually care about, because the
thing we want to study is the *give-and-take* between the lead caller and the colour
commentator.

WhisperX is a command-line tool (Linux + a terminal is all you need) that chains three
stages: Whisper transcribes, wav2vec2 aligns the words to precise timings, and pyannote
does the diarization. Output: a transcript with per-segment speaker labels and
timestamps.

**The Hugging Face token procedure** (the diarization model is *gated* — free, but you
must register and accept its terms):

1. Make a free account at huggingface.co.
2. **Accept the model terms** (the step everyone forgets — without it the token does
   nothing): https://huggingface.co/pyannote/speaker-diarization-community-1
   — click to agree while logged in. *(This used to be two separate model pages;
   it's now folded into this single one.)*
3. Create a token: profile → Settings → **Access Tokens** → New token, type **Read**.
4. Copy it immediately (`hf_...`; shown in full only once).
5. Treat it like a password — **never commit it.** Read it from an environment
   variable, don't hard-code it:
   ```bash
   export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
   ```

**Running it** (mp3 goes straight in — WhisperX decodes via ffmpeg, no manual
conversion needed):

```bash
sudo apt install ffmpeg                    # one-time, system tool

uv venv --python 3.12                      # its own venv, away from the others
source .venv/bin/activate
uv pip install whisperx

whisperx race.mp3 \
  --model large-v3 \                       # big model = better on noisy audio
  --diarize \                              # THIS flag turns speaker-tagging on
  --min_speakers 2 --max_speakers 2 \      # you have exactly two commentators
  --hf_token $HF_TOKEN \
  --compute_type int8                      # gentler on 6 GB of VRAM
```

**Lessons baked into those flags:**

- **Pin the speaker count.** With exactly two commentators, `--min_speakers 2
  --max_speakers 2` tells it not to invent a third voice — a real accuracy win.
- **Noise and overlap are diarization's weak spot.** Hence §4b below.
- **The output is structure, not identity.** You get `SPEAKER_00` / `SPEAKER_01`, not
  "Phill"/"Benny" — it tags *that there are two distinct voices*. One glance at the
  first exchange tells you which is the play-by-play and which is the colour man, and
  you relabel by hand. For our purposes that's ideal: `SPEAKER_00/01` with timestamps
  *is* the give-and-take laid bare — who held the floor, for how long, where the
  handoffs fall.

### 4b. Demucs — pulling a voice out of engine noise

Demucs is a **source-separation** model: hand it a mixed track and it splits it into
stems. The `--two-stems vocals` mode splits everything into "vocals" vs.
"everything else" — and a human voice over engine roar is exactly that kind of split.

It solves **two** of our problems with one tool:

1. **Clean the broadcast before transcription.** Engine noise confuses diarization;
   strip it first, then feed the clean vocal stem to WhisperX.
2. **Clean our own reference clips before cloning.** The background noise that's been
   ruining your Chatterbox samples — run the dirty sample through Demucs and cut the
   `refs/` clip from the cleaned stem instead.

```bash
uv pip install demucs

demucs --two-stems vocals race.mp3
# -> separated/htdemucs/race/vocals.wav

# then either feed that to WhisperX, or cut a Chatterbox reference clip from it.
```

**Honest caveats (it isn't magic):**

- It's trained mostly on **music**, so isolating speech from mechanical noise is
  slightly off-distribution — much cleaner, not surgically clean.
- It can introduce faint **"underwater" / smeary artifacts**. For *voice cloning* this
  matters: an artifact-heavy clip can sometimes clone *worse* than a slightly noisy
  but natural-sounding one. Trust your ears, not "cleaner on paper."
- **The cleaner the source moment, the cleaner the stem.** A voice *over* the engine
  separates better than one *buried under* it. Be picky about which seconds you sample.
- **Model variants:** default `htdemucs` is fast; `-n htdemucs_ft` (fine-tuned) is
  cleaner but several times slower — worth it for a short clip you'll reuse a lot.

---

## 5. Calibration — "commentary variety is a tuning problem"

A recurring lesson: a lot of what makes the broadcast feel *real* isn't logic, it's
**frequencies and variety**, and those are tuned empirically, not guessed.

- **Monte Carlo sweeps.** To check how often something happens (or whether the
  commentary repeats audibly), run the race many times and measure. **Bounded sweeps
  of 120–400 races** are the right tool; thousands are overkill and just burn time.
  Reusable scratch harnesses (`_mc.py`, `_harness.py`) live across sessions for this.
- **`_fresh()` no-repeat selection.** Lines are drawn from pools via a `_fresh()`
  helper that avoids immediate repeats. Variety is a *pool-management* problem.
- **Pools must be deep enough.** Minimum **6 lines per angle**, or repetition becomes
  audible over a full weekend.
- **The calibration targets we tune toward:**
  - Safety car ~30–40% of races, VSC ~25%, red flag ~2–3%, *any* neutralisation ~57%.
  - Attrition ~3.3–3.8 DNFs/race (genuine retirements + the two guaranteed
    Objectivist DNFs — Rand and Stirner never finish; that's the structural gag).
  - **Per-lap incident rates are normalised against a 40-lap baseline**, so a long
    circuit like Monaco (78 laps) doesn't inflate the carnage.

The lesson: when realism is statistical, *measure it* with bounded simulation and tune
to explicit targets — don't eyeball it.

---

## 6. How we actually work (meta-lessons)

These are working habits this project settled into that are worth keeping:

- **Design-forward.** Genuine architectural forks get discussed *before* building.
  Only the load-bearing forks get surfaced for a decision; minor trade-offs default to
  a recommendation. (This is why the `SeasonMemory`-wraps-`RaceMemory` boundary was
  agreed as a clean seam *before* any season-level code existed.)
- **Batched cross-layer deliveries.** A feature ships through every layer it touches
  at once — engine → director → booth → lore together — not as a trickle of partial
  patches.
- **Decisive execution.** No over-validation, no unsolicited rebuilds, no needless
  mid-build check-ins.
- **The engine stays pure stdlib.** External dependencies live only in the *optional*
  audio layers, never the core simulator. The thing always runs with bare `python`.

---

## 7. Quick command reference (the cheat-sheet)

Everything above, condensed to "what do I type."

**Run a race**
```bash
python main.py                                  # random circuit, text only
python main.py --track Spa                       # pick a circuit
python main.py --voice piper --track Monza       # read aloud (CPU)
python main.py --voice chatterbox --chatterbox original --render spa.wav   # best audio → file
```

**Set up an environment (uv)**
```bash
uv venv --python 3.11 .venv-cb && source .venv-cb/bin/activate   # e.g. Chatterbox
uv pip install <packages>
deactivate
```

**Transcribe + speaker-tag a real broadcast**
```bash
demucs --two-stems vocals race.mp3               # 1. strip engine noise
whisperx separated/htdemucs/race/vocals.wav \    # 2. transcribe + diarize
  --model large-v3 --diarize \
  --min_speakers 2 --max_speakers 2 \
  --hf_token $HF_TOKEN --compute_type int8
```

**Clean a Chatterbox reference clip**
```bash
demucs --two-stems vocals dirty_sample.mp3       # cut refs/ clip from the vocals.wav
# (use -n htdemucs_ft for a cleaner, slower separation on a clip you'll reuse a lot)
```

**Sanity checks**
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available())"   # GPU visible?
ffmpeg -version                                                       # ffmpeg present?
```

---

## 8. Where this is heading (not built yet — context only)

Recorded so future-you knows the intended direction:

- **Season-level narrative** — what a *season* sounds like: a standings narrative and
  a title race the booth carries across rounds. The seam is already drawn:
  `SeasonMemory` wrapping `RaceMemory`.
- **A unified "topic stack"** — generalising the two existing thread mechanisms
  (battle arcs in the director; the discussion thread in the booth) into one
  conversational thread manager that can *park* any topic on interruption and
  *resurface* it with an explicit bridge, the way a real booth does. The real-broadcast
  transcripts from §4 are the spec for this.
- **Intensity-driven audio pacing** — `Beat.intensity` (1–3) is already computed but
  currently discarded at the audio layer, where every line gets a flat 0.35 s gap.
  Making the inter-line gap vary with intensity is a cheap, decoupled realism win.

---

*Raweceek Simulator © 2026 by Pope Brak — CC BY-NC-SA 4.0. This lessons file is a
personal reference and is not part of the distributed project.*
