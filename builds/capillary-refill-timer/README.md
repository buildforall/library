# Capillary refill timer

A fingertip cradle that times how fast blood returns after a standard press, in tenths of a second.

**Who it is for:** Emergency and paediatric triage staff  
**Board:** ESP32-C3 SuperMini  
**Firmware:** C, ESP-IDF  
**Parts:** about $16 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

Pressing a child's fingertip for five seconds and counting how long the colour takes to return is a standard bedside check for shock and severe dehydration. WHO emergency triage treats a refill time over three seconds as a danger sign.

The test depends on how hard the clinician presses, how long, the light in the room, the child's skin tone and the clinician's counting. Two people timing the same child often disagree by a second or more, which is the entire width of the decision.

## How it works

The child's finger rests pad-down on a cradle with an optical sensor under the window. The clinician presses the nail with a plunger that has a force sensor in it; a bar on the screen shows when the press is in the target range, and the device counts the five seconds.

When the plunger is released, the sensor under the fingertip watches the reflected infrared light return to its pre-press level. Refill time is reported as the moment the signal recovers ninety percent of the way back, to a tenth of a second. A skin thermistor warns when the finger is cold, since cold fingers refill slowly for reasons that have nothing to do with shock.

## What is in this folder

```
capillary-refill-timer/
├── firmware/
│   ├── main/main.c         hardware set-up, screens, the measurement loop
│   ├── main/crt.c, crt.h   the refill state machine, no hardware calls
│   ├── main/max30102.c     optical sensor driver
│   ├── main/oled.c         display driver and 6x8 font
│   └── tests/              host tests with simulated refills
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    ├── arch.step / .stl
    ├── base.step / .stl
    ├── cradle.step / .stl
    └── plunger.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO8 | SDA |
| GPIO9 | SCL |
| GPIO1 | FSR |
| GPIO2 | NTC |
| 3V3 | 3V3 |
| GND | GND |
| GPIO5 | BTN_START |
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
| U2 | 1 | MAX30102 breakout | Red/IR reflectance sensor, I²C |
| U3 | 1 | SSD1306 OLED 0.96 in | 128×64, I²C |
| FSR1 | 1 | Force-sensing resistor 12 mm | FSR 402 or equivalent |
| RT1 | 1 | NTC thermistor 10 kΩ, B3950 | Skin temperature |
| R1, R2 | 2 | 10 kΩ resistor | Dividers |
| SW2 | 1 | 12 mm tactile switch | Start |
| LS1 | 1 | Passive piezo buzzer 12 mm |  |
| Mech | 1 | Clear acrylic disc 12 × 1 mm | Sensor window |
| Mech | 1 | PETG print | Cradle and plunger |

Prices for each line are in `hardware/bom.csv`; the total is about $16.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. With ESP-IDF 5.x: `idf.py set-target esp32c3`, then `idf.py build flash monitor` from `firmware/`. Or with PlatformIO: `pio run -t upload`. The force band is set in `main/crt.h`.
4. Glue the clear window into the cradle with the MAX30102 directly underneath, facing up.
5. Stack the force sensor under the plunger head so the whole press goes through it.
6. Bed the thermistor beside the window with a little thermal paste.
7. Set the force band: rest 1 kg, then 2 kg on the plunger, note the millivolts in the serial log and put them in `CRT_FSR_LOW_MV` and `CRT_FSR_HIGH_MV`.

The signal processing has tests that run on a computer, no hardware needed:

```
make -C firmware/tests
```

## Testing before clinical use

Bench calibration of the force sensor with weights, then a comparison with slow-motion video timing by two clinicians on children presenting to an emergency department, with skin temperature recorded.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
