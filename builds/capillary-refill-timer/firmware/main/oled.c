#include "oled.h"

#include <string.h>
#include "font6x8.h"

#define W 128
#define H 64

static i2c_master_dev_handle_t dev;
static uint8_t fb[1 + W * H / 8];   // fb[0] is the 0x40 data control byte

static esp_err_t cmds(const uint8_t *c, size_t n)
{
    uint8_t b[32];
    b[0] = 0x00;
    memcpy(b + 1, c, n);
    return i2c_master_transmit(dev, b, n + 1, 50);
}

esp_err_t oled_init(i2c_master_bus_handle_t bus)
{
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = 0x3C,
        .scl_speed_hz = 400000,
    };
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, &dev);
    if (err != ESP_OK)
        return err;
    static const uint8_t init[] = {
        0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00,
        0xA1, 0xC8, 0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6, 0xAF,
    };
    oled_clear();
    return cmds(init, sizeof init);
}

void oled_clear(void)
{
    memset(fb + 1, 0, sizeof fb - 1);
}

static void px(int x, int y)
{
    if (x >= 0 && x < W && y >= 0 && y < H)
        fb[1 + x + (y / 8) * W] |= 1 << (y & 7);
}

void oled_text(int x, int y, const char *s)
{
    for (; *s; s++, x += 6) {
        char ch = (*s < 0x20 || *s > 0x7E) ? '?' : *s;
        const uint8_t *g = FONT6X8[ch - 0x20];
        for (int cx = 0; cx < 6; cx++)
            for (int cy = 0; cy < 8; cy++)
                if (g[cx] >> cy & 1)
                    px(x + cx, y + cy);
    }
}

void oled_rect(int x, int y, int w, int h, bool fill)
{
    for (int i = 0; i < w; i++)
        for (int j = 0; j < h; j++)
            if (fill || i == 0 || j == 0 || i == w - 1 || j == h - 1)
                px(x + i, y + j);
}

void oled_vline(int x, int y, int h)
{
    for (int j = 0; j < h; j++)
        px(x, y + j);
}

void oled_show(void)
{
    static const uint8_t window[] = {0x21, 0x00, W - 1, 0x22, 0x00, H / 8 - 1};
    cmds(window, sizeof window);
    fb[0] = 0x40;
    i2c_master_transmit(dev, fb, sizeof fb, 100);
}
