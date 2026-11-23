// Synthetic blows through the spirometry maths:  make -C tests
#include <cassert>
#include <cmath>
#include <cstdio>

#include "spirometry.hpp"

using namespace spiro;

// Forced expiration as a single exponential emptying: V(t) = FVC * (1 - e^(-t/tau)).
// Flow is converted to mesh pressure with resistance R, before BTPS.
static Result blow(float fvc, float tau, float r = 120.0f, float delay_s = 0.3f) {
    static Recording rec;
    rec.reset(false, r, 1.0f);
    for (int i = 0; i < 20 * kSampleHz; i++) {
        float t = i * kDt - delay_s;
        float q = t < 0 ? 0 : fvc / tau * std::exp(-t / tau);
        auto s = rec.push(q * r);
        if (s == Recording::State::Done || s == Recording::State::Full) break;
    }
    assert(rec.state() == Recording::State::Done);
    return analyse(rec.flow(), rec.volume(), rec.size());
}

int main() {
    // Healthy: FVC 4 L, tau 0.35 s, so FEV1/FVC = 1 - e^(-1/0.35) ~ 0.94
    Result healthy = blow(4.0f, 0.35f);
    std::printf("healthy:     FEV1 %.2f  FVC %.2f  ratio %.2f  PEF %.1f\n", healthy.fev1, healthy.fvc,
                healthy.ratio, healthy.pef);
    assert(std::fabs(healthy.fvc - 4.0f) < 0.12f);
    assert(!healthy.low_ratio());
    assert(!healthy.slow_start);

    // Obstructed: tau 1.2 s, FEV1/FVC = 1 - e^(-1/1.2) ~ 0.57
    Result obstructed = blow(3.0f, 1.2f);
    std::printf("obstructed:  FEV1 %.2f  FVC %.2f  ratio %.2f  PEF %.1f\n", obstructed.fev1,
                obstructed.fvc, obstructed.ratio, obstructed.pef);
    assert(obstructed.low_ratio());
    assert(std::fabs(obstructed.ratio - 0.57f) < 0.06f);

    // Syringe mode integrates pressure: integral = R * volume
    Recording syringe;
    syringe.reset(true, 0, 1.0f);
    const float r = 95.0f;
    for (int i = 0; i < 6 * kSampleHz; i++) {
        float t = i * kDt;
        float q = (t > 0.2f && t < 2.2f) ? 1.5f : 0.0f;   // 1.5 L/s for 2 s = 3 L
        if (syringe.push(q * r) == Recording::State::Done) break;
    }
    std::printf("syringe:     R %.1f (expected %.1f)\n", syringe.pa_integral() / 3.0, r);
    assert(std::fabs(syringe.pa_integral() / 3.0 - r) < 2.0);

    // BTPS at 22 C: 1.091 in the standard tables (saturated air); 1.106 at the
    // 50 % humidity the firmware assumes.
    assert(std::fabs(btps(22.0f) - 1.106f) < 0.005f);

    std::puts("spirometry: all tests passed");
    return 0;
}
