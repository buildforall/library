# Host tests for the spirometry maths:  make -C tests
CXXFLAGS = -std=c++17 -Wall -Wextra -Werror -O2 -I../main

test_spirometry: test_spirometry.cpp ../main/spirometry.hpp
	$(CXX) $(CXXFLAGS) -o $@ test_spirometry.cpp
	./$@

.PHONY: clean
clean:
	rm -f test_spirometry
