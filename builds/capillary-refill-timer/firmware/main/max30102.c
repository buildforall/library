#include "max30102.h"

#include "esp_check.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define ADDR          0x57
#define FIFO_WR_PTR   0x04
#define OVF_COUNTER   0x05
#define FIFO_RD_PTR   0x06
#define FIFO_DATA     0x07
#define FIFO_CONFIG   0x08
#define MODE_CONFIG   0x09
#define SPO2_CONFIG   0x0A
#define LED1_PA       0x0C   // red
#define LED2_PA       0x0D   // IR
#define PART_ID       0xFF

static i2c_master_dev_handle_t dev;

static esp_err_t wr(uint8_t reg, uint8_t val)
{
    uint8_t b[2] = {reg, val};
    return i2c_master_transmit(dev, b, 2, 50);
}

static esp_err_t rd(uint8_t reg, uint8_t *out, size_t n)
{
    return i2c_master_transmit_receive(dev, &reg, 1, out, n, 50);
}

esp_err_t max30102_init(i2c_master_bus_handle_t bus, uint8_t led_current)
{
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = ADDR,
        .scl_speed_hz = 400000,
    };
    ESP_RETURN_ON_ERROR(i2c_master_bus_add_device(bus, &cfg, &dev), "max30102", "add");

    uint8_t id = 0;
    ESP_RETURN_ON_ERROR(rd(PART_ID, &id, 1), "max30102", "id");
    if (id != 0x15)
        return ESP_ERR_NOT_FOUND;

    ESP_RETURN_ON_ERROR(wr(MODE_CONFIG, 0x40), "max30102", "reset");
    vTaskDelay(pdMS_TO_TICKS(10));
    // 4-sample averaging, FIFO rollover, almost-full at 17 free
    ESP_RETURN_ON_ERROR(wr(FIFO_CONFIG, 0x5F), "max30102", "fifo");
    // ADC range 16384 nA, 400 samples/s (100/s after averaging), 411 us pulses
    ESP_RETURN_ON_ERROR(wr(SPO2_CONFIG, 0x6F), "max30102", "spo2");
    ESP_RETURN_ON_ERROR(wr(LED1_PA, led_current), "max30102", "red");
    ESP_RETURN_ON_ERROR(wr(LED2_PA, led_current), "max30102", "ir");
    ESP_RETURN_ON_ERROR(wr(FIFO_WR_PTR, 0), "max30102", "wp");
    ESP_RETURN_ON_ERROR(wr(OVF_COUNTER, 0), "max30102", "ovf");
    ESP_RETURN_ON_ERROR(wr(FIFO_RD_PTR, 0), "max30102", "rp");
    return wr(MODE_CONFIG, 0x03);   // SpO2 mode: red and IR
}

int max30102_read_ir(uint32_t *ir, int max)
{
    uint8_t wp, rp;
    if (rd(FIFO_WR_PTR, &wp, 1) != ESP_OK || rd(FIFO_RD_PTR, &rp, 1) != ESP_OK)
        return 0;
    int n = (wp - rp) & 0x1F;
    if (n > max)
        n = max;
    for (int i = 0; i < n; i++) {
        uint8_t s[6];   // red[3], ir[3], 18-bit big-endian
        if (rd(FIFO_DATA, s, 6) != ESP_OK)
            return i;
        ir[i] = (((uint32_t)s[3] << 16) | ((uint32_t)s[4] << 8) | s[5]) & 0x3FFFF;
    }
    return n;
}
