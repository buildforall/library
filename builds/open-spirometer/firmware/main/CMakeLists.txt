idf_component_register(
    SRCS "main.cpp" "sdp810.cpp" "display.cpp" "curve_service.cpp"
    INCLUDE_DIRS "."
    PRIV_REQUIRES esp_driver_i2c esp_driver_gpio esp_driver_ledc esp_adc esp_timer nvs_flash bt
)
target_compile_options(${COMPONENT_LIB} PRIVATE -std=gnu++17)
