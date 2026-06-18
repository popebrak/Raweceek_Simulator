# RaWeCeEk Simulator

I'm learning python.

By the most absurd means possible.

Do not judge me.

---

A terminal **Formula 1 race-weekend simulator** in which the grid is twenty radical
political philosophers, and a two-person commentary booth calls the whole thing —
optionally **out loud**, in synthesized voices.

It runs a full weekend: qualifying (with the real 107% rule), a race with tyre wear,
pit strategy, weather, and crashes, and pre- and post-race shows. Everything the engine
does becomes something the booth can talk about.

## What it does

- **A 20-driver, 10-team grid of philosophers** — Plato, Nietzsche, Bakunin, de
  Beauvoir, Marx, Luxemburg, Goldman, Foucault, Derrida, Fanon, and more. (The
  Objectivism team of Rand and Stirner is contractually obligated to never see the
  chequered flag.)
- **A proper race model** — qualifying and the 107% cut, per-compound tyre wear and
  warm-up, pit strategy with tactical undercuts, launches, overtaking tuned per
  circuit, two-car collisions with component damage, and delayed mechanical DNFs.
- **Weather** that can change mid-race and reshuffle everything.
- **A commentary booth with two personas** — **Vale**, the excitable lap-caller, and
  **Benny**, the dry ex-racer who thinks the philosophy is daft. They preview the grid,
  call the race live, build run-in tension in the closing laps, and debrief afterwards,
  with quotes from the philosophers on the podium.
- **Optional spoken commentary** — the booth can be *read aloud* by any of four
  text-to-speech engines, from instant-and-robotic to GPU-quality voice cloning. Or it
  can render a whole weekend to a single `.wav` file.

## Sample

```
  ==============================================================
  ITALIAN GRAND PRIX
  Monza, Italy   --   53 laps
  The Temple of Speed -- long straights, big tows, easy passing.
  ==============================================================

  QUALIFYING RESULTS
  --------------------------------------------------------------
  P1  Mikhail Bakunin       Black Banner    1:20.602  POLE
  P2  Michel Foucault       Différance      1:20.670  +0.068
  ...
  P20 Jacques Derrida       Différance      1:21.635  +1.032

  107% cutoff: 1:26.245   (pole 1:20.602)

  ------------------------------------------------------------
  COUNTDOWN TO GREEN
  VALE:  Welcome to Monza -- we are set for the Italian Grand Prix.
  BENNY: Big tow, late on the brakes, tifosi screaming for red. Can't not love it.
  VALE:  Pole position goes to Mikhail Bakunin for Black Banner, Michel Foucault alongside.
  BENNY: Quick over one lap -- but the head for a race? We'll see. Could come back to bite.

  ... [the race plays back live, lap by lap] ...

  L11  VALE:  THE UNDERCUT WORKS! Thomas Paine boxed a lap earlier than Diogenes,
              and the fresh rubber vaults them ahead into P6.

  FINAL CLASSIFICATION
  ------------------------------------------------------------------
  P1  Michel Foucault       Différance      18:43.888  WINNER    (from P2, UP 1)
  P2  Mary Wollstonecraft   Rights of Man   18:50.339  +6.451    (from P6, UP 4)
  P3  Karl Marx             Vanguard        18:53.384  +9.497    (from P8, UP 5)  [damaged]
  ...
  --  Ayn Rand              Objectivism     DNF (lap 1, from P13)

  POST-RACE SHOW
  VALE:  And that's the chequered flag at Monza -- Michel Foucault wins it for Différance!
  BENNY: From second on the grid! That's not luck, that's a drive.
  VALE:  Let's hear from the podium.
  MICHEL FOUCAULT: They were all being watched. I was the one who decided where to look.
  KARL MARX: The history of all racing is the history of strategy. Today, the strategy was correct.
  VALE:  From Monza, that's all from us. Goodnight!
  BENNY: Drive home safe. Unlike that lot.
```

## Running it

```bash
python main.py                       # random circuit, text only
python main.py --track Spa           # pick a circuit
python main.py --voice piper         # read the booth aloud (see setup below)
python main.py --voice chatterbox --render spa.wav   # export a weekend to audio
```

Options: `--voice {silent,espeak,piper,kokoro,chatterbox}` (default `silent`),
`--track NAME`, `--laps N`, `--speed N`, `--render FILE`. With a voice on, the race
paces itself to the speech; `--render` writes a `.wav` instead of playing live.

## Setup

The simulator itself is pure Python and needs nothing extra — `python main.py` just
works. Everything below is **only** for hearing the commentary aloud.

### The virtual environment (do this once)

On recent Linux/macOS, `pip install` into the system Python fails with
`error: externally-managed-environment` — the OS is protecting its own Python. The fix
is a virtual environment (a private Python for this project), not `sudo`:

```bash
sudo apt install python3-venv python3-pip    # Debian/Ubuntu only; skip on macOS
cd /path/to/this/project
python3 -m venv .venv                        # create it once, at the project root
source .venv/bin/activate                    # activate each session (prompt shows (.venv))
pip install --upgrade pip
#   .venv\Scripts\Activate.ps1   on Windows PowerShell
```

You only *create* it once; each new terminal, just re-run the `source ... activate`
line. `deactivate` when done.

### The four voices

| Engine | Quality | Needs | Install |
|--------|---------|-------|---------|
| **espeak** | robotic, instant | nothing but the system package | `sudo apt install espeak-ng` (or `brew install espeak`) |
| **piper** | clearer, still synthetic | CPU only; voice packs | `pip install piper-tts` + download voices (below) |
| **kokoro** | noticeably natural | CPU (downloads ~few hundred MB once) | `pip install kokoro soundfile` |
| **chatterbox** | best; clones voices | a CUDA GPU + a fussier install | see its own section |

espeak is a *system program*, not a pip package — it installs the same way regardless
of any venv. The other three go through pip, inside your activated venv.

### Piper voices

Piper needs voice packs (an `.onnx` model **plus** its `.onnx.json` config) in a
`voices/` folder. Three voices give the booth Vale, Benny, and a podium voice:

```bash
cd voices
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main
wget $BASE/en/en_GB/alan/medium/en_GB-alan-medium.onnx
wget $BASE/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json
wget $BASE/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx
wget $BASE/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json
wget $BASE/en/en_US/ryan/high/en_US-ryan-high.onnx
wget $BASE/en/en_US/ryan/high/en_US-ryan-high.onnx.json
cd ..
python main.py --voice piper --track Spa
```

(No `wget`? use `curl -L -O <url>`.) Full voice catalogue and the role→voice map are in
`voices/README.md`.

### Kokoro

```bash
pip install kokoro soundfile
python main.py --voice kokoro --track Spa
```

The first run downloads the ~82M-parameter model from Hugging Face (a few hundred MB,
once — you'll see a "please wait" message, then it's cached). It uses espeak-ng as a
pronunciation fallback, so having espeak installed helps.

### Chatterbox (the GPU one)

Highest quality and it *clones* voices from short reference clips — but it's the fussiest
to set up, and it's a GPU model.

- **Use Python 3.10 or 3.11.** On 3.12 the install breaks (an old pinned NumPy needs
  `distutils`, which 3.12 removed). Chatterbox therefore needs its **own** virtual
  environment, separate from the `.venv` you set up for the simulator and
  Piper/Kokoro — they can't share one, because that `.venv` is almost certainly on a
  different Python version.

  Only one venv is active in a terminal at a time, so **first deactivate the one you're
  in**, then create and activate a *new, separate* venv (`.venv-cb`) at the project
  root, built with a 3.10/3.11 interpreter:

  ```bash
  deactivate                  # leave the simulator/Piper/Kokoro .venv if it's active
                              # (skip this if no venv is currently active)

  cd /path/to/this/project    # the project root -- same place as your existing .venv
  python3.11 -m venv .venv-cb # a brand-new, separate venv (note the different name)
  source .venv-cb/bin/activate
  pip install --upgrade pip

  # install a CUDA build of PyTorch FIRST (cu121 is a safe default for an RTX 2060):
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
  pip install chatterbox-tts
  python -c "import torch; print('CUDA:', torch.cuda.is_available())"   # want: True
  ```

  From then on you have two venvs side by side: activate `.venv` for `--voice piper`
  or `--voice kokoro`, or `.venv-cb` for `--voice chatterbox`. Switching between them is
  always `deactivate` then `source <the-other>/bin/activate`.

- **VRAM:** Chatterbox wants ~5–7 GB. On a 6 GB card use the **Turbo** variant (the
  default here, ~4.5 GB); don't switch `CHATTERBOX_VARIANT` to `original`.
- **Voices:** drop a clean ~10–30 s WAV per role into `refs/` as `vale.wav` and
  `benny.wav`. No clips → both speakers use the built-in default voice. See
  `refs/README.md`.
- **Run it** (rendering to a file is the reliable path for a heavyweight model):

  ```bash
  python main.py --voice chatterbox --track Spa --render spa.wav
  ```

## Project structure

```
main.py         entry point + CLI; runs a weekend, plays it back, drives audio
simulation.py   the engine: qualifying, race loop, strategy, analysis
drivers.py      the 20-philosopher / 10-team grid (data)
tracks.py       the circuit calendar (data)
weather.py      conditions and changes (data)
colour.py       the commentary booth -- Vale & Benny, the shows, the banter
lore.py         the lines: track history, persona quips, podium quotes
display.py      rendering: standings board, commentary feed, telemetry, results
narration.py    the optional spoken layer -- espeak / piper / kokoro / chatterbox
voices/         Piper voice packs live here (README inside)
refs/           Chatterbox reference clips live here (README inside)
```

Architecture in one line: **the engine reasons, the data describes, the display speaks,
and the narration gives it a voice.**

## .gitignore

The downloaded models and audio are big and/or personal, so they're not tracked:

```gitignore
.venv*/               # any virtual environment (.venv, .venv-cb, ...)
__pycache__/
*.pyc
voices/*.onnx         # Piper voice packs (the folder's README stays tracked)
voices/*.onnx.json
*.wav                 # Chatterbox reference clips + rendered race audio
```

(Kokoro and Chatterbox model weights cache in `~/.cache/huggingface`, outside the repo,
so there's nothing to ignore for those.)

---

Raweceek Simulator © 2026 by Pope Brak is licensed under CC BY-NC-SA 4.0. To view a copy
of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/
