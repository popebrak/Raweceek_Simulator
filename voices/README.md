# Piper voice packs

This folder is where the **Piper** voices live. `narration.py` looks here by default
(override with the `PIPER_VOICE_DIR` environment variable). Each "voice" is **two
files** that must sit side by side: the model (`.onnx`) and its config (`.onnx.json`).
Piper won't load one without the other.

You only need these for `--voice piper`. The espeak and kokoro backends don't use this
folder (espeak is a system package; kokoro downloads its own model on first run).

## What maps to whom

The role-to-voice map lives at the top of `narration.py` (`PIPER_VOICE`). The defaults:

| Booth role | Persona | Voice pack                          |
|------------|---------|-------------------------------------|
| `pbp`      | Vale    | `en_GB-alan-medium`                 |
| `colour`   | Benny   | `en_GB-northern_english_male-medium`|
| (fallback) | podium  | `en_US-ryan-high`                   |

To swap a voice, download a different pack (see the full list linked below) and change
the filename in `PIPER_VOICE` / `PIPER_DEFAULT`.

## Download (run these from inside this `voices/` folder)

The packs come from the official Piper voices repo on Hugging Face
(`rhasspy/piper-voices`, MIT-licensed; the repo is archived and read-only, so these
links are stable). Six files total — a model and a config for each of the three voices:

```bash
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main

# Vale  -- en_GB-alan-medium
wget $BASE/en/en_GB/alan/medium/en_GB-alan-medium.onnx
wget $BASE/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json

# Benny -- en_GB-northern_english_male-medium
wget $BASE/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx
wget $BASE/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json

# Podium / fallback -- en_US-ryan-high
wget $BASE/en/en_US/ryan/high/en_US-ryan-high.onnx
wget $BASE/en/en_US/ryan/high/en_US-ryan-high.onnx.json
```

No `wget`? Swap each line for `curl -L -O <url>` (the `-L` follows Hugging Face's
redirect; `-O` keeps the original filename).

## The one-command alternative

Recent `piper-tts` ships a downloader that fetches a voice into the current folder:

```bash
python -m piper.download_voices en_GB-alan-medium
```

If your installed version doesn't have that subcommand, just use the `wget` lines above
— they're the same files.

## Check it worked

From the project root, with piper installed:

```bash
python main.py --voice piper --track Spa
```

If the voices are found you'll hear the booth; if a file is missing you'll get a one-line
hint naming this folder, and the race falls back to the normal text-only playback.

The full catalogue of voices (35 languages, multiple speakers each):
https://github.com/rhasspy/piper/blob/master/VOICES.md
