# Stroke hand-rehabilitation glove

A glove with a bend sensor on each finger that measures range of motion and counts exercise repetitions at home.

**Who it is for:** Stroke survivors and physiotherapists  
**Board:** ESP32-S3 SuperMini  
**Firmware:** Arduino  
**Parts:** about $34 for one unit at 2026 retail prices

> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.

## Why

After a stroke, recovery of the hand depends on thousands of repetitions in the months after discharge. Almost all of that work happens at home, and the physiotherapist sees the patient for a few minutes every few weeks.

Neither the patient nor the therapist can see whether the hand is actually improving between visits, or whether the exercises are being done at all. A measured trend would let a therapist adjust the programme instead of guessing.

## How it works

A soft cotton glove carries a flex sensor along the back of each finger and a small pod on the back of the hand. Each sensor changes resistance as the finger bends; the pod reads all five fifty times a second, along with wrist rotation from a motion sensor.

A thirty-second calibration (open hand, then fist) maps each finger to 0 to 100 percent of the patient's own range. The firmware counts a repetition each time a finger goes past 70 percent and back below 30, and keeps per-session totals and peak range for each finger. The record streams over Bluetooth to a phone, which is where the exercise app comes next.

## What is in this folder

```
stroke-rehab-glove/
├── firmware/
│   └── rehab_glove/rehab_glove.ino   the whole sketch
├── hardware/
│   └── bom.csv         parts list with prices
└── enclosure/          STEP to edit, STL to print
    └── pod.step / .stl
```

## Wiring

| Board pin | Connects to |
|---|---|
| GPIO1 | THUMB |
| GPIO2 | INDEX |
| GPIO3 | MIDDLE |
| GPIO4 | RING |
| GPIO5 | LITTLE |
| 3V3 | 3V3 |
| GND | GND |
| GPIO8 | SDA |
| GPIO9 | SCL |
| GPIO6 | BTN |
| GPIO7 | VBAT_SENSE |
| 5V | VBAT |

## Parts

| Ref | Qty | Part | Notes |
|---|---|---|---|
| U1 | 1 | ESP32-S3 SuperMini | Microcontroller board, USB-C, onboard RGB LED |
| U9 | 1 | TP4056 USB-C module | 1 A Li-ion charger with DW01 protection |
| BT1 | 1 | LiPo cell 3.7 V 500 mAh | With JST-PH lead |
| SW1 | 1 | SS12D00 slide switch | Main power |
| R8, R9 | 2 | 100 kΩ resistor | Battery divider to GPIO7 |
| FS1–FS5 | 5 | Flex sensor 2.2 in | Bend-sensitive resistor |
| R1–R5 | 5 | 47 kΩ resistor | Divider per finger |
| U2 | 1 | LSM6DS3TR-C breakout | 6-axis IMU, I²C |
| SW2 | 1 | 6 mm tactile switch |  |
| Mech | 1 | Cotton glove + sewn sensor sleeves | Machine-washable with pod removed |
| Mech | 1 | Ribbon cable 7-way, 15 cm | Sensors to pod |
| Mech | 1 | PETG print | Hand pod |

Prices for each line are in `hardware/bom.csv`; the total is about $34.

## Build

1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.
2. Wire everything as in the table above. Keep the I²C wires under 10 cm.
3. Flash the firmware. Arduino IDE 2 with Espressif's **esp32** core 4.x. Board: *ESP32S3 Dev Module*, with *USB CDC On Boot* enabled. Library from the Library Manager: Adafruit LSM6DS. Bluetooth comes with the core.
4. Sew a fabric sleeve along the back of each finger and slide a flex sensor in, printed side up, connector at the knuckle.
5. Run the ribbon from the sensors to the pod. The pod lifts off so the glove can be washed.
6. Calibrate per patient: hold the button 2 s. Blue: open the hand. Amber: make a fist. Green: saved.
7. A short press starts or ends a session. Live data and the session summary are readable over Bluetooth.

## Testing before clinical use

Comparison of glove-measured joint range against goniometer measurements by a physiotherapist, then a home-use feasibility study tracking adherence for four weeks.

If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.
