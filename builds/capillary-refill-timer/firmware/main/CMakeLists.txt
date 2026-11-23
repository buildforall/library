idf_component_register(
    SRCS "main.c" "crt.c" "max30102.c" "oled.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES esp_driver_i2c esp_driver_gpio esp_driver_ledc esp_adc esp_timer
)
