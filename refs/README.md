# Chatterbox reference voices

This folder holds the **reference clips** that give the Chatterbox booth its voices.
Chatterbox clones a voice from a short sample, so each booth role points at one WAV
here (`narration.py`, the `CHATTERBOX_VOICE` map). Override the location with the
`CHATTERBOX_REF_DIR` environment variable.

| Booth role | Persona | Reference file |
|------------|---------|----------------|
| `pbp`      | Vale    | `vale.wav`     |
| `colour`   | Benny   | `benny.wav`    |

If a clip is missing, that role falls back to Chatterbox's built-in default voice —
which works, but then **both commentators sound the same**, so for the two-voice booth
you want both files present.

## What makes a good clip

- **10–30 seconds** of one person speaking, clean, no music or background noise.
- A mono or stereo WAV is fine. Match the *character* you want: a brighter, quicker
  voice for Vale; a lower, drier one for Benny.
- The expressiveness dial (`exaggeration` in `CHATTERBOX_VOICE`) is already set per
  role — animated for Vale, level for Benny. Tweak there, not in the clip.

You can record these yourself (a phone voice memo exported to WAV is plenty) or use any
audio you have the rights to use. Drop them in as `vale.wav` and `benny.wav`.

## Installing Chatterbox (the fiddly part)

Chatterbox is a GPU model, so this is more involved than Piper/Kokoro:

```bash
# Use Python 3.10 -- it's the version with prebuilt wheels for all the deps.
python3.10 -m venv .venv-cb
source .venv-cb/bin/activate
pip install --upgrade pip

# Install a CUDA build of PyTorch FIRST (pick the index URL for your CUDA version;
# cu121 is a safe default for an RTX 2060). See https://pytorch.org for the current line.
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Then Chatterbox itself.
pip install chatterbox-tts

# Sanity check that the GPU is visible:
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

If that last line prints `CUDA: True`, you're set. If it prints `False`, PyTorch
installed as a CPU build — reinstall it with the CUDA index URL above.

## Running it

```bash
# Your RTX 2060 has 6 GB, so use the Turbo variant (the default here). It's set via
# the CHATTERBOX_VARIANT env var; "original" wants more VRAM than a 2060 has.
python main.py --voice chatterbox --track Spa

# Heavyweight models are happiest rendering to a file rather than pacing a live race:
python main.py --voice chatterbox --track Spa --render spa.wav
```

First run downloads the model (~1 GB) and loads it onto the GPU — you'll see a
`[chatterbox: first run downloads...]` message, then `[chatterbox: ready]`. After that
it's cached. If you see a "no CUDA GPU" notice, the race falls back to silent and the
hint tells you to fix the PyTorch install (above) or render to WAV instead.

Note: Chatterbox embeds an inaudible watermark in its output (Resemble AI's PerTh) so
synthetic audio stays detectable — normal, and it doesn't affect how it sounds.
