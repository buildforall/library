# Freezing-of-gait anklet

An ankle pod that detects a Parkinson's freeze from the leg's trembling and starts a vibration rhythm to restart walking.

**Who it is for:** People with Parkinson's and their neurologists  
**Board:** ESP32-C3 SuperMini  
**Firmware:** C++, PlatformIO  
**Parts:** about $13 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

Many people with advanced Parkinson's disease freeze in the middle of walking, most often at doorways and turns: the feet stop while the body keeps moving. Freezing is one of the main causes of falls in Parkinson's, and medication controls it poorly.

A steady external rhythm, a metronome or a pulse on the skin, helps many patients restart. The problem is delivering it at the right moment, without the patient having to reach for anything.

## How it works

A pod strapped above the ankle samples the shank's motion sixty-four times a second. During a freeze the leg trembles at 3 to 8 Hz instead of swinging at walking speed. Every half second the firmware computes the freeze index, the ratio of power in that trembling band to power in the walking band (0.5 to 3 Hz), over the last four seconds.

When the index crosses the patient's threshold, two vibration motors pulse at the patient's own walking cadence until normal stepping resumes, then for three seconds more. Each episode is logged with its time and duration, and the log can be read over Bluetooth for the neurologist.

## What is in this folder

```
freezing-of-gait-anklet/
├── firmware/
│   ├── platformio.ini            board and library versions
│   ├── src/main.cpp              sensor, motors, button, Bluetooth
│   ├── lib/FreezeIndex/          freeze index, cadence and cue logic
│   └── test/test_freeze_index/   unit tests that run on a computer
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    └── pod.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO8 | SDA |
| GPIO9 | SCL |
| 3V3 | 3V3 |
| GND | GND |
| GPIO10 | MOTOR |
| GPIO5 | BTN |
| GPIO0 | VBAT_SENSE |
| 5V | VBAT |

## Parts

| Ref | Qty | Part | Notes |
|---|---|---|---|
| U1 | 1 | ESP32-C3 SuperMini | Microcontroller board, USB-C, onboard 3V3 LDO |
| U9 | 1 | TP4056 USB-C module | 1 A Li-ion charger with DW01 protection |
| BT1 | 1 | LiPo cell 3.7 V 300 mAh | With JST-PH lead |
| SW1 | 1 | SS12D00 slide switch | Main power |
| R8, R9 | 2 | 100 kΩ resistor | Battery voltage divider to GPIO0 |
| U2 | 1 | LSM6DS3TR-C breakout | 6-axis IMU, I²C |
| M1, M2 | 2 | 10 mm coin vibration motor | 3 V ERM |
| Q1 | 1 | AO3400 N-MOSFET | Low-side motor switch |
| D1 | 1 | 1N4148 diode | Flyback across motors |
| R3 | 1 | 100 kΩ resistor | Gate pull-down |
| SW2 | 1 | 6 mm tactile switch |  |
| Mech | 1 | Hook-and-loop strap 30 mm | Above the ankle |
| Mech | 1 | PETG print | Pod, about 14 g |

Prices for each line are in `hardware/bom.csv`; the total is about $13.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. With PlatformIO, from `firmware/`: `pio run -e supermini -t upload`. The libraries (Adafruit LSM6DS, NimBLE-Arduino) are fetched on the first build.
4. Glue both vibration motors to the inner (skin) face of the pod.
5. Wear it on the outside of the leg, a hand's width above the ankle bone, strap snug.
6. Start with a threshold of 2.0. With the neurologist, connect over Bluetooth (nRF Connect works) and write T and a number, such as T2.4, to the settings characteristic to tune it.

The signal processing has tests that run on a computer, no hardware needed:

```
cd firmware && pio test -e native
```

## Testing before clinical use

Threshold tuning on a published labelled freezing dataset, then supervised walking trials with patients through a doorway course, scored from video by a movement-disorders clinician.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
