# Host tests for the refill state machine:  make -C tests
CFLAGS = -std=c11 -Wall -Wextra -Werror -O2 -I../main

test_crt: test_crt.c ../main/crt.c ../main/crt.h
	$(CC) $(CFLAGS) -o $@ test_crt.c ../main/crt.c -lm
	./$@

.PHONY: clean
clean:
	rm -f test_crt
