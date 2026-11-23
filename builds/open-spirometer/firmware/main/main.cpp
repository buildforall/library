// Open spirometer, ESP-IDF (C++17) on an ESP32-C3 SuperMini.
//
// Pins: SDA 8, SCL 9, button 5, buzzer 7, battery divider 0.
//
// Calibrate once with a 3 L syringe: hold the button for 2 s while switching
// on, then push the full syringe through. The mesh resistance is kept in NVS.

#include <cstdio>
#include <cstring>

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/ledc.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs.h"
#include "nvs_flash.h"

#include "curve_service.hpp"
#include "display.hpp"
#include "sdp810.hpp"
#include "spirometry.hpp"

namespace {

constexpr gpio_num_t kSda = GPIO_NUM_8, kScl = GPIO_NUM_9, kButton = GPIO_NUM_5, kBuzzer = GPIO_NUM_7;
constexpr adc_channel_t kBattery = ADC_CHANNEL_0;   // GPIO0
constexpr const char *kTitle = "Spirometer";
const char *TAG = "spiro";

Sdp810 sensor;
Display display;
spiro::Recording rec;
adc_oneshot_unit_handle_t adc;
adc_cali_handle_t cali;

float resistance = 0;   // Pa per L/s; 0 until calibrated
float zero_pa = 0;
float ambient_c = 22;

uint32_t millis() { return static_cast<uint32_t>(esp_timer_get_time() / 1000); }
bool button_down() { return gpio_get_level(kButton) == 0; }

bool low_battery() {
    int mv = 0;
    adc_oneshot_get_calibrated_result(adc, cali, kBattery, &mv);
    return mv * 2 < 3450;
}

void show(std::initializer_list<const char *> lines) { display.show(kTitle, lines, low_battery()); }

void beep(uint32_t hz, uint32_t ms) {
    ledc_set_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0, hz);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 512);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    vTaskDelay(pdMS_TO_TICKS(ms));
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

void save_resistance(float r) {
    nvs_handle_t h;
    if (nvs_open("spiro", NVS_READWRITE, &h) != ESP_OK) return;
    uint32_t bits;
    std::memcpy(&bits, &r, sizeof bits);
    nvs_set_u32(h, "R", bits);
    nvs_commit(h);
    nvs_close(h);
}

float load_resistance() {
    nvs_handle_t h;
    uint32_t bits = 0;
    if (nvs_open("spiro", NVS_READONLY, &h) != ESP_OK) return 0;
    nvs_get_u32(h, "R", &bits);
    nvs_close(h);
    float r;
    std::memcpy(&r, &bits, sizeof r);
    return r;
}

// One second of no-flow readings: the pressure offset, and the air temperature.
void zero() {
    double acc = 0;
    int n = 0;
    float pa, tc;
    uint32_t t0 = millis();
    while (millis() - t0 < 1000) {
        vTaskDelay(pdMS_TO_TICKS(5));
        if (sensor.read(pa, tc)) {
            acc += pa;
            n++;
            ambient_c = tc;
        }
    }
    zero_pa = n ? static_cast<float>(acc / n) : 0;
}

// Samples at 200 Hz until the recording ends. False if nothing started within 15 s.
bool record(bool syringe) {
    rec.reset(syringe, resistance, spiro::btps(ambient_c));
    TickType_t wake = xTaskGetTickCount();
    uint32_t t0 = millis();
    float pa, tc;
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(1000 / spiro::kSampleHz));
        if (!sensor.read(pa, tc)) continue;
        auto s = rec.push(pa - zero_pa);
        if (s == spiro::Recording::State::Done || s == spiro::Recording::State::Full) return true;
        if (s == spiro::Recording::State::Waiting && millis() - t0 > 15000) return false;
    }
}

void calibrate_with_syringe() {
    show({"Syringe calibration", "Attach 3 L syringe.", "Zeroing..."});
    zero();
    show({"Push the full 3 L", "steadily through."});
    if (!record(true) || rec.pa_integral() <= 0) {
        show({"No flow seen.", "Restart to retry."});
        return;
    }
    resistance = static_cast<float>(rec.pa_integral() / 3.0);   // integral(dP dt) = R * volume
    save_resistance(resistance);
    char line[24];
    std::snprintf(line, sizeof line, "R = %.2f Pa.s/L", resistance);
    show({"Saved.", line});
    beep(2000, 200);
    vTaskDelay(pdMS_TO_TICKS(2500));
}

void measure() {
    show({"Zeroing, no flow..."});
    zero();
    show({"Breathe in fully,", "then BLAST out", "and keep going."});
    beep(2200, 150);
    if (!record(false) || rec.size() < spiro::kSampleHz) {
        show({"No blow detected.", "", "Press to retry."});
        return;
    }
    spiro::Result r = spiro::analyse(rec.flow(), rec.volume(), rec.size());

    char a[24], b[24], c[24];
    std::snprintf(a, sizeof a, "FEV1 %.2f L", r.fev1);
    std::snprintf(b, sizeof b, "FVC  %.2f L", r.fvc);
    std::snprintf(c, sizeof c, "Ratio %.2f PEF %.1f", r.ratio, r.pef);
    const char *d = r.slow_start ? "Slow start: repeat" : r.low_ratio() ? "LOW RATIO: refer" : "Ratio normal";
    show({a, b, c, d});
    beep(r.low_ratio() ? 2600 : 1500, 300);
    ESP_LOGI(TAG, "fev1,%.3f,fvc,%.3f,ratio,%.3f,pef,%.2f,extrap,%.3f,n,%d", r.fev1, r.fvc, r.ratio,
             r.pef, r.extrapolated, rec.size());
    curve_service::send(rec.volume(), rec.flow(), rec.size());
}

void init_hardware() {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }

    i2c_master_bus_config_t bus_cfg = {};
    bus_cfg.i2c_port = I2C_NUM_0;
    bus_cfg.sda_io_num = kSda;
    bus_cfg.scl_io_num = kScl;
    bus_cfg.clk_source = I2C_CLK_SRC_DEFAULT;
    bus_cfg.glitch_ignore_cnt = 7;
    bus_cfg.flags.enable_internal_pullup = true;
    i2c_master_bus_handle_t bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    ESP_ERROR_CHECK(display.begin(bus));

    gpio_config_t btn = {};
    btn.pin_bit_mask = 1ULL << kButton;
    btn.mode = GPIO_MODE_INPUT;
    btn.pull_up_en = GPIO_PULLUP_ENABLE;
    gpio_config(&btn);

    adc_oneshot_unit_init_cfg_t unit = {};
    unit.unit_id = ADC_UNIT_1;
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit, &adc));
    adc_oneshot_chan_cfg_t ch = {};
    ch.atten = ADC_ATTEN_DB_12;
    ch.bitwidth = ADC_BITWIDTH_DEFAULT;
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc, kBattery, &ch));
    adc_cali_curve_fitting_config_t cc = {};
    cc.unit_id = ADC_UNIT_1;
    cc.atten = ADC_ATTEN_DB_12;
    cc.bitwidth = ADC_BITWIDTH_DEFAULT;
    ESP_ERROR_CHECK(adc_cali_create_scheme_curve_fitting(&cc, &cali));

    ledc_timer_config_t t = {};
    t.speed_mode = LEDC_LOW_SPEED_MODE;
    t.duty_resolution = LEDC_TIMER_10_BIT;
    t.timer_num = LEDC_TIMER_0;
    t.freq_hz = 2000;
    t.clk_cfg = LEDC_AUTO_CLK;
    ESP_ERROR_CHECK(ledc_timer_config(&t));
    ledc_channel_config_t c = {};
    c.gpio_num = kBuzzer;
    c.speed_mode = LEDC_LOW_SPEED_MODE;
    c.channel = LEDC_CHANNEL_0;
    c.timer_sel = LEDC_TIMER_0;
    ESP_ERROR_CHECK(ledc_channel_config(&c));

    float pa, tc;
    if (sensor.begin(bus) != ESP_OK || !sensor.read(pa, tc)) {
        show({"Pressure sensor", "not found."});
        for (;;) vTaskDelay(portMAX_DELAY);
    }
}

}  // namespace

extern "C" void app_main() {
    init_hardware();
    resistance = load_resistance();

    uint32_t t0 = millis();
    while (button_down()) {
        if (millis() - t0 > 2000) {
            calibrate_with_syringe();
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    curve_service::start("BFA spirometer");
    show({resistance > 0 ? "Ready." : "NOT CALIBRATED", "Mouthpiece on,", "nose clip on.", "Press: zero + start"});

    for (;;) {
        if (!button_down()) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }
        while (button_down()) vTaskDelay(pdMS_TO_TICKS(5));
        if (resistance <= 0) {
            show({"Calibrate first:", "hold button while", "switching on."});
            continue;
        }
        measure();
    }
}
