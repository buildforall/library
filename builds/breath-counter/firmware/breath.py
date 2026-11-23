# Breath counting from abdominal motion.
#
# Pure Python, no hardware imports, so the same file runs on the board and
# under CPython for the tests in tests/.
#
# Each accelerometer axis is band-passed to 0.15-2 Hz (9-120 breaths/min) and
# counted with an adaptive hysteresis threshold. The axis that carries the most
# breathing power over the minute gives the count. High-frequency energy on the
# vector magnitude means the child is moving; the minute pauses until they settle.

import math

FS = 50                 # samples per second
MIN_BREATH_S = 0.66     # refractory period: nothing faster than ~90/min is counted
MOTION_G = 0.08         # RMS of >3 Hz content that counts as "moving", in g
COUNT_S = 60
SETTLE_S = 5
MAX_MOTION_S = 30

AGE_BANDS = ("< 2 months", "2-11 months", "1-5 years")
CUTOFFS = (60, 50, 40)  # WHO fast-breathing thresholds, breaths per minute


class Biquad:
    """Second-order section, RBJ cookbook, Q = 1/sqrt(2)."""

    def __init__(self, highpass, fc, fs=FS):
        w = 2 * math.pi * fc / fs
        c, s = math.cos(w), math.sin(w)
        alpha = s / (2 * 0.70710678)
        a0 = 1 + alpha
        if highpass:
            self.b0 = (1 + c) / 2 / a0
            self.b1 = -(1 + c) / a0
        else:
            self.b0 = (1 - c) / 2 / a0
            self.b1 = (1 - c) / a0
        self.b2 = self.b0
        self.a1 = -2 * c / a0
        self.a2 = (1 - alpha) / a0
        self.z1 = self.z2 = 0.0

    def step(self, x):
        y = self.b0 * x + self.z1
        self.z1 = self.b1 * x - self.a1 * y + self.z2
        self.z2 = self.b2 * x - self.a2 * y
        return y


class Axis:
    def __init__(self):
        self.hp = Biquad(True, 0.15)
        self.lp = Biquad(False, 2.0)
        self.var = 1e-6
        self.power = 0.0
        self.high = False
        self.last = -10.0
        self.count = 0

    def update(self, x, t, counting):
        y = self.lp.step(self.hp.step(x))
        self.var += (y * y - self.var) / (5 * FS)       # ~5 s time constant
        h = 0.35 * math.sqrt(self.var)
        if not self.high and y > h:
            self.high = True
            if counting and t - self.last >= MIN_BREATH_S:
                self.count += 1
                self.last = t
        elif self.high and y < -h:
            self.high = False
        if counting:
            self.power += y * y


IDLE, SETTLE, COUNTING, RESULT, ABORTED = range(5)


class Session:
    """One measurement. Feed it one sample every 1/FS seconds."""

    def __init__(self, band):
        self.band = band
        self.axes = [Axis(), Axis(), Axis()]
        self.motion_hp = Biquad(True, 3.0)
        self.motion_pow = 0.0
        self.phase = SETTLE
        self.n = 0              # samples since start
        self.counted = 0        # samples counted (child still)
        self.moving_n = 0       # samples lost to movement
        self.result = None

    @property
    def moving(self):
        return self.motion_pow > MOTION_G * MOTION_G

    @property
    def best(self):
        return max(self.axes, key=lambda a: a.power)

    @property
    def live_count(self):
        return self.best.count

    @property
    def seconds_counted(self):
        return self.counted // FS

    @property
    def fast(self):
        return self.result is not None and self.result >= CUTOFFS[self.band]

    def feed(self, gx, gy, gz):
        """Acceleration in g. Returns the phase after this sample."""
        if self.phase not in (SETTLE, COUNTING):
            return self.phase
        self.n += 1
        mag = math.sqrt(gx * gx + gy * gy + gz * gz)
        m = self.motion_hp.step(mag)
        self.motion_pow += (m * m - self.motion_pow) / (0.5 * FS)

        counting = self.phase == COUNTING and not self.moving
        t = self.counted / FS
        for axis, v in zip(self.axes, (gx, gy, gz)):
            axis.update(v, t, counting)

        if self.phase == SETTLE:
            if self.n >= SETTLE_S * FS:
                self.phase = COUNTING
        else:
            if counting:
                self.counted += 1
            else:
                self.moving_n += 1
            if self.moving_n > MAX_MOTION_S * FS:
                self.phase = ABORTED
            elif self.counted >= COUNT_S * FS:
                self.result = self.best.count
                self.phase = RESULT
        return self.phase
