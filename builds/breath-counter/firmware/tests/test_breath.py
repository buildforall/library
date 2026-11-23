# Run on a computer:  python3 -m pytest tests/   (from firmware/)
# Feeds synthetic abdominal motion through breath.Session.

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import breath  # noqa: E402


def run(rate_per_min, band=2, seconds=70, noise=0.004, wobble=None, seed=1):
    rng = random.Random(seed)
    s = breath.Session(band)
    f = rate_per_min / 60.0
    for n in range(int(seconds * breath.FS)):
        t = n / breath.FS
        b = 0.02 * math.sin(2 * math.pi * f * t)
        x, y, z = 0.05 + 0.3 * b, -0.02 + b, 0.99 + 0.6 * b
        if wobble and wobble[0] <= t < wobble[1]:
            jolt = 0.3 * math.sin(2 * math.pi * 7 * t)
            x, y, z = x + jolt, y - 0.5 * jolt, z + jolt
        x += rng.gauss(0, noise)
        y += rng.gauss(0, noise)
        z += rng.gauss(0, noise)
        if s.feed(x, y, z) in (breath.RESULT, breath.ABORTED):
            break
    return s


def test_counts_within_two_breaths():
    for rate in (30, 45, 62, 75):
        s = run(rate, seconds=80)
        assert s.phase == breath.RESULT
        assert abs(s.result - rate) <= 2, (rate, s.result)


def test_cutoffs_by_age():
    assert run(55, band=1, seconds=80).fast
    assert not run(55, band=0, seconds=80).fast
    assert run(42, band=2, seconds=80).fast


def test_movement_pauses_the_minute():
    s = run(40, seconds=90, wobble=(20, 30))
    assert s.phase == breath.RESULT
    assert s.moving_n > 8 * breath.FS
    assert abs(s.result - 40) <= 2


def test_long_movement_aborts():
    s = run(40, seconds=90, wobble=(10, 50))
    assert s.phase == breath.ABORTED
