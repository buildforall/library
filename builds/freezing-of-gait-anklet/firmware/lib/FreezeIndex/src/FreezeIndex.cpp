#include "FreezeIndex.h"

#include <math.h>

namespace fog {

namespace {
constexpr float kPi = 3.14159265358979f;
constexpr uint32_t kPulseMs = 120;

float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
}  // namespace

void fft(float *x, float *y, int n) {   // in-place iterative radix-2
    for (int i = 1, j = 0; i < n; i++) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
            float t = x[i]; x[i] = x[j]; x[j] = t;
            t = y[i]; y[i] = y[j]; y[j] = t;
        }
    }
    for (int len = 2; len <= n; len <<= 1) {
        float ang = -2 * kPi / len, wr = cosf(ang), wi = sinf(ang);
        for (int i = 0; i < n; i += len) {
            float cr = 1, ci = 0;
            for (int k = 0; k < len / 2; k++) {
                int a = i + k, b = i + k + len / 2;
                float tr = x[b] * cr - y[b] * ci, ti = x[b] * ci + y[b] * cr;
                x[b] = x[a] - tr; y[b] = y[a] - ti;
                x[a] += tr; y[a] += ti;
                float nr = cr * wr - ci * wi;
                ci = cr * wi + ci * wr;
                cr = nr;
            }
        }
    }
}

bool FreezeIndex::push(float g) {
    ring_[head_] = g;
    head_ = (head_ + 1) % kWindow;
    if (filled_ < kWindow) filled_++;
    if (++sinceHop_ < kHop || filled_ < kWindow) return false;
    sinceHop_ = 0;
    analyse();
    return true;
}

void FreezeIndex::analyse() {
    float mean = 0;
    for (float v : ring_) mean += v;
    mean /= kWindow;
    for (int i = 0; i < kWindow; i++) {   // oldest sample first, Hann window
        float w = 0.5f - 0.5f * cosf(2 * kPi * i / (kWindow - 1));
        re_[i] = (ring_[(head_ + i) % kWindow] - mean) * w;
        im_[i] = 0;
    }
    fft(re_, im_, kWindow);

    float pLoc = 0, pFrz = 0, peak = 0;
    int peakBin = 0;
    for (int k = 1; k < kWindow / 2; k++) {
        float f = k * kBinHz, p = re_[k] * re_[k] + im_[k] * im_[k];
        if (f >= 0.5f && f < 3.0f) {
            pLoc += p;
            if (p > peak) { peak = p; peakBin = k; }
        } else if (f >= 3.0f && f <= 8.0f) {
            pFrz += p;
        }
    }
    last_.power = (pLoc + pFrz) / kWindow;
    last_.freezeIndex = pFrz / (pLoc > 1e-9f ? pLoc : 1e-9f);
    last_.moving = last_.power > kMinPower;

    // Normal walking: follow the wearer's cadence so cues match their rhythm.
    // The magnitude signal peaks once per step.
    if (last_.moving && last_.freezeIndex < 1.0f && peakBin)
        cadence_ += (clampf(peakBin * kBinHz * 60.0f, 70.0f, 140.0f) - cadence_) * 0.1f;
}

bool CueController::update(const Analysis &a, uint32_t nowMs) {
    bool freezing = a.moving && a.freezeIndex > threshold;
    if (freezing) {
        if (!cueOn_) { freezeStart_ = nowMs; cueOn_ = true; }
        lastAbove_ = nowMs;
        return false;
    }
    if (cueOn_ && nowMs - lastAbove_ > kTailMs) {
        cueOn_ = false;
        if (count < kMaxEpisodes) {
            episodes[count++] = {freezeStart_ / 1000, (uint16_t)((lastAbove_ - freezeStart_) / 1000)};
        }
        return true;
    }
    return false;
}

bool CueController::motor(bool active, float cadence, uint32_t nowMs) {
    uint32_t period = (uint32_t)(60000.0f / cadence);
    if (active && nowMs - lastPulse_ >= period) lastPulse_ = nowMs;
    return active && (nowMs - lastPulse_) < kPulseMs;
}

}  // namespace fog
