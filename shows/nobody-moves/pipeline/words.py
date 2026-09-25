"""When each word of a spoken line is said, for captions that highlight the current word.

The TTS model reports no timings, so they come from the audio of the finished line:
  1. the pauses the voice leaves at punctuation split the line into phrases (each comma or full
     stop in the spoken text is matched to a silence in the clip, in order);
  2. inside a phrase, its voiced time is shared among its words by their length in phonemes;
  3. the spoken words ("three twelve AM") are mapped back onto the caption's words ("3:12 AM").
Good to a fraction of a word, and it works on any audio: Kokoro, ElevenLabs or the user's own take.

  .venv/bin/python pipeline/words.py        # offline self-check on synthetic speech
"""
import difflib
import functools
import re

import numpy as np

FRAME = 0.01          # analysis hop, seconds
FLOOR_DB = -32        # a frame this far under the line's loudest frame counts as silence
MIN_PAUSE = 0.07      # shortest silence that counts as a pause
SKIP_BREAK = 0.35     # DP cost of a punctuation mark with no pause (voices sometimes run on)
SKIP_PAUSE = 0.12     # DP cost of a pause with no punctuation (a breath, a dramatic beat)
ENDS_PHRASE = re.compile(r"[,.;:!?—–…]+[\"')\]]*$")


def norm(word):
    return re.sub(r"[^\w']", "", word.lower())


@functools.lru_cache(maxsize=None)
def weight(word, phonemize=None):
    """How long a word takes to say, in phonemes (letters if no phonemizer)."""
    w = norm(word)
    if not w:
        return 0.3
    if phonemize:
        try:
            ph = re.sub(r"[ˈˌː\s.,!?;:\-]", "", phonemize(w))
            if ph:
                return float(len(ph))
        except Exception:
            pass
    return float(len(w))


def speech_map(y, sr):
    """(speech start, speech end, [(pause start, pause end), ...]) of a mono clip, in seconds."""
    y = np.asarray(y, dtype=np.float64)
    if y.ndim > 1:
        y = y.mean(axis=1)
    f = max(1, int(sr * FRAME))
    n = len(y) // f
    if n == 0:
        return 0.0, len(y) / sr, []
    env = np.sqrt(np.mean(y[: n * f].reshape(n, f) ** 2, axis=1))
    voiced = env > env.max() * 10 ** (FLOOR_DB / 20)
    idx = np.nonzero(voiced)[0]
    if not len(idx):
        return 0.0, len(y) / sr, []
    a, b = int(idx[0]), int(idx[-1]) + 1
    pauses, i = [], a
    while i < b:
        if voiced[i]:
            i += 1
            continue
        j = i
        while j < b and not voiced[j]:
            j += 1
        if (j - i) * FRAME >= MIN_PAUSE:
            pauses.append((i * FRAME, j * FRAME))
        i = j
    return a * FRAME, b * FRAME, pauses


def match_breaks(expected, pauses):
    """Ordered matching of predicted phrase breaks (times) to detected pauses: {break i: pause j}."""
    k, m = len(expected), len(pauses)
    mid = [(p0 + p1) / 2 for p0, p1 in pauses]
    cost = np.full((k + 1, m + 1), np.inf)
    move = np.zeros((k + 1, m + 1), dtype=int)
    cost[0, 0] = 0.0
    for i in range(k + 1):
        for j in range(m + 1):
            if i and cost[i - 1, j] + SKIP_BREAK < cost[i, j]:
                cost[i, j], move[i, j] = cost[i - 1, j] + SKIP_BREAK, 1
            if j and cost[i, j - 1] + SKIP_PAUSE < cost[i, j]:
                cost[i, j], move[i, j] = cost[i, j - 1] + SKIP_PAUSE, 2
            if i and j and cost[i - 1, j - 1] + abs(expected[i - 1] - mid[j - 1]) < cost[i, j]:
                cost[i, j], move[i, j] = cost[i - 1, j - 1] + abs(expected[i - 1] - mid[j - 1]), 3
    pairs, i, j = {}, k, m
    while i or j:
        mv = move[i, j]
        if mv == 3:
            pairs[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif mv == 1:
            i -= 1
        else:
            j -= 1
    return pairs


def spread(words_w, t0, t1, gaps):
    """Share [t0, t1] minus the silences in `gaps` among words by weight: [(start, end), ...]."""
    spans, cur = [], t0
    for g0, g1 in sorted(gaps):
        g0, g1 = max(g0, t0), min(g1, t1)
        if g1 <= g0:                   # this silence is outside the phrase
            continue
        if g0 > cur:
            spans.append((cur, g0))
        cur = max(cur, g1)
    if t1 > cur:
        spans.append((cur, t1))
    total_voiced = sum(b - a for a, b in spans) or 1e-6

    def at(frac):                      # voiced-time fraction -> clock time
        left = frac * total_voiced
        for a, b in spans:
            if left <= b - a:
                return a + left
            left -= b - a
        return t1

    total_w = sum(words_w) or 1.0
    out, acc = [], 0.0
    for w in words_w:
        out.append((at(acc / total_w), at((acc + w) / total_w)))
        acc += w
    return out


def spoken_times(y, sr, say, phonemize=None):
    """[(word, start, end), ...] for the words of `say`, relative to the clip start."""
    words = say.split()
    if not words:
        return []
    s0, s1, pauses = speech_map(y, sr)
    ws = [weight(w, phonemize) for w in words]
    total = sum(ws)
    # predicted time of each phrase break, from the words' share of the whole line
    breaks, acc = [], 0.0
    for i, w in enumerate(words[:-1]):
        acc += ws[i]
        if ENDS_PHRASE.search(w):
            breaks.append((i, s0 + (s1 - s0) * acc / total))
    pairs = match_breaks([t for _, t in breaks], pauses)
    used = set(pairs.values())
    free = [p for j, p in enumerate(pauses) if j not in used]
    # phrases between matched pauses
    bounds, start_word, start_t = [], 0, s0
    for bi, (wi, _) in enumerate(breaks):
        if bi in pairs:
            p0, p1 = pauses[pairs[bi]]
            bounds.append((start_word, wi + 1, start_t, p0))
            start_word, start_t = wi + 1, p1
    bounds.append((start_word, len(words), start_t, s1))
    # a pause with no punctuation (a breath, a beat) still falls between two words: split the phrase
    # at the word boundary nearest to it, if one is close; otherwise it's just skipped over
    loose = []
    for p0, p1 in free:
        for n, (a, b, t0, t1) in enumerate(bounds):
            if t0 < p0 and p1 < t1:
                cuts = spread(ws[a:b], t0, t1, [(p0, p1)])
                edges = [(abs(cuts[i][1] - (p0 + p1) / 2), a + i + 1) for i in range(b - a - 1)]
                if edges and min(edges)[0] < 0.3:
                    cut = min(edges)[1]
                    bounds[n:n + 1] = [(a, cut, t0, p0), (cut, b, p1, t1)]
                else:
                    loose.append((p0, p1))
                break
    out = []
    for a, b, t0, t1 in bounds:
        for w, (ta, tb) in zip(words[a:b], spread(ws[a:b], t0, t1, loose)):
            out.append((w, ta, tb))
    return out


def caption_times(y, sr, say, text, phonemize=None):
    """[[caption word, start, end], ...] relative to the clip start, for the caption `text`."""
    spoken = spoken_times(y, sr, say, phonemize)
    shown = text.split()
    if not spoken or not shown:
        return []
    a = [norm(w) for w, _, _ in spoken]
    b = [norm(w) for w in shown]
    out = [None] * len(shown)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                out[j1 + k] = (spoken[i1 + k][1], spoken[i1 + k][2])
        elif tag == "replace":        # e.g. "three twelve" said for "3:12": share the span by length
            t0, t1 = spoken[i1][1], spoken[i2 - 1][2]
            lens = [max(1, len(w)) for w in shown[j1:j2]]
            acc = 0
            for k, n in enumerate(lens):
                out[j1 + k] = (t0 + (t1 - t0) * acc / sum(lens), t0 + (t1 - t0) * (acc + n) / sum(lens))
                acc += n
        elif tag == "insert":         # shown but not said: flash with the next spoken word
            t = spoken[i1][1] if i1 < len(spoken) else spoken[-1][2]
            for k in range(j1, j2):
                out[k] = (t, t)
    return [[w, round(t0, 3), round(t1, 3)] for w, (t0, t1) in zip(shown, out)]


def selfcheck():
    """Tone bursts stand in for words; the pauses sit at the commas and one at a breath."""
    sr = 24000

    def burst(sec):
        t = np.arange(int(sec * sr)) / sr
        return 0.3 * np.sin(2 * np.pi * 180 * t) * (1 + 0.5 * np.sin(2 * np.pi * 7 * t))

    def gap(sec):
        return np.zeros(int(sec * sr))

    # "At three twelve AM, someone moved Deb." as bursts; a burst per word, a 0.3 s pause at the comma
    say = "At three twelve AM, someone moved Deb."
    parts, starts, t = [], [], 0.05
    parts.append(gap(0.05))
    for i, (w, sec) in enumerate(zip(say.split(), [0.15, 0.3, 0.35, 0.3, 0.4, 0.3, 0.3])):
        starts.append(t)
        parts.append(burst(sec))
        t += sec
        pause = 0.3 if w.endswith(",") else 0.0
        parts.append(gap(pause))
        t += pause
    parts.append(gap(0.2))
    y = np.concatenate(parts)
    got = caption_times(y, sr, say, "At 3:12 AM, someone moved Deb.")
    words = [w for w, _, _ in got]
    assert words == ["At", "3:12", "AM,", "someone", "moved", "Deb."], words
    assert all(a <= b for _, a, b in got), got
    assert all(got[i][1] <= got[i + 1][1] for i in range(len(got) - 1)), got
    someone = got[3][1]
    assert abs(someone - starts[4]) < 0.03, (someone, starts[4])    # right after the comma's pause
    assert got[0][1] < 0.1 and got[-1][2] > t - 0.05, got
    print("words.py self-check: ok (" + ", ".join(f"{w}@{a:.2f}" for w, a, _ in got) + ")")


if __name__ == "__main__":
    selfcheck()
