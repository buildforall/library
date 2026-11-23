# Clubfoot brace adherence sensor

A coin-sized temperature logger inside a clubfoot brace that tells the clinic how many hours a day it was worn.

**Who it is for:** Ponseti clinics and the families they treat  
**Board:** Seeed XIAO nRF52840  
**Firmware:** Zephyr RTOS  
**Parts:** about $17 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

Clubfoot affects about one in every thousand babies. The Ponseti method corrects almost every case with casts and a small operation, but the correction only holds if the child wears a foot-abduction brace for most of the day for three months and then at night until about age four.

Families stop using the brace for understandable reasons, and relapse follows. At follow-up the clinic has to rely on what the parents remember, so it cannot tell which families need help until the foot has already turned back in.

## How it works

A sealed capsule the size of a large coin clips inside one of the brace's shoes. A precision temperature sensor reads every ten minutes; between readings the board sleeps on a few microamps. When the shoe is on a foot, its temperature sits close to skin temperature; when it is off, it falls towards room temperature.

The firmware classifies each reading as worn or not worn, with hysteresis so a cool morning does not count as removal, and adds up hours worn per day. At follow-up the nurse presses the capsule's button and reads months of daily totals on a phone over Bluetooth. A charge lasts several months between visits.

## What is in this folder

```
clubfoot-brace-sensor/
├── firmware/
│   ├── prj.conf                  Bluetooth, I2C, LittleFS
│   ├── boards/xiao_ble.overlay   sensor, button and log partition on the XIAO
│   ├── src/main.c                sampling, log file, Bluetooth service
│   ├── src/wearlog.c             encoding and daily summaries, no hardware calls
│   └── tests/                    host tests for the summaries
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    ├── capsule.step / .stl
    └── clip.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| D4 | SDA |
| D5 | SCL |
| 3V3 | 3V3 |
| GND | GND |
| D1 | BTN |
| BAT+ | VBAT |
| BAT− | GND |

## Parts

| Ref | Qty | Part | Notes |
|---|---|---|---|
| U1 | 1 | Seeed XIAO nRF52840 | BLE board with onboard Li-ion charger |
| U2 | 1 | TMP117 breakout | ±0.1 °C digital temperature sensor |
| BT1 | 1 | LiPo 3.7 V 100 mAh | 401230 cell |
| SW2 | 1 | Sealed tactile switch 6 mm | IP67 |
| Mech | 1 | PETG print + silicone gasket | Ø36 mm capsule, clip |

Prices for each line are in `hardware/bom.csv`; the total is about $17.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. With Zephyr 4.x and west: `west build -b xiao_ble firmware`. Double-tap the XIAO's reset button and copy `build/zephyr/zephyr.uf2` to the drive that appears. `boards/nrf52840dk_nrf52840.overlay` builds the same app for an nRF52840 DK on the bench.
4. Flash and test before sealing; the LED blinks once at every reading.
5. Press the TMP117 against the capsule wall that faces the foot, with a dab of thermal paste.
6. Close the cap over the gasket and clip the capsule inside the brace shoe, behind the heel.
7. At follow-up: press the button, connect over Bluetooth, turn on notifications for the data characteristic and write S for the daily summary.

The signal processing has tests that run on a computer, no hardware needed:

```
make -C firmware/tests
```

## Testing before clinical use

Bench tests against a logged heating pad to set thresholds across room temperatures, then a pilot with families at a Ponseti clinic comparing sensor totals with a daily diary.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
