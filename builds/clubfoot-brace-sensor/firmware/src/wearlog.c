#include "wearlog.h"

#include <stdbool.h>
#include <stdio.h>

uint8_t wear_encode(float celsius)
{
	float v = (celsius - 10.0f) * 4.0f;

	if (v < 0.0f) {
		v = 0.0f;
	}
	if (v > 254.0f) {
		v = 254.0f;
	}
	return (uint8_t)(v + 0.5f);
}

float wear_decode(uint8_t b)
{
	return 10.0f + b / 4.0f;
}

void wear_summarise(const uint8_t *log, size_t n,
		    void (*emit)(const struct wear_summary *s, void *ctx), void *ctx)
{
	struct wear_summary s = {.day = 1};
	bool worn = false;

	for (size_t i = 0; i < n; i++) {
		float t = wear_decode(log[i]);

		if (!worn && t > WEAR_ON_C) {
			worn = true;
		} else if (worn && t < WEAR_OFF_C) {
			worn = false;
		}
		s.worn_samples += worn;
		if (++s.samples == WEAR_SAMPLES_PER_DAY) {
			emit(&s, ctx);
			s.day++;
			s.samples = 0;
			s.worn_samples = 0;
		}
	}
	if (s.samples) {
		emit(&s, ctx);
	}
}

int wear_format(const struct wear_summary *s, char *out, size_t cap)
{
	/* tenths of an hour, without pulling floating-point printf into the build */
	int tenths = (s->worn_samples * 10 + 3) / 6;

	return snprintf(out, cap, "%d,%d.%d%s\n", s->day, tenths / 10, tenths % 10,
			s->samples < WEAR_SAMPLES_PER_DAY ? " (partial)" : "");
}
