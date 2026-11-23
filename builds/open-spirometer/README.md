# Open spirometer

A 3D-printed flow tube and a differential pressure sensor that measure FEV1, FVC and peak flow from one hard breath out.

**Who it is for:** Chest clinics, TB programmes, general practitioners  
**Board:** ESP32-C3 SuperMini  
**Firmware:** C++17, ESP-IDF  
**Parts:** about $43 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

Chronic lung disease is common in Pakistan, driven by tobacco, cooking smoke from wood and dung, and lung damage left behind by tuberculosis. Spirometry, the test that measures how much air the lungs can move and how fast, is how these conditions are diagnosed and graded.

Outside large hospitals, spirometers are rare, and an office unit usually costs several hundred dollars or more. Patients with chronic obstructive lung disease are often labelled with asthma, or with nothing, for years.

## How it works

The patient blows as hard and long as possible through a disposable mouthpiece into a printed tube with a fine stainless steel mesh across it. Air through the mesh produces a small pressure drop proportional to flow. A Sensirion differential pressure sensor reads that drop two hundred times a second.

Firmware converts pressure to flow using a constant set with a 3-litre calibration syringe, integrates flow into volume, finds the start of the blow by back-extrapolation, and reports FEV1 (volume in the first second), FVC (total volume), their ratio and peak flow. A ratio under 0.70 is flagged as possible obstruction, which then needs a repeat test after a bronchodilator. The full flow-volume curve streams over Bluetooth.

## What is in this folder

```
open-spirometer/
├── firmware/
│   ├── main/main.cpp            set-up, calibration, measurement
│   ├── main/spirometry.hpp      flow, volume, back-extrapolation, BTPS
│   ├── main/sdp810.cpp          pressure sensor driver
│   ├── main/curve_service.cpp   Bluetooth LE service (NimBLE)
│   ├── main/display.cpp         display driver
│   └── tests/                   host tests with simulated blows
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    ├── flow-tube.step / .stl
    ├── grip.step / .stl
    └── mesh-flange.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO8 | SDA |
| GPIO9 | SCL |
| 3V3 | 3V3 |
| GND | GND |
| GPIO5 | BTN |
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
| U2 | 1 | Sensirion SDP810-500Pa | Differential pressure, I²C, with tube ports |
| U3 | 1 | SSD1306 OLED 0.96 in | 128×64, I²C |
| Mech | 1 | Stainless mesh disc, 400 mesh, Ø30 mm | Flow resistance |
| Mech | 2 | Silicone tube 3 mm ID, 6 cm | Pressure taps to sensor |
| Mech | 1 | Cardboard mouthpiece 30 mm | Single-use, per patient |
| SW2 | 1 | 12 mm tactile switch |  |
| LS1 | 1 | Passive piezo buzzer 12 mm |  |
| Mech | 1 | PETG print | Flow head and body |

Prices for each line are in `hardware/bom.csv`; the total is about $43.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. With ESP-IDF 5.x: `idf.py set-target esp32c3`, then `idf.py build flash monitor` from `firmware/`. Or with PlatformIO: `pio run -t upload`.
4. Clamp the stainless mesh disc in the flange between the two halves of the flow tube.
5. Connect the mouth-side tap to the sensor's + port and the other tap to the − port.
6. Calibrate before first use and weekly: hold the button while switching on, then push a 3 L syringe through at a steady speed.
7. New cardboard mouthpiece and a nose clip for every patient.

The signal processing has tests that run on a computer, no hardware needed:

```
make -C firmware/tests
```

## Testing before clinical use

Calibration and linearity check with a 3-litre syringe at several speeds against the ATS/ERS accuracy limit of ±3 percent, then side-by-side testing against a hospital spirometer in a chest clinic.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
