# Needle-free anaemia screener

A fingertip clip that shines five wavelengths through the finger and estimates haemoglobin without a blood sample.

**Who it is for:** Antenatal clinics, lady health visitors, school health programmes  
**Board:** ESP32-C3 SuperMini  
**Firmware:** CircuitPython  
**Parts:** about $20 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

About four in ten women of reproductive age in Pakistan are anaemic (WHO, 2019). Anaemia in pregnancy raises the risk of haemorrhage, low birth weight and maternal death, and it is cheap to treat once found.

Finding it usually means a finger prick and a reagent cuvette or a lab, which costs money per test and needs sharps disposal. A test that costs nothing per use could screen every woman at every antenatal visit.

## How it works

The finger sits in a light-tight clip between five LEDs (530, 590, 660, 810 and 940 nm) and a photodiode with a built-in amplifier. The LEDs fire one at a time, with a dark frame between, about seventy-five times a second for twenty seconds.

Each wavelength produces a pulse waveform. Its pulsing part comes from arterial blood; its steady part from everything else. Ratios of pulsing to steady light across pairs of wavelengths change with haemoglobin concentration, and a regression model turns those ratios into an estimate in g/dL. The screen shows the estimate and flags it against the WHO cut-off for the person's group.

## What is in this folder

```
anaemia-screener/
├── firmware/
│   ├── code.py              runs at boot: LEDs, button, screen
│   ├── hb.py                AC/DC separation and log ratios, no hardware calls
│   ├── ads1115.py           16-bit ADC driver
│   ├── model.example.json   where fitted coefficients go
│   └── tests/               pytest, synthetic pulse signals
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    ├── lower.step / .stl
    └── upper.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO8 | SDA |
| GPIO9 | SCL |
| 3V3 | 3V3 |
| GND | GND |
| GPIO1 | LED_530 |
| GPIO3 | LED_590 |
| GPIO4 | LED_660 |
| GPIO5 | LED_810 |
| GPIO6 | LED_940 |
| GPIO10 | BTN |
| GPIO7 | BUZZER |
| GPIO0 | VBAT_SENSE |

## Parts

| Ref | Qty | Part | Notes |
|---|---|---|---|
| U1 | 1 | ESP32-C3 SuperMini | Microcontroller board, USB-C, onboard 3V3 LDO |
| U9 | 1 | TP4056 USB-C module | 1 A Li-ion charger with DW01 protection |
| BT1 | 1 | LiPo cell 3.7 V 400 mAh | With JST-PH lead |
| SW1 | 1 | SS12D00 slide switch | Main power |
| R8, R9 | 2 | 100 kΩ resistor | Battery voltage divider to GPIO0 |
| U2 | 1 | ADS1115 breakout | 16-bit ADC, I²C |
| U4 | 1 | OPT101 photodiode + TIA | DIP-8 |
| D1–D5 | 5 | LEDs 530, 590, 660, 810, 940 nm | 3 mm or 5 mm, narrow band |
| Q1–Q5 | 5 | 2N7002 N-MOSFET | LED switches |
| R10–R14 | 5 | Series resistors 68–150 Ω | Set per LED for equal DC level |
| U3 | 1 | SSD1306 OLED 0.96 in | 128×64, I²C |
| SW2 | 1 | 6 mm tactile switch |  |
| LS1 | 1 | Passive piezo buzzer 12 mm |  |
| Mech | 1 | Black PETG print + foam liner | Light-tight finger clip |

Prices for each line are in `hardware/bom.csv`; the total is about $20.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. Install CircuitPython 9 or later for the ESP32-C3, copy `code.py`, `hb.py` and `ads1115.py` to the board, and install the two display libraries with `circup install -r requirements.txt`. Once coefficients have been fitted, copy `model.example.json` to `model.json` on the board and fill them in.
4. Put the five LEDs in a row in the upper shell, pointing down through the finger, with the OPT101 opposite in the lower shell.
5. Line the finger channel with black foam so it closes around the finger and blocks room light.
6. With a finger in, pick each LED's series resistor so the DC levels in the serial log come out similar (about 1.5 to 2.5 V).
7. Every reading prints AC, DC and the four log ratios to the serial console. Pair them with a lab haemoglobin to build the calibration set.

The signal processing has tests that run on a computer, no hardware needed:

```
cd firmware && pytest tests/
```

## Testing before clinical use

The regression must be fitted against laboratory haemoglobin across skin tones before the device reports g/dL; until then it shows raw ratios. The planned study pairs readings with venous haemoglobin at an antenatal clinic.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
