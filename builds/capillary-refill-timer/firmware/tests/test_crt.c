// Synthetic presses through the refill state machine.
#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "crt.h"

// Simulated finger: IR rises while blanched, then returns exponentially.
// tau_ms sets how fast the colour comes back.
static crt_t run(float tau_ms, int press_mv, int press_ms)
{
    crt_t c;
    uint32_t t = 1000;
    crt_start(&c, t);
    const float base = 60000, blanched = 68000;
    uint32_t press_start = t + CRT_BASELINE_MS + 300;
    uint32_t release = press_start + press_ms;
    for (int i = 0; i < 6000; i++, t += 10) {
        int mv = (t >= press_start && t < release) ? press_mv : 0;
        float ir = base;
        if (t >= press_start && t < release)
            ir = blanched;
        else if (t >= release)
            ir = base + (blanched - base) * expf(-(float)(t - release) / tau_ms);
        crt_phase_t p = crt_step(&c, t, mv, ir);
        if (p == CRT_DONE || p == CRT_NO_PRESS)
            break;
    }
    return c;
}

int main(void)
{
    // 90 % recovery takes tau * ln(10)
    crt_t fast = run(600, 1500, 5200);
    assert(fast.phase == CRT_DONE);
    assert(fabsf(fast.crt_ms - 600 * logf(10)) < 60);
    assert(crt_classify(fast.crt_ms) == CRT_NORMAL);

    crt_t mid = run(1000, 1500, 5200);
    assert(crt_classify(mid.crt_ms) == CRT_BORDERLINE);

    crt_t slow = run(1600, 1500, 5200);
    assert(crt_classify(slow.crt_ms) == CRT_PROLONGED);

    crt_t never = run(20000, 1500, 5200);
    assert(never.phase == CRT_DONE && never.crt_ms == 0);
    assert(crt_classify(never.crt_ms) == CRT_PROLONGED);

    crt_t light = run(600, 700, 5200);    // below the force band: never counts
    assert(light.phase == CRT_NO_PRESS || light.crt_ms == 0);

    crt_t short_press = run(600, 1500, 3000);   // released before 5 s
    assert(short_press.phase != CRT_DONE || short_press.crt_ms == 0);

    printf("crt: all tests passed (normal %u ms, borderline %u ms, prolonged %u ms)\n",
           (unsigned)fast.crt_ms, (unsigned)mid.crt_ms, (unsigned)slow.crt_ms);
    return 0;
}
