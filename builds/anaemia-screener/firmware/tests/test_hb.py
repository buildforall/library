# pytest tests/   (from firmware/)
import math
import os
import random
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hb  # noqa: E402

FS = 40.0


def ppg(dc, ac_pp, seconds=20, hr=75, noise=0.0, seed=0):
    rng = random.Random(seed)
    f = hr / 60
    return [dc + ac_pp / 2 * math.sin(2 * math.pi * f * n / FS) + rng.gauss(0, noise)
            for n in range(int(seconds * FS))]


def test_ac_dc_recovers_a_sine():
    ac, dc = hb.ac_dc(ppg(3000, 40), FS)
    assert abs(dc - 3000) < 1
    # The 1.5 s moving average does not span a whole number of beats, so the
    # absolute AC is biased by a few per cent. The bias is the same at every
    # wavelength and cancels in the ratios, which test_ratio_* check.
    assert abs(ac - 40) < 0.1 * 40


def test_ratio_is_zero_when_perfusion_matches_reference():
    sig = [ppg(2000 + 300 * i, 0.01 * (2000 + 300 * i)) for i in range(5)]
    ac, dc = zip(*(hb.ac_dc(s, FS) for s in sig))
    x = hb.ratios(list(ac), list(dc))
    assert all(abs(v) < 0.02 for v in x)


def test_ratio_sign_follows_relative_pulsatility():
    sig = [ppg(2000, 40), ppg(2000, 20), ppg(2000, 20), ppg(2000, 20), ppg(2000, 20)]
    ac, dc = zip(*(hb.ac_dc(s, FS) for s in sig))
    x = hb.ratios(list(ac), list(dc))
    assert abs(x[0] - math.log(2)) < 0.05


def test_weak_signal_detected():
    ac, dc = zip(*(hb.ac_dc(ppg(100, 5), FS) for _ in range(5)))
    assert hb.weak(list(ac), list(dc))


def test_estimate_is_linear():
    assert hb.estimate([12.0, 1.0, 0, 0, -2.0], [0.5, 9, 9, 0.25]) == 12.0
