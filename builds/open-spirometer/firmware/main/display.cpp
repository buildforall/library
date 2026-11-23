#include "display.hpp"

#include <cstring>

#include "font6x8.h"

esp_err_t Display::begin(i2c_master_bus_handle_t bus) {
    i2c_device_config_t cfg = {};
    cfg.dev_addr_length = I2C_ADDR_BIT_LEN_7;
    cfg.device_address = 0x3C;
    cfg.scl_speed_hz = 400000;
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, &dev_);
    if (err != ESP_OK) return err;
    static const uint8_t init[] = {
        0x00,   // command stream
        0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00,
        0xA1, 0xC8, 0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6, 0xAF,
    };
    return i2c_master_transmit(dev_, init, sizeof init, 50);
}

void Display::clear() { std::memset(fb_ + 1, 0, sizeof fb_ - 1); }

void Display::text(int x, int y, const char *s) {
    for (; *s && x <= 122; s++, x += 6) {
        char ch = (*s < 0x20 || *s > 0x7E) ? '?' : *s;
        const uint8_t *g = FONT6X8[ch - 0x20];
        for (int cx = 0; cx < 6; cx++)
            for (int cy = 0; cy < 8; cy++)
                if ((g[cx] >> cy) & 1) {
                    int px = x + cx, py = y + cy;
                    if (px < 128 && py < 64) fb_[1 + px + (py / 8) * 128] |= 1 << (py & 7);
                }
    }
}

void Display::flush() {
    static const uint8_t window[] = {0x00, 0x21, 0x00, 127, 0x22, 0x00, 7};
    i2c_master_transmit(dev_, window, sizeof window, 50);
    fb_[0] = 0x40;
    i2c_master_transmit(dev_, fb_, sizeof fb_, 100);
}

void Display::show(const char *title, std::initializer_list<const char *> lines, bool low_battery) {
    clear();
    text(0, 0, title);
    if (low_battery) text(110, 0, "LOW");
    int y = 16;
    for (const char *l : lines) {
        text(0, y, l);
        y += 12;
    }
    flush();
}
