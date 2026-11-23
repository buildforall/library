# Breath counter for childhood pneumonia

A belly clip that counts a child's breaths for a full minute and applies WHO's fast-breathing cut-offs by age.

**Who it is for:** Lady Health Workers and outpatient nurses  
**Board:** ESP32-C3 SuperMini  
**Firmware:** MicroPython  
**Parts:** about $15 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

Pneumonia kills more children under five than any other infection, and Pakistan carries one of the heaviest burdens in the world. At the front line, the test is a health worker counting breaths for sixty seconds and comparing the count to an age cut-off: 60 or more a minute under two months, 50 or more up to a year, 40 or more up to five years.

Counting a squirming, crying infant's breaths by eye is hard, and studies of community health workers show counts that drift far from video-verified rates. A wrong count sends a sick child home or a healthy one to hospital.

## How it works

A puck the size of a matchbox sits on the child's belly under an elastic band. A six-axis motion sensor reads the rise and fall of the abdomen fifty times a second. Firmware filters out everything outside the breathing band (0.15 to 2 Hz), picks the axis carrying the most breathing signal, and counts complete cycles with an adaptive threshold.

The health worker sets the child's age band with one button and starts the count with the other. After sixty seconds the screen shows the count and, if it crosses the WHO cut-off, the words FAST BREATHING. If the child moves too much, the count pauses and the minute is extended rather than guessed.

## What is in this folder

```
breath-counter/
├── firmware/
│   ├── main.py      runs at boot: buttons, screen, buzzer
│   ├── breath.py    filtering and breath counting, no hardware calls
│   ├── lsm6ds3.py   accelerometer driver
│   └── tests/       pytest, synthetic breathing signals
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    ├── base.step / .stl
    └── lid.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO8 | SDA |
| GPIO9 | SCL |
| 3V3 | 3V3 |
| GND | GND |
| GPIO5 | BTN_START |
| GPIO6 | BTN_AGE |
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
| U2 | 1 | LSM6DS3TR-C breakout | 6-axis IMU, I²C |
| U3 | 1 | SSD1306 OLED 0.96 in | 128×64, I²C |
| SW2, SW3 | 2 | 6 mm tactile switch | Start, age band |
| LS1 | 1 | Passive piezo buzzer 12 mm |  |
| Mech | 1 | Elastic belt 25 mm with buckle | Holds puck on abdomen |
| Mech | 1 | PLA or PETG print | Enclosure, about 18 g |

Prices for each line are in `hardware/bom.csv`; the total is about $15.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. Install MicroPython for the ESP32-C3 (the *ESP32_GENERIC_C3* image from micropython.org), then from `firmware/` run `mpremote mip install ssd1306` and `mpremote cp main.py breath.py lsm6ds3.py :`. Reset the board.
4. Stick the motion sensor flat to the floor of the base with foam tape, X axis along the long side. It must not rattle.
5. Seat the OLED behind the window and the two buttons in the lid; the buzzer sits under the small vent.
6. Thread a 25 mm elastic band through both side lugs.
7. Test on yourself: lie down, put the puck on your abdomen, count your own breaths for a minute and compare. Then try breathing fast.

The signal processing has tests that run on a computer, no hardware needed:

```
cd firmware && pytest tests/
```

## Testing before clinical use

Before any clinical use: bench test on a motorised breathing phantom at 20 to 90 breaths a minute, then a comparison against two clinicians counting from video in a paediatric ward, reported as a Bland-Altman analysis.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
