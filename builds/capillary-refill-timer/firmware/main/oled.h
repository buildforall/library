#pragma once
#include <stdbool.h>
#include "driver/i2c_master.h"

// SSD1306 128x64 over I2C, with a frame buffer and a 6x8 font.
esp_err_t oled_init(i2c_master_bus_handle_t bus);
void oled_clear(void);
void oled_text(int x, int y, const char *s);
void oled_rect(int x, int y, int w, int h, bool fill);
void oled_vline(int x, int y, int h);
void oled_show(void);
