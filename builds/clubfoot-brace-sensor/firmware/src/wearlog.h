/*
 * Wear log for the clubfoot brace sensor.
 *
 * One byte per 10-minute sample: (T - 10 C) * 4, so 0.25 C steps from 10 C
 * to 73.5 C. Whether the brace was worn is decided at read-out, with
 * hysteresis: worn above 30.5 C, taken off below 28.0 C.
 *
 * No Zephyr headers here, so tests/ can build it on a computer.
 */

#pragma once
#include <stddef.h>
#include <stdint.h>

#define WEAR_SAMPLES_PER_DAY 144
#define WEAR_ON_C            30.5f
#define WEAR_OFF_C           28.0f

uint8_t wear_encode(float celsius);
float wear_decode(uint8_t b);

struct wear_summary {
	int day;          /* 1-based, counted from the first sample */
	int worn_samples; /* 10-minute samples counted as worn */
	int samples;      /* samples in this day, 144 unless partial */
};

/*
 * Walks the log and calls `emit` once per 24 h block (the last may be partial).
 * The hysteresis state carries across days, as it does on the child's foot.
 */
void wear_summarise(const uint8_t *log, size_t n,
		    void (*emit)(const struct wear_summary *s, void *ctx), void *ctx);

/* Formats one summary line, "3,21.5\n" or "4,6.0 (partial)\n". Returns length. */
int wear_format(const struct wear_summary *s, char *out, size_t cap);
