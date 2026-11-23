// Spirometry from mesh pressure drop. Header-only and free of ESP-IDF, so
// tests/ can run it on a computer.
//
// Flow = dP / R, where R (Pa per L/s) comes from a 3 L syringe calibration:
// integral(dP dt) over the stroke = R * 3 L. FEV1 uses back-extrapolated time
// zero (ATS/ERS 2019); FEV1/FVC below 0.70 is flagged as possible obstruction.

#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace spiro {

constexpr float kSampleHz = 200.0f;
constexpr float kDt = 1.0f / kSampleHz;
constexpr float kStartLps = 0.20f;    // flow that starts a recording
constexpr float kEndLps = 0.025f;     // flow below this for 1 s ends it
constexpr int kMaxSamples = 3000;     // 15 s
constexpr float kLowRatio = 0.70f;

// Body temperature and pressure, saturated: corrects ambient-air volume to
// what the lungs held. Ambient air assumed 50 % RH at 101.3 kPa.
inline float btps(float ambient_c) {
    float p_h2o = 0.5f * 0.6108f * std::exp(17.27f * ambient_c / (ambient_c + 237.3f));
    return (310.15f / (273.15f + ambient_c)) * ((101.3f - p_h2o) / (101.3f - 6.28f));
}

class Recording {
public:
    enum class State { Waiting, Recording, Done, Full };

    // raw_pa: syringe mode, integrate pressure instead of computing flow.
    void reset(bool raw_pa, float resistance, float btps_factor) {
        raw_ = raw_pa;
        r_ = resistance;
        k_ = btps_factor;
        n_ = 0;
        quiet_ = 0;
        pa_integral_ = 0;
        state_ = State::Waiting;
    }

    // One zeroed pressure sample, every kDt seconds.
    State push(float pa) {
        if (state_ == State::Done || state_ == State::Full) return state_;
        float q = (raw_ || r_ <= 0) ? 0.0f : std::max(0.0f, pa / r_ * k_);
        if (state_ == State::Waiting) {
            bool go = raw_ ? pa > 2.0f : q > kStartLps;
            if (!go) return state_;
            state_ = State::Recording;
        }
        flow_[n_] = q;
        if (raw_) pa_integral_ += std::max(0.0f, pa) * kDt;
        vol_[n_] = n_ ? vol_[n_ - 1] + 0.5f * (q + flow_[n_ - 1]) * kDt : q * kDt;
        n_++;
        bool low = raw_ ? pa < 0.5f : q < kEndLps;
        quiet_ = low ? quiet_ + 1 : 0;
        if (quiet_ > kSampleHz) state_ = State::Done;   // 1 s of no flow ends the blow
        else if (n_ >= kMaxSamples) state_ = State::Full;
        return state_;
    }

    State state() const { return state_; }
    int size() const { return n_; }
    double pa_integral() const { return pa_integral_; }
    const float *flow() const { return flow_.data(); }
    const float *volume() const { return vol_.data(); }

private:
    bool raw_ = false;
    float r_ = 0, k_ = 1;
    int n_ = 0, quiet_ = 0;
    double pa_integral_ = 0;
    State state_ = State::Waiting;
    std::array<float, kMaxSamples> flow_{}, vol_{};
};

struct Result {
    float fev1, fvc, ratio, pef, extrapolated;
    bool slow_start;   // back-extrapolated volume above 5 % of FVC or 100 mL
    bool low_ratio() const { return ratio < kLowRatio; }
};

// Back-extrapolation: the tangent to the volume-time curve at its steepest
// point (peak flow, smoothed over 80 ms) crosses zero volume at time zero.
inline Result analyse(const float *flow, const float *vol, int n) {
    int i_max = 0;
    float pef = 0;
    for (int i = 16; i < n; i++) {
        float q = 0;
        for (int j = i - 16; j < i; j++) q += flow[j];
        q /= 16;
        if (q > pef) { pef = q; i_max = i - 8; }
    }
    float t0 = i_max * kDt - vol[i_max] / std::max(flow[i_max], 0.01f);
    int iz = std::clamp(static_cast<int>(t0 / kDt), 0, n - 1);
    float extrap = vol[iz];
    int i1 = std::clamp(static_cast<int>((t0 + 1.0f) / kDt), 0, n - 1);
    Result r{};
    r.fev1 = vol[i1] - extrap;
    r.fvc = vol[n - 1] - extrap;
    r.ratio = r.fev1 / std::max(r.fvc, 0.01f);
    r.pef = pef;
    r.extrapolated = extrap;
    r.slow_start = extrap > std::max(0.05f * r.fvc, 0.100f);
    return r;
}

}  // namespace spiro
