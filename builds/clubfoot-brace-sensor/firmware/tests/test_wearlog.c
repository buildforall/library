/* Synthetic wear patterns through the summary. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "wearlog.h"

static char out[512];
static size_t used;

static void collect(const struct wear_summary *s, void *ctx)
{
	(void)ctx;
	used += wear_format(s, out + used, sizeof(out) - used);
}

static const char *summarise(const uint8_t *log, size_t n)
{
	used = 0;
	out[0] = 0;
	wear_summarise(log, n, collect, NULL);
	return out;
}

int main(void)
{
	static uint8_t log[3 * WEAR_SAMPLES_PER_DAY];

	/* Encoding round-trips to the nearest 0.25 C and clamps at both ends. */
	assert(wear_decode(wear_encode(33.1f)) == 33.0f);
	assert(wear_decode(wear_encode(-5.0f)) == 10.0f);
	assert(wear_decode(wear_encode(99.0f)) == 73.5f);

	/* Day 1: 23 h on the foot (34 C), 1 h off (22 C). */
	for (int i = 0; i < WEAR_SAMPLES_PER_DAY; i++)
		log[i] = wear_encode(i < 138 ? 34.0f : 22.0f);
	/* Day 2: worn 12 h, but the foot cools to 29 C for an hour: hysteresis keeps it "worn". */
	for (int i = 0; i < WEAR_SAMPLES_PER_DAY; i++) {
		float t = i < 66 ? 34.0f : i < 72 ? 29.0f : 22.0f;
		log[WEAR_SAMPLES_PER_DAY + i] = wear_encode(t);
	}
	/* Day 3, partial: 3 h worn. */
	for (int i = 0; i < 18; i++)
		log[2 * WEAR_SAMPLES_PER_DAY + i] = wear_encode(35.0f);

	const char *s = summarise(log, 2 * WEAR_SAMPLES_PER_DAY + 18);
	printf("%s", s);
	assert(strcmp(s, "1,23.0\n2,12.0\n3,3.0 (partial)\n") == 0);

	/* A brace left in a warm room (29 C) never counts as worn. */
	for (int i = 0; i < WEAR_SAMPLES_PER_DAY; i++)
		log[i] = wear_encode(29.0f);
	assert(strcmp(summarise(log, WEAR_SAMPLES_PER_DAY), "1,0.0\n") == 0);

	puts("wearlog: all tests passed");
	return 0;
}
