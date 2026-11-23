// Capillary refill timer, ESP-IDF on an ESP32-C3 SuperMini.
//
// The finger rests pad-down on the optical sensor. The clinician presses the
// nail with the force-sensing plunger, guided into a target band, for 5 s.
// After release the firmware times the infrared signal back to 90 % of its
// pre-press level.
//
// Pins: SDA 8, SCL 9, FSR divider 1, NTC divider 2, button 5, buzzer 7,
//       battery divider 0.

#include <math.h>
#include <stdio.h>

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

#include "crt.h"
#include "max30102.h"
#include "oled.h"

#define PIN_SDA   8
#define PIN_SCL   9
#define PIN_BTN   5
#define PIN_BUZZ  7
#define CH_VBAT   ADC_CHANNEL_0   // GPIO0
#define CH_FSR    ADC_CHANNEL_1   // GPIO1
#define CH_NTC    ADC_CHANNEL_2   // GPIO2

#define COLD_C    30.0f

static const char *TAG = "crt";
static adc_oneshot_unit_handle_t adc;
static adc_cali_handle_t cali;

static uint32_t now_ms(void) { return (uint32_t)(esp_timer_get_time() / 1000); }

static int read_mv(adc_channel_t ch)
{
    int mv = 0;
    adc_oneshot_get_calibrated_result(adc, cali, ch, &mv);
    return mv;
}

static float battery_v(void) { return read_mv(CH_VBAT) * 2 / 1000.0f; }

// 10k B3950 NTC to GND, 10k to 3V3
static float skin_c(void)
{
    float v = read_mv(CH_NTC) / 1000.0f;
    if (v <= 0.01f || v >= 3.29f)
        return NAN;
    float r = 10000.0f * v / (3.3f - v);
    float inv_t = 1.0f / 298.15f + logf(r / 10000.0f) / 3950.0f;
    return 1.0f / inv_t - 273.15f;
}

static void beep(uint32_t hz, uint32_t ms)
{
    ledc_set_freq(LEDC_LOW_SPEED_MODE, LEDC_TIMER_0, hz);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 512);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    vTaskDelay(pdMS_TO_TICKS(ms));
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, 0);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

// Moving average of IR over the last 8 samples (80 ms) to remove pulse ripple
static float ir_smooth(void)
{
    static float buf[8];
    static int i, filled;
    uint32_t s[32];
    int n = max30102_read_ir(s, 32);
    for (int k = 0; k < n; k++) {
        buf[i] = (float)s[k];
        i = (i + 1) % 8;
        if (filled < 8)
            filled++;
    }
    float acc = 0;
    for (int k = 0; k < filled; k++)
        acc += buf[k];
    return filled ? acc / filled : 0;
}

static int bar_x(int mv)
{
    if (mv < 0) mv = 0;
    if (mv > 3000) mv = 3000;
    return mv * 127 / 3000;
}

static void screen(const char *a, const char *b, const char *c, int force_mv)
{
    oled_clear();
    oled_text(0, 0, "Capillary refill");
    if (battery_v() < 3.45f)
        oled_text(104, 0, "LOW");
    oled_text(0, 16, a);
    oled_text(0, 28, b);
    oled_text(0, 40, c);
    if (force_mv >= 0) {   // force bar with the target band marked
        oled_rect(0, 54, 128, 10, false);
        oled_rect(0, 54, bar_x(force_mv), 10, true);
        oled_vline(bar_x(CRT_FSR_LOW_MV), 50, 14);
        oled_vline(bar_x(CRT_FSR_HIGH_MV), 50, 14);
    }
    oled_show();
}

static void wait_button(void)
{
    while (gpio_get_level(PIN_BTN))
        vTaskDelay(pdMS_TO_TICKS(5));
    vTaskDelay(pdMS_TO_TICKS(30));
    while (!gpio_get_level(PIN_BTN))
        vTaskDelay(pdMS_TO_TICKS(5));
}

static void hw_init(void)
{
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = PIN_SDA,
        .scl_io_num = PIN_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    i2c_master_bus_handle_t bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    ESP_ERROR_CHECK(oled_init(bus));

    gpio_config_t btn = {
        .pin_bit_mask = 1ULL << PIN_BTN,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
    };
    gpio_config(&btn);

    adc_oneshot_unit_init_cfg_t unit = {.unit_id = ADC_UNIT_1};
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit, &adc));
    adc_oneshot_chan_cfg_t ch = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    adc_channel_t chans[] = {CH_VBAT, CH_FSR, CH_NTC};
    for (int i = 0; i < 3; i++)
        ESP_ERROR_CHECK(adc_oneshot_config_channel(adc, chans[i], &ch));
    adc_cali_curve_fitting_config_t cc = {
        .unit_id = ADC_UNIT_1, .atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    ESP_ERROR_CHECK(adc_cali_create_scheme_curve_fitting(&cc, &cali));

    ledc_timer_config_t t = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = 2000,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&t));
    ledc_channel_config_t c = {
        .gpio_num = PIN_BUZZ,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
    };
    ESP_ERROR_CHECK(ledc_channel_config(&c));

    if (max30102_init(bus, 0x24) != ESP_OK) {
        screen("Optical sensor", "not found.", "", -1);
        for (;;)
            vTaskDelay(portMAX_DELAY);
    }
}

static void measure(void)
{
    char tl[24], l1[24], l2[28];
    float t = skin_c();
    if (isnan(t))
        snprintf(tl, sizeof tl, "Skin temp: --");
    else
        snprintf(tl, sizeof tl, "Skin %.1f C%s", t, t < COLD_C ? " COLD" : "");

    crt_t c;
    crt_start(&c, now_ms());
    crt_phase_t shown = CRT_DONE;
    uint32_t last_draw = 0;

    for (;;) {
        int mv = read_mv(CH_FSR);
        float ir = ir_smooth();
        uint32_t now = now_ms();
        crt_phase_t p = crt_step(&c, now, mv, ir);

        if (p == CRT_DONE || p == CRT_NO_PRESS)
            break;
        if (p == CRT_WAIT_RELEASE && shown != CRT_WAIT_RELEASE)
            beep(2400, 120);

        if (p != shown || (p == CRT_PRESS && now - last_draw > 60)) {
            switch (p) {
            case CRT_BASELINE:
                screen("Baseline...", "Keep finger still.", tl, -1);
                break;
            case CRT_PRESS: {
                int left = crt_hold_seconds_left(&c, now);
                if (left)
                    snprintf(l2, sizeof l2, "Hold... %d s", left);
                else
                    snprintf(l2, sizeof l2, "%s", mv < CRT_FSR_LOW_MV ? "Press harder" : "Press lighter");
                screen("Press the nail.", l2, tl, mv);
                break;
            }
            case CRT_WAIT_RELEASE:
                screen("RELEASE now", "", tl, -1);
                break;
            case CRT_TIMING:
                screen("Timing refill...", "", tl, -1);
                break;
            default:
                break;
            }
            shown = p;
            last_draw = now;
        }
        vTaskDelay(pdMS_TO_TICKS(p == CRT_TIMING || p == CRT_WAIT_RELEASE ? 10 : 20));
    }

    if (c.phase == CRT_NO_PRESS) {
        screen("No press detected.", "", "Button: start", -1);
        return;
    }
    crt_class_t k = crt_classify(c.crt_ms);
    if (!c.crt_ms) {
        snprintf(l1, sizeof l1, "CRT > 10 s");
        snprintf(l2, sizeof l2, "PROLONGED");
    } else {
        float s = roundf(c.crt_ms / 100.0f) / 10.0f;
        snprintf(l1, sizeof l1, "CRT %.1f s", s);
        snprintf(l2, sizeof l2, "%s", k == CRT_PROLONGED ? "PROLONGED (3 s+)" : k == CRT_BORDERLINE ? "Borderline" : "Normal");
        ESP_LOGI(TAG, "crt,%.1f,base,%.0f,release,%.0f,skinC,%.1f", s, c.base, c.at_release, t);
    }
    beep(k == CRT_PROLONGED ? 2800 : 1500, 300);
    screen(l1, l2, tl, -1);
}

void app_main(void)
{
    hw_init();
    screen("Rest finger, pad", "down, in the cradle.", "Button: start", -1);
    for (;;) {
        wait_button();
        measure();
    }
}
