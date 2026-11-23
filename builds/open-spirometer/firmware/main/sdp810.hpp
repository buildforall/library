// Sensirion SDP810-500Pa differential pressure sensor.
#pragma once

#include "driver/i2c_master.h"

class Sdp810 {
public:
    esp_err_t begin(i2c_master_bus_handle_t bus);
    // Latest averaged reading. False on a bus or CRC error.
    bool read(float &pa, float &celsius);

private:
    esp_err_t command(uint16_t cmd);
    static uint8_t crc8(const uint8_t *d, int n);
    i2c_master_dev_handle_t dev_ = nullptr;
};
