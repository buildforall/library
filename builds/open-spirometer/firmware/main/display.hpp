// SSD1306 128x64 over I2C: four lines of text under a title.
#pragma once

#include <cstdint>
#include <initializer_list>

#include "driver/i2c_master.h"

class Display {
public:
    esp_err_t begin(i2c_master_bus_handle_t bus);
    // Title on top, up to four lines below, "LOW" at top right if asked.
    void show(const char *title, std::initializer_list<const char *> lines, bool low_battery);

private:
    void clear();
    void text(int x, int y, const char *s);
    void flush();
    i2c_master_dev_handle_t dev_ = nullptr;
    uint8_t fb_[1 + 128 * 64 / 8] = {};   // fb_[0] holds the 0x40 data control byte
};
