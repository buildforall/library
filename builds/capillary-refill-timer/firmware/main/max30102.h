#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "driver/i2c_master.h"

// MAX30102 / MAX30105 pulse-oximetry front end, red + IR mode.
esp_err_t max30102_init(i2c_master_bus_handle_t bus, uint8_t led_current);

// Drains the FIFO. Returns the number of samples read (0..32) and writes the
// IR values to ir[], newest last.
int max30102_read_ir(uint32_t *ir, int max);
