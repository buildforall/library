#include "crt.h"

#include <math.h>
#include <string.h>

static void enter(crt_t *c, crt_phase_t p, uint32_t now_ms)
{
    c->phase = p;
    c->t_phase = now_ms;
}

void crt_start(crt_t *c, uint32_t now_ms)
{
    memset(c, 0, sizeof *c);
    enter(c, CRT_BASELINE, now_ms);
}

crt_phase_t crt_step(crt_t *c, uint32_t now_ms, int fsr_mv, float ir)
{
    uint32_t dt = now_ms - c->t_phase;

    switch (c->phase) {
    case CRT_BASELINE:
        c->acc += ir;
        c->n++;
        if (dt >= CRT_BASELINE_MS) {
            c->base = (float)(c->acc / (c->n ? c->n : 1));
            enter(c, CRT_PRESS, now_ms);
        }
        break;

    case CRT_PRESS: {
        bool in_band = fsr_mv >= CRT_FSR_LOW_MV && fsr_mv <= CRT_FSR_HIGH_MV;
        if (in_band && !c->in_band_since)
            c->in_band_since = now_ms ? now_ms : 1;
        // Brief overshoot is forgiven; dropping well below the band restarts the hold.
        if (!in_band && fsr_mv < CRT_FSR_LOW_MV - 150)
            c->in_band_since = 0;
        if (c->in_band_since && now_ms - c->in_band_since >= CRT_PRESS_MS)
            enter(c, CRT_WAIT_RELEASE, now_ms);
        else if (dt > CRT_PRESS_GIVEUP_MS)
            enter(c, CRT_NO_PRESS, now_ms);
        break;
    }

    case CRT_WAIT_RELEASE:
        if (fsr_mv <= CRT_FSR_RELEASE_MV) {
            c->t_release = now_ms;
            c->at_release = ir;
            c->tolerance = fabsf(ir - c->base) * (1.0f - CRT_RECOVERY);
            c->ok_run = 0;
            enter(c, CRT_TIMING, now_ms);
        }
        break;

    case CRT_TIMING:
        // Three consecutive samples inside the tolerance end the refill.
        if (fabsf(ir - c->base) <= c->tolerance) {
            if (++c->ok_run >= 3) {
                c->crt_ms = now_ms - c->t_release;
                enter(c, CRT_DONE, now_ms);
            }
        } else {
            c->ok_run = 0;
        }
        if (c->phase == CRT_TIMING && dt >= CRT_TIMEOUT_MS) {
            c->crt_ms = 0;
            enter(c, CRT_DONE, now_ms);
        }
        break;

    case CRT_DONE:
    case CRT_NO_PRESS:
        break;
    }
    return c->phase;
}

int crt_hold_seconds_left(const crt_t *c, uint32_t now_ms)
{
    if (c->phase != CRT_PRESS || !c->in_band_since)
        return 0;
    uint32_t held = now_ms - c->in_band_since;
    return held >= CRT_PRESS_MS ? 0 : (int)((CRT_PRESS_MS - held) / 1000 + 1);
}

crt_class_t crt_classify(uint32_t crt_ms)
{
    if (crt_ms == 0 || crt_ms >= 3000)
        return CRT_PROLONGED;
    if (crt_ms > 2000)
        return CRT_BORDERLINE;
    return CRT_NORMAL;
}
