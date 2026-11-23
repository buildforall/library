// pio test -e native
#include <math.h>
#include <unity.h>

#include "FreezeIndex.h"

using namespace fog;

static const float kPi = 3.14159265f;

// |a| of a shank: 1 g plus a gait component at `stepHz`, optionally with
// trembling at `trembleHz` (the 3-8 Hz "freeze" band).
static float shank(float t, float stepHz, float stepAmp, float trembleHz, float trembleAmp) {
    return 1.0f + stepAmp * sinf(2 * kPi * stepHz * t) + trembleAmp * sinf(2 * kPi * trembleHz * t);
}

static Analysis feedSeconds(FreezeIndex &fi, float seconds, float stepHz, float stepAmp,
                            float trembleHz, float trembleAmp, float t0 = 0) {
    for (int i = 0; i < (int)(seconds * kSampleHz); i++) {
        float t = t0 + i / kSampleHz;
        fi.push(shank(t, stepHz, stepAmp, trembleHz, trembleAmp));
    }
    return fi.last();
}

void setUp() {}
void tearDown() {}

void test_walking_is_not_a_freeze() {
    FreezeIndex fi;
    Analysis a = feedSeconds(fi, 10, 1.8f, 0.4f, 6.0f, 0.02f);
    TEST_ASSERT_TRUE(a.moving);
    TEST_ASSERT_LESS_THAN_FLOAT(1.0f, a.freezeIndex);
}

void test_trembling_in_place_is_a_freeze() {
    FreezeIndex fi;
    Analysis a = feedSeconds(fi, 10, 1.8f, 0.05f, 5.5f, 0.35f);
    TEST_ASSERT_TRUE(a.moving);
    TEST_ASSERT_GREATER_THAN_FLOAT(2.0f, a.freezeIndex);
}

void test_standing_still_is_ignored() {
    FreezeIndex fi;
    Analysis a = feedSeconds(fi, 10, 1.8f, 0.005f, 5.5f, 0.01f);
    TEST_ASSERT_FALSE(a.moving);
}

void test_cadence_follows_walking() {
    FreezeIndex fi;
    feedSeconds(fi, 60, 1.8f, 0.4f, 0, 0);   // 108 steps per minute
    TEST_ASSERT_FLOAT_WITHIN(4.0f, 108.0f, fi.cadence());
}

void test_cue_runs_through_tail_and_logs_episode() {
    FreezeIndex fi;
    CueController cue;
    uint32_t ms = 0, ms0 = 0;
    bool ended = false;
    auto run = [&](float seconds, float stepAmp, float trembleAmp) {
        for (int i = 0; i < (int)(seconds * kSampleHz); i++) {
            ms = (uint32_t)(i * 1000 / kSampleHz) + ms0;
            if (fi.push(shank(ms / 1000.0f, 1.8f, stepAmp, 5.5f, trembleAmp)))
                ended |= cue.update(fi.last(), ms);
        }
        ms0 = ms;
    };
    run(10, 0.4f, 0.02f);   // walking
    TEST_ASSERT_FALSE(cue.cueOn());
    run(8, 0.05f, 0.35f);   // freeze
    TEST_ASSERT_TRUE(cue.cueOn());
    run(10, 0.4f, 0.02f);   // walking again, past the tail
    TEST_ASSERT_FALSE(cue.cueOn());
    TEST_ASSERT_TRUE(ended);
    TEST_ASSERT_EQUAL(1, cue.count);
    TEST_ASSERT_INT_WITHIN(4, 8, cue.episodes[0].durationS);
}

void test_motor_pulses_at_cadence() {
    CueController cue;
    int pulses = 0;
    bool was = false;
    for (uint32_t t = 0; t < 60000; t += 10) {
        bool on = cue.motor(true, 100.0f, t);
        if (on && !was) pulses++;
        was = on;
    }
    TEST_ASSERT_INT_WITHIN(1, 100, pulses);
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_walking_is_not_a_freeze);
    RUN_TEST(test_trembling_in_place_is_a_freeze);
    RUN_TEST(test_standing_still_is_ignored);
    RUN_TEST(test_cadence_follows_walking);
    RUN_TEST(test_cue_runs_through_tail_and_logs_episode);
    RUN_TEST(test_motor_pulses_at_cadence);
    return UNITY_END();
}
