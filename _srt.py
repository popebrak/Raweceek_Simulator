#!/usr/bin/env python3
"""_srt.py -- dev-only analysis harness for a diarized .srt transcript.

NOT project code. NOT for the repo. A measuring instrument, like _mc.py.
It reads whatever .srt path you give it and reports STRUCTURE ONLY --
turn rhythms, floor-holding, handoff balance, and generic discourse-marker
leanings per speaker. It contains, stores, and prints NO transcript content:
only aggregate numbers. The sample audio/transcript stay in the dev process;
nothing here ever crosses into Phill & Benny's lines.

Usage:
    python _srt.py path/to/vocals.srt
    python _srt.py path/to/vocals.srt --top 3      # how many lead voices to profile
"""

import argparse
import re
import statistics as stats
from collections import Counter, defaultdict

SPK = re.compile(r"\[SPEAKER_(\d+)\]")
TS = re.compile(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)")

# Generic English discourse hinges, grouped by the role they tend to signal.
# These are ordinary connective words, not lines lifted from any broadcast.
MARKERS = {
    "lead (chaining)": ["and", "so", "but", "now", "then", "because", "as"],
    "colour (opener)": ["well", "look", "i mean", "you know", "for me",
                         "to be fair", "mind you", "that said", "i think",
                         "the thing is", "what i", "of course"],
}


def parse(path):
    """Yield (speaker_or_None, seconds, word_count) per caption block."""
    block = []
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = raw.rstrip("\n")
        if line.strip() == "":
            if block:
                yield _block(block)
                block = []
        else:
            block.append(line)
    if block:
        yield _block(block)


def _block(lines):
    spk, secs, text_parts = None, 0.0, []
    for ln in lines:
        m = TS.search(ln)
        if m:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, m.groups())
            t1 = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
            t2 = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
            secs = max(0.0, t2 - t1)
            continue
        if ln.strip().isdigit() and not text_parts:
            continue  # the index line
        sm = SPK.search(ln)
        if sm:
            spk = sm.group(1)
            ln = SPK.sub("", ln).lstrip(": ").strip()
        text_parts.append(ln)
    words = len(" ".join(text_parts).split())
    return spk, secs, words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("srt")
    ap.add_argument("--top", type=int, default=3,
                    help="profile this many dominant speakers (default 3)")
    args = ap.parse_args()

    blocks = list(parse(args.srt))

    # --- per-speaker totals -------------------------------------------------
    secs = defaultdict(float)
    words = defaultdict(int)
    nblk = defaultdict(int)
    for spk, s, w in blocks:
        key = spk if spk is not None else "??"
        secs[key] += s
        words[key] += w
        nblk[key] += 1

    ranked = sorted((k for k in secs if k != "??"),
                    key=lambda k: secs[k], reverse=True)
    top = ranked[:args.top]
    total_secs = sum(secs.values()) or 1.0

    print("=" * 64)
    print(f"FILE: {args.srt}   ({len(blocks)} caption blocks)")
    print("=" * 64)
    print("\n--- talk-time share (who the booth actually is) ---")
    print(f"{'spk':>5} {'blocks':>7} {'words':>7} {'mins':>7} {'share':>7}")
    for k in ranked + (["??"] if "??" in secs else []):
        print(f"{k:>5} {nblk[k]:>7} {words[k]:>7} "
              f"{secs[k]/60:>7.1f} {secs[k]/total_secs:>6.1%}")

    # --- collapse consecutive same-speaker blocks into TURNS ---------------
    turns = defaultdict(list)          # speaker -> list of (blocks, words, secs)
    seq = []                           # ordered speaker sequence (for handoffs)
    cur, cb, cw, cs = None, 0, 0, 0.0
    for spk, s, w in blocks:
        if spk != cur:
            if cur is not None:
                turns[cur].append((cb, cw, cs))
            cur, cb, cw, cs = spk, 0, 0, 0.0
            if spk is not None:
                seq.append(spk)
        cb += 1
        cw += w
        cs += s
    if cur is not None:
        turns[cur].append((cb, cw, cs))

    print(f"\n--- floor-holding profile (top {args.top} by talk-time) ---")
    print("the LEAD holds long runs; the COLOUR punctuates with short ones")
    print(f"{'spk':>5} {'turns':>6} {'med_blk':>8} {'avg_blk':>8} "
          f"{'longest':>8} {'med_wds':>8}")
    for k in top:
        t = turns[k]
        blk = [x[0] for x in t]
        wds = [x[1] for x in t]
        print(f"{k:>5} {len(t):>6} {stats.median(blk):>8.1f} "
              f"{sum(blk)/len(t):>8.1f} {max(blk):>8} {stats.median(wds):>8.1f}")

    # --- handoff matrix among the top speakers -----------------------------
    pair = Counter()
    for a, b in zip(seq, seq[1:]):
        if a in top and b in top and a != b:
            pair[(a, b)] += 1
    print("\n--- handoffs among top speakers (balance = real dialogue) ---")
    for (a, b), n in pair.most_common():
        rev = pair.get((b, a), 0)
        bal = f"(<-> {rev}; {min(n,rev)/max(n,rev):.0%} balanced)" if rev else ""
        print(f"  {a} -> {b}: {n:>3}  {bal}")

    # --- discourse-marker leanings, per 1000 words -------------------------
    # second pass: need text per speaker, but counted as numbers only
    mtext = defaultdict(str)
    block = []
    for raw in open(args.srt, encoding="utf-8", errors="replace"):
        ln = raw.rstrip("\n")
        if ln.strip() == "":
            block = []
            continue
        sm = SPK.search(ln)
        if sm:
            txt = SPK.sub("", ln).lstrip(": ").strip()
            mtext[sm.group(1)] += " " + txt.lower()

    print("\n--- discourse-marker rate per 1000 words (higher = leans on it) ---")
    hdr = "  ".join(f"{k:>6}" for k in top)
    print(f"{'marker':>14}  {hdr}")
    for group, words_list in MARKERS.items():
        print(f"  [{group}]")
        for mk in words_list:
            patt = re.compile(r"\b" + re.escape(mk) + r"\b")
            row = []
            for k in top:
                wc = max(1, words[k])
                rate = len(patt.findall(mtext[k])) / wc * 1000
                row.append(f"{rate:>6.1f}")
            print(f"{mk:>14}  " + "  ".join(row))


if __name__ == "__main__":
    main()
