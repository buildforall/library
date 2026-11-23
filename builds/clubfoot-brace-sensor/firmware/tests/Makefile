# Host tests for the wear log:  make -C tests
CFLAGS = -std=c11 -Wall -Wextra -Werror -O2 -I../src

test_wearlog: test_wearlog.c ../src/wearlog.c ../src/wearlog.h
	$(CC) $(CFLAGS) -o $@ test_wearlog.c ../src/wearlog.c
	./$@

.PHONY: clean
clean:
	rm -f test_wearlog
