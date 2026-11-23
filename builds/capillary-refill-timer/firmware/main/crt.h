// Capillary refill measurement as a state machine.
//
// No ESP-IDF headers here: the same code is built for the board and, from
// tests/, on a computer with synthetic signals.

#pragma once
#include <stdbool.h>
#include <stdint.h>

// Force band at the FSR divider, in millivolts. Set with weights during bench
// calibration (README, step 6). Defaults correspond to roughly 1 to 2 kg.
#define CRT_FSR_LOW_MV      1100
#define CRT_FSR_HIGH_MV     2000
#define CRT_FSR_RELEASE_MV   250

#define CRT_BASELINE_MS     2000
#define CRT_PRESS_MS        5000
#define CRT_PRESS_GIVEUP_MS 30000
#define CRT_TIMEOUT_MS      10000
#define CRT_RECOVERY        0.90f   // CRT ends at 90 % recovery of the IR signal

typedef enum {
    CRT_BASELINE,       // finger at rest, averaging the IR level
    CRT_PRESS,          // waiting for a press held in the force band
    CRT_WAIT_RELEASE,   // press complete, waiting for the plunger to lift
    CRT_TIMING,         // released, timing the IR signal's return
    CRT_DONE,
    CRT_NO_PRESS,
} crt_phase_t;

typedef enum { CRT_NORMAL, CRT_BORDERLINE, CRT_PROLONGED } crt_class_t;

typedef struct {
    crt_phase_t phase;
    uint32_t t_phase;       // ms, start of the current phase
    double acc;
    uint32_t n;
    float base;             // resting IR level
    uint32_t in_band_since; // 0 when not in band
    float at_release;
    float tolerance;        // |IR - base| below this counts as recovered
    int ok_run;
    uint32_t t_release;
    uint32_t crt_ms;        // 0 if it never recovered within the timeout
} crt_t;

void crt_start(crt_t *c, uint32_t now_ms);

// Call every 10-20 ms with the current force (mV at the FSR divider) and the
// smoothed IR level. Returns the phase after this step.
crt_phase_t crt_step(crt_t *c, uint32_t now_ms, int fsr_mv, float ir);

// Seconds left in the held press, for the display. 0 if not in band.
int crt_hold_seconds_left(const crt_t *c, uint32_t now_ms);

crt_class_t crt_classify(uint32_t crt_ms);
