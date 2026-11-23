# Signal processing for the anaemia screener. Plain Python: runs on the board
# under CircuitPython and on a computer for the tests.
#
# Five LEDs shine through the fingertip in turn. For each wavelength the
# pulsatile (AC) and steady (DC) parts of the light are separated. Log ratios of
# AC/DC against 940 nm are the model inputs for haemoglobin.

import math

NM = (530, 590, 660, 810, 940)
REF = 4   # 940 nm is the reference channel

# WHO haemoglobin cut-offs for anaemia, g/dL
GROUPS = ("Woman", "Pregnant", "Man", "Child 6-59m")
CUTOFFS = (12.0, 11.0, 13.0, 11.0)


def ac_dc(x, fs):
    """AC: RMS after removing a 1.5 s moving average, scaled to the
    peak-to-peak of an equivalent sine. DC: mean."""
    n = len(x)
    dc = sum(x) / n
    w = max(3, int(1.5 * fs))
    run = 0.0
    ss = 0.0
    m = 0
    for i in range(n):
        run += x[i]
        if i >= w:
            run -= x[i - w]
            d = x[i - w // 2] - run / w
            ss += d * d
            m += 1
    ac = 2.828 * math.sqrt(ss / max(m, 1))
    return ac, dc


def ratios(ac, dc):
    """log((AC/DC)_i / (AC/DC)_940) for the four non-reference wavelengths."""
    ref = ac[REF] / dc[REF]
    return [math.log((ac[i] / max(dc[i], 1.0)) / ref) for i in range(4)]


def weak(ac, dc):
    return dc[REF] < 200 or ac[REF] < 1


def estimate(model, x):
    """model: [c0, c1, c2, c3, c4] for Hb = c0 + c1*x1 + ... + c4*x4."""
    return model[0] + sum(c * v for c, v in zip(model[1:], x))
