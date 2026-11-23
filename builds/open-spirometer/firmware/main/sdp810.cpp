#include "sdp810.hpp"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace {
constexpr uint8_t kAddress = 0x25;
constexpr uint16_t kStop = 0x3FF9;
constexpr uint16_t kContinuousAveraged = 0x3615;   // differential pressure, averaged
}  // namespace

esp_err_t Sdp810::begin(i2c_master_bus_handle_t bus) {
    i2c_device_config_t cfg = {};
    cfg.dev_addr_length = I2C_ADDR_BIT_LEN_7;
    cfg.device_address = kAddress;
    cfg.scl_speed_hz = 400000;
    esp_err_t err = i2c_master_bus_add_device(bus, &cfg, &dev_);
    if (err != ESP_OK) return err;
    command(kStop);   // in case a measurement is still running from before a reset
    vTaskDelay(pdMS_TO_TICKS(2));
    err = command(kContinuousAveraged);
    vTaskDelay(pdMS_TO_TICKS(20));
    return err;
}

esp_err_t Sdp810::command(uint16_t cmd) {
    uint8_t b[2] = {static_cast<uint8_t>(cmd >> 8), static_cast<uint8_t>(cmd & 0xFF)};
    return i2c_master_transmit(dev_, b, 2, 20);
}

uint8_t Sdp810::crc8(const uint8_t *d, int n) {
    uint8_t c = 0xFF;
    for (int i = 0; i < n; i++) {
        c ^= d[i];
        for (int b = 0; b < 8; b++) c = (c & 0x80) ? (c << 1) ^ 0x31 : c << 1;
    }
    return c;
}

bool Sdp810::read(float &pa, float &celsius) {
    uint8_t b[9];
    if (i2c_master_receive(dev_, b, sizeof b, 20) != ESP_OK) return false;
    for (int i = 0; i < 9; i += 3)
        if (crc8(b + i, 2) != b[i + 2]) return false;
    int16_t dp = static_cast<int16_t>((b[0] << 8) | b[1]);
    int16_t t = static_cast<int16_t>((b[3] << 8) | b[4]);
    int16_t scale = static_cast<int16_t>((b[6] << 8) | b[7]);
    pa = static_cast<float>(dp) / (scale ? scale : 60);
    celsius = t / 200.0f;
    return true;
}
