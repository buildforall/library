// Freeze-of-gait detection from shank acceleration.
//
// Freeze index (Moore et al., 2008): power in the 3-8 Hz "freeze" band divided
// by power in the 0.5-3 Hz "locomotion" band, over a 4 s window updated every
// 0.5 s. No Arduino headers, so the same code runs in the unit tests on a PC.

#pragma once
#include <stddef.h>
#include <stdint.h>

namespace fog {

constexpr float kSampleHz = 64.0f;
constexpr int kWindow = 256;   // 4 s
constexpr int kHop = 32;       // 0.5 s
constexpr float kBinHz = kSampleHz / kWindow;
constexpr float kMinPower = 0.02f;   // below this the wearer is standing still

struct Analysis {
    float freezeIndex = 0;
    float power = 0;
    bool moving = false;
};

class FreezeIndex {
public:
    // Push one |acceleration| sample in g. Returns true when a new analysis is ready.
    bool push(float g);
    const Analysis &last() const { return last_; }
    float cadence() const { return cadence_; }   // steps per minute, learned while walking

private:
    void analyse();
    float ring_[kWindow] = {};
    int head_ = 0, filled_ = 0, sinceHop_ = 0;
    float re_[kWindow], im_[kWindow];
    float cadence_ = 100.0f;
    Analysis last_;
};

// Turns analyses into a cue (on/off) with a tail, and records episodes.
class CueController {
public:
    struct Episode {
        uint32_t startS;
        uint16_t durationS;
    };
    static constexpr int kMaxEpisodes = 64;
    static constexpr uint32_t kTailMs = 3000;

    float threshold = 2.0f;   // per patient, set at the clinic over Bluetooth

    // Returns true when an episode has just ended (and been logged).
    bool update(const Analysis &a, uint32_t nowMs);
    bool cueOn() const { return cueOn_; }

    // Motor drive for a cue pulsing at `cadence` steps per minute.
    bool motor(bool active, float cadence, uint32_t nowMs);

    Episode episodes[kMaxEpisodes];
    int count = 0;

private:
    bool cueOn_ = false;
    uint32_t freezeStart_ = 0, lastAbove_ = 0, lastPulse_ = 0;
};

void fft(float *re, float *im, int n);

}  // namespace fog
