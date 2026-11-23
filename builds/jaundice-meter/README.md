# Transcutaneous jaundice meter

A handheld probe that estimates bilirubin through a newborn's skin using reflected blue and green light.

**Who it is for:** Neonatal nurses, lady health visitors, midwives  
**Board:** ESP32-C3 SuperMini  
**Firmware:** Rust  
**Parts:** about $25 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

Most newborns turn yellow in their first week. In a small number, bilirubin climbs high enough to cause permanent brain damage, and South Asia carries a large share of those cases. Catching the rise early depends on measuring it.

Hospitals measure bilirubin with a blood test or with a transcutaneous meter that costs several thousand dollars. Most clinics in Pakistan have neither, so the decision rests on looking at the baby's skin colour, which is unreliable, and worse on darker skin.

## How it works

The probe tip is pressed against the baby's forehead or sternum until an internal spring trips a switch, so every reading uses the same pressure. That pressure also pushes blood out of the skin, which would otherwise swamp the signal.

A white LED lights the skin and an eleven-channel spectral sensor reads the reflected light. Bilirubin absorbs strongly around 450 to 480 nm; haemoglobin and melanin absorb elsewhere. The firmware converts each channel to optical density against a white PTFE reference stored in the cap, then computes a jaundice index from the blue band minus the green band, corrected for skin pigment using the red channels.

## What is in this folder

```
jaundice-meter/
├── firmware/
│   ├── Cargo.toml      esp-hal, no_std
│   ├── src/main.rs     probe, buttons, screen, measurement loop
│   ├── src/as7341.rs   spectral sensor driver
│   └── src/optics.rs   optical density, melanin correction, jaundice index
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    ├── body-lower.step / .stl
    ├── body-upper.step / .stl
    ├── probe-collar.step / .stl
    └── reference-cap.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO8 | SDA |
| GPIO9 | SCL |
| 3V3 | 3V3 |
| GND | GND |
| GPIO5 | PROBE_SW |
| GPIO6 | BTN_MODE |
| GPIO7 | BUZZER |
| GPIO0 | VBAT_SENSE |
| 5V | VBAT |

## Parts

| Ref | Qty | Part | Notes |
|---|---|---|---|
| U1 | 1 | ESP32-C3 SuperMini | Microcontroller board, USB-C, onboard 3V3 LDO |
| U9 | 1 | TP4056 USB-C module | 1 A Li-ion charger with DW01 protection |
| BT1 | 1 | LiPo cell 3.7 V 400 mAh | With JST-PH lead |
| SW1 | 1 | SS12D00 slide switch | Main power |
| R8, R9 | 2 | 100 kΩ resistor | Battery voltage divider to GPIO0 |
| U2 | 1 | AS7341 breakout with LED | 11-channel spectral sensor, I²C |
| U3 | 1 | SSD1306 OLED 0.96 in | 128×64, I²C |
| SW2 | 1 | Micro switch, short lever | Pressure trigger |
| SW3 | 1 | 6 mm tactile switch | Mode |
| LS1 | 1 | Passive piezo buzzer 12 mm |  |
| Mech | 1 | PTFE disc 15 × 2 mm | White reference in cap |
| Mech | 1 | Compression spring 6 × 15 mm | Sets probe force |
| Mech | 1 | PETG print, black | Light-tight body and probe |

Prices for each line are in `hardware/bom.csv`; the total is about $25.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. Install Rust with rustup and then espflash (`cargo install espflash`). From `firmware/`, `cargo run --release` builds for the ESP32-C3, flashes over USB and opens the serial monitor. The serum-bilirubin calibration goes in `CALIBRATION` in `src/optics.rs`.
4. Print the body in black PETG so no outside light reaches the sensor; paint the inside of the nose matte black if you print in white.
5. Mount the AS7341 board at the back of the nose, sensor and LED facing the aperture.
6. Fit the spring between the nose and the micro switch so it only trips when the tip is pressed firmly against skin.
7. Glue the PTFE disc into the cap. Press MODE, push the probe into the cap and the white reference is saved. Redo it weekly.

## Testing before clinical use

The index must be calibrated against serum bilirubin drawn at the same time, across skin tones, before it can be reported in mg/dL. The planned study pairs readings with routine blood tests in a neonatal unit and fits the calibration openly.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
