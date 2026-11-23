"""Single source of truth for every Build for All device.

Used by the drawing generators, the README builder and the website.
Prices are approximate 2026 single-unit retail in USD from common online
electronics suppliers. They are for budgeting, not quotes.
"""

C3 = {"title": "ESP32-C3 SuperMini", "part": "RISC-V, 160 MHz, Wi-Fi + BLE 5"}
S3 = {"title": "ESP32-S3 SuperMini", "part": "Dual-core 240 MHz, Wi-Fi + BLE 5"}
NRF = {"title": "Seeed XIAO nRF52840", "part": "Cortex-M4, BLE 5, µA sleep"}

LIPO_CHAIN = lambda mah: [("USB-C 5 V", "J1, charging only"),
                          ("TP4056 module", "Li-ion charger + DW01 cut-off"),
                          (f"LiPo 3.7 V", f"BT1, {mah} mAh"),
                          ("Slide switch", "SW1, main power")]

COMMON_C3_BOM = lambda mah, price: [
    ("U1", 1, "ESP32-C3 SuperMini", "Microcontroller board, USB-C, onboard 3V3 LDO", 3.00),
    ("U9", 1, "TP4056 USB-C module", "1 A Li-ion charger with DW01 protection", 0.60),
    ("BT1", 1, f"LiPo cell 3.7 V {mah} mAh", "With JST-PH lead", price),
    ("SW1", 1, "SS12D00 slide switch", "Main power", 0.10),
    ("R8, R9", 2, "100 kΩ resistor", "Battery voltage divider to GPIO0", 0.02),
]

DEVICES = [
# ---------------------------------------------------------------------------
{
"id": "BFA-02", "slug": "breath-counter", "name": "Breath counter for childhood pneumonia",
"short": "A belly clip that counts a child's breaths for a full minute and applies WHO's fast-breathing cut-offs by age.",
"area": "Newborns and children", "status": "Design, rev A", "cost": 16,
"subtitle": "System: chest-wall motion in, WHO fast-breathing classification out",
"problem": [
    "Pneumonia kills more children under five than any other infection, and Pakistan carries one of the heaviest burdens in the world. At the front line, the test is a health worker counting breaths for sixty seconds and comparing the count to an age cut-off: 60 or more a minute under two months, 50 or more up to a year, 40 or more up to five years.",
    "Counting a squirming, crying infant's breaths by eye is hard, and studies of community health workers show counts that drift far from video-verified rates. A wrong count sends a sick child home or a healthy one to hospital."
],
"how": [
    "A puck the size of a matchbox sits on the child's belly under an elastic band. A six-axis motion sensor reads the rise and fall of the abdomen fifty times a second. Firmware filters out everything outside the breathing band (0.15 to 2 Hz), picks the axis carrying the most breathing signal, and counts complete cycles with an adaptive threshold.",
    "The health worker sets the child's age band with one button and starts the count with the other. After sixty seconds the screen shows the count and, if it crosses the WHO cut-off, the words FAST BREATHING. If the child moves too much, the count pauses and the minute is extended rather than guessed."
],
"validation": "Before any clinical use: bench test on a motorised breathing phantom at 20 to 90 breaths a minute, then a comparison against two clinicians counting from video in a paediatric ward, reported as a Bland-Altman analysis.",
"users": "Lady Health Workers and outpatient nurses",
"inputs": [
    {"title": "Motion sensor", "part": "LSM6DS3TR-C, U2", "lines": ["accelerometer + gyroscope", "abdominal motion, 50 Hz"], "bus": "I²C"},
    {"title": "Buttons", "part": "SW2 start, SW3 age band", "lines": ["<2 mo, 2–11 mo, 1–5 yr"], "bus": "GPIO"},
    {"title": "Battery monitor", "part": "R8/R9 divider", "lines": ["low-battery warning"], "bus": "ADC"},
],
"outputs": [
    {"title": "OLED display", "part": "SSD1306 128×64, U3", "lines": ["live count, timer, result"], "bus": "I²C"},
    {"title": "Buzzer", "part": "Passive piezo, LS1", "lines": ["start, end, movement tones"], "bus": "PWM"},
],
"mcu": dict(C3, note="Runs from battery, no phone needed"),
"steps": ["Sample 3 axes at 50 Hz", ["Band-pass 0.15–2 Hz", "(two biquad stages)"], "Choose axis with most power", ["Count cycles, adaptive", "hysteresis, 0.66 s minimum"], ["Pause on movement,", "extend the minute"], "Classify by WHO age cut-off"],
"power": LIPO_CHAIN(400), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-C3 SuperMini", "part": "U1",
          "left": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO5", "BTN_START"), ("GPIO6", "BTN_AGE"), ("GPIO7", "BUZZER"), ("GPIO0", "VBAT_SENSE"), ("5V", "VBAT")]},
"modules": [
    {"title": "Motion sensor", "part": "LSM6DS3TR-C breakout", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VIN", "3V3"), ("GND", "GND")]},
    {"title": "OLED 0.96 in", "part": "SSD1306, address 0x3C", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]},
    {"title": "Start button", "part": "SW2, to GND", "side": "R", "pins": [("1", "BTN_START"), ("2", "GND")]},
    {"title": "Age button", "part": "SW3, to GND", "side": "R", "pins": [("1", "BTN_AGE"), ("2", "GND")]},
    {"title": "Piezo buzzer", "part": "LS1, passive", "side": "R", "pins": [("+", "BUZZER"), ("−", "GND")]},
],
"bom": COMMON_C3_BOM(400, 3.20) + [
    ("U2", 1, "LSM6DS3TR-C breakout", "6-axis IMU, I²C", 3.50),
    ("U3", 1, "SSD1306 OLED 0.96 in", "128×64, I²C", 2.50),
    ("SW2, SW3", 2, "6 mm tactile switch", "Start, age band", 0.10),
    ("LS1", 1, "Passive piezo buzzer 12 mm", "", 0.30),
    ("Mech", 1, "Elastic belt 25 mm with buckle", "Holds puck on abdomen", 1.20),
    ("Mech", 1, "PLA or PETG print", "Enclosure, about 18 g", 0.60),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-03", "slug": "jaundice-meter", "name": "Transcutaneous jaundice meter",
"short": "A handheld probe that estimates bilirubin through a newborn's skin using reflected blue and green light.",
"area": "Newborns and children", "status": "Design, rev A", "cost": 25,
"subtitle": "System: skin reflectance spectrum in, jaundice index out",
"problem": [
    "Most newborns turn yellow in their first week. In a small number, bilirubin climbs high enough to cause permanent brain damage, and South Asia carries a large share of those cases. Catching the rise early depends on measuring it.",
    "Hospitals measure bilirubin with a blood test or with a transcutaneous meter that costs several thousand dollars. Most clinics in Pakistan have neither, so the decision rests on looking at the baby's skin colour, which is unreliable, and worse on darker skin."
],
"how": [
    "The probe tip is pressed against the baby's forehead or sternum until an internal spring trips a switch, so every reading uses the same pressure. That pressure also pushes blood out of the skin, which would otherwise swamp the signal.",
    "A white LED lights the skin and an eleven-channel spectral sensor reads the reflected light. Bilirubin absorbs strongly around 450 to 480 nm; haemoglobin and melanin absorb elsewhere. The firmware converts each channel to optical density against a white PTFE reference stored in the cap, then computes a jaundice index from the blue band minus the green band, corrected for skin pigment using the red channels.",
],
"validation": "The index must be calibrated against serum bilirubin drawn at the same time, across skin tones, before it can be reported in mg/dL. The planned study pairs readings with routine blood tests in a neonatal unit and fits the calibration openly.",
"users": "Neonatal nurses, lady health visitors, midwives",
"inputs": [
    {"title": "Spectral sensor", "part": "AS7341, U2", "lines": ["11 channels, 415–910 nm", "reflectance from skin"], "bus": "I²C"},
    {"title": "Probe switch", "part": "Micro switch, SW2", "lines": ["trips at fixed pressure"], "bus": "GPIO"},
    {"title": "Mode button", "part": "SW3", "lines": ["measure, average, white cal"], "bus": "GPIO"},
],
"outputs": [
    {"title": "Illumination", "part": "White LED via AS7341 LDR", "lines": ["4000 K, current-controlled"], "bus": "I²C"},
    {"title": "OLED display", "part": "SSD1306, U3", "lines": ["index, mean of 3, refer flag"], "bus": "I²C"},
    {"title": "Buzzer", "part": "LS1", "lines": ["reading taken"], "bus": "PWM"},
],
"mcu": dict(C3, note="White reference stored in flash"),
"steps": ["Wait for probe switch", "Dark frame, LED off", "Lit frame, 9 channels", ["Reflectance vs PTFE white,", "optical density per band"], ["Index = OD(445–480)", "− OD(555), pigment-corrected"], "Average 3 readings, flag"],
"power": LIPO_CHAIN(400), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-C3 SuperMini", "part": "U1",
          "left": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO5", "PROBE_SW"), ("GPIO6", "BTN_MODE"), ("GPIO7", "BUZZER"), ("GPIO0", "VBAT_SENSE"), ("5V", "VBAT")]},
"modules": [
    {"title": "Spectral sensor", "part": "AS7341 breakout, onboard LED", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VIN", "3V3"), ("GND", "GND")]},
    {"title": "OLED 0.96 in", "part": "SSD1306, 0x3C", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]},
    {"title": "Probe switch", "part": "SW2, normally open", "side": "R", "pins": [("COM", "GND"), ("NO", "PROBE_SW")]},
    {"title": "Mode button", "part": "SW3", "side": "R", "pins": [("1", "BTN_MODE"), ("2", "GND")]},
    {"title": "Piezo buzzer", "part": "LS1", "side": "R", "pins": [("+", "BUZZER"), ("−", "GND")]},
],
"bom": COMMON_C3_BOM(400, 3.20) + [
    ("U2", 1, "AS7341 breakout with LED", "11-channel spectral sensor, I²C", 12.00),
    ("U3", 1, "SSD1306 OLED 0.96 in", "128×64, I²C", 2.50),
    ("SW2", 1, "Micro switch, short lever", "Pressure trigger", 0.30),
    ("SW3", 1, "6 mm tactile switch", "Mode", 0.05),
    ("LS1", 1, "Passive piezo buzzer 12 mm", "", 0.30),
    ("Mech", 1, "PTFE disc 15 × 2 mm", "White reference in cap", 1.50),
    ("Mech", 1, "Compression spring 6 × 15 mm", "Sets probe force", 0.20),
    ("Mech", 1, "PETG print, black", "Light-tight body and probe", 1.20),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-04", "slug": "capillary-refill-timer", "name": "Capillary refill timer",
"short": "A fingertip cradle that times how fast blood returns after a standard press, in tenths of a second.",
"area": "Newborns and children", "status": "Design, rev A", "cost": 17,
"subtitle": "System: press force and fingertip reflectance in, refill time out",
"problem": [
    "Pressing a child's fingertip for five seconds and counting how long the colour takes to return is a standard bedside check for shock and severe dehydration. WHO emergency triage treats a refill time over three seconds as a danger sign.",
    "The test depends on how hard the clinician presses, how long, the light in the room, the child's skin tone and the clinician's counting. Two people timing the same child often disagree by a second or more, which is the entire width of the decision."
],
"how": [
    "The child's finger rests pad-down on a cradle with an optical sensor under the window. The clinician presses the nail with a plunger that has a force sensor in it; a bar on the screen shows when the press is in the target range, and the device counts the five seconds.",
    "When the plunger is released, the sensor under the fingertip watches the reflected infrared light return to its pre-press level. Refill time is reported as the moment the signal recovers ninety percent of the way back, to a tenth of a second. A skin thermistor warns when the finger is cold, since cold fingers refill slowly for reasons that have nothing to do with shock."
],
"validation": "Bench calibration of the force sensor with weights, then a comparison with slow-motion video timing by two clinicians on children presenting to an emergency department, with skin temperature recorded.",
"users": "Emergency and paediatric triage staff",
"inputs": [
    {"title": "Optical sensor", "part": "MAX30102, U2", "lines": ["red + IR reflectance, 100 Hz", "under the finger pad"], "bus": "I²C"},
    {"title": "Force sensor", "part": "FSR 402 in plunger", "lines": ["press force, target band"], "bus": "ADC"},
    {"title": "Skin thermistor", "part": "NTC 10 kΩ, RT1", "lines": ["cold-finger warning"], "bus": "ADC"},
],
"outputs": [
    {"title": "OLED display", "part": "SSD1306, U3", "lines": ["force bar, countdown, CRT"], "bus": "I²C"},
    {"title": "Buzzer", "part": "LS1", "lines": ["release cue at 5 s"], "bus": "PWM"},
],
"mcu": dict(C3, note="One button: start a measurement"),
"steps": ["2 s baseline, finger at rest", ["Guide press into force", "band, hold 5 s"], "Detect release from FSR", ["Track IR back to baseline", "at 100 Hz"], ["CRT = time to 90%", "recovery, 0.1 s steps"], "Flag 3 s or more; warn <30 °C"],
"power": LIPO_CHAIN(400), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-C3 SuperMini", "part": "U1",
          "left": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("GPIO1", "FSR"), ("GPIO2", "NTC"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO5", "BTN_START"), ("GPIO7", "BUZZER"), ("GPIO0", "VBAT_SENSE"), ("5V", "VBAT")]},
"modules": [
    {"title": "Optical sensor", "part": "MAX30102 breakout", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VIN", "3V3"), ("GND", "GND")]},
    {"title": "OLED 0.96 in", "part": "SSD1306, 0x3C", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]},
    {"title": "FSR + 10 kΩ", "part": "FSR to 3V3, R1 to GND", "side": "R", "pins": [("FSR a", "3V3"), ("FSR b", "FSR"), ("R1", "GND")]},
    {"title": "NTC + 10 kΩ", "part": "R2 to 3V3, NTC to GND", "side": "R", "pins": [("R2", "3V3"), ("mid", "NTC"), ("NTC", "GND")]},
    {"title": "Start button", "part": "SW2", "side": "R", "pins": [("1", "BTN_START"), ("2", "GND")]},
],
"bom": COMMON_C3_BOM(400, 3.20) + [
    ("U2", 1, "MAX30102 breakout", "Red/IR reflectance sensor, I²C", 2.20),
    ("U3", 1, "SSD1306 OLED 0.96 in", "128×64, I²C", 2.50),
    ("FSR1", 1, "Force-sensing resistor 12 mm", "FSR 402 or equivalent", 2.50),
    ("RT1", 1, "NTC thermistor 10 kΩ, B3950", "Skin temperature", 0.20),
    ("R1, R2", 2, "10 kΩ resistor", "Dividers", 0.02),
    ("SW2", 1, "12 mm tactile switch", "Start", 0.10),
    ("LS1", 1, "Passive piezo buzzer 12 mm", "", 0.30),
    ("Mech", 1, "Clear acrylic disc 12 × 1 mm", "Sensor window", 0.30),
    ("Mech", 1, "PETG print", "Cradle and plunger", 1.00),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-05", "slug": "freezing-of-gait-anklet", "name": "Freezing-of-gait anklet",
"short": "An ankle pod that detects a Parkinson's freeze from the leg's trembling and starts a vibration rhythm to restart walking.",
"area": "Neurology and rehabilitation", "status": "Design, rev A", "cost": 14,
"subtitle": "System: shank motion in, rhythmic vibration cue out",
"problem": [
    "Many people with advanced Parkinson's disease freeze in the middle of walking, most often at doorways and turns: the feet stop while the body keeps moving. Freezing is one of the main causes of falls in Parkinson's, and medication controls it poorly.",
    "A steady external rhythm, a metronome or a pulse on the skin, helps many patients restart. The problem is delivering it at the right moment, without the patient having to reach for anything."
],
"how": [
    "A pod strapped above the ankle samples the shank's motion sixty-four times a second. During a freeze the leg trembles at 3 to 8 Hz instead of swinging at walking speed. Every half second the firmware computes the freeze index, the ratio of power in that trembling band to power in the walking band (0.5 to 3 Hz), over the last four seconds.",
    "When the index crosses the patient's threshold, two vibration motors pulse at the patient's own walking cadence until normal stepping resumes, then for three seconds more. Each episode is logged with its time and duration, and the log can be read over Bluetooth for the neurologist."
],
"validation": "Threshold tuning on a published labelled freezing dataset, then supervised walking trials with patients through a doorway course, scored from video by a movement-disorders clinician.",
"users": "People with Parkinson's and their neurologists",
"inputs": [
    {"title": "Motion sensor", "part": "LSM6DS3TR-C, U2", "lines": ["vertical shank acceleration", "64 Hz"], "bus": "I²C"},
    {"title": "Button", "part": "SW2", "lines": ["manual cue on/off, cadence set"], "bus": "GPIO"},
    {"title": "Battery monitor", "part": "R8/R9 divider", "lines": ["low-battery pulse"], "bus": "ADC"},
],
"outputs": [
    {"title": "Vibration motors", "part": "2 × 10 mm ERM, Q1", "lines": ["rhythmic cue at cadence"], "bus": "PWM"},
    {"title": "Episode log", "part": "BLE to phone", "lines": ["time, duration per freeze"], "bus": "BLE", "wireless": True},
],
"mcu": dict(C3, note="Episodes kept in flash between reads"),
"steps": ["Sample vertical axis, 64 Hz", ["4 s window, FFT every", "0.5 s (256 points)"], ["Freeze index = power", "3–8 Hz ÷ power 0.5–3 Hz"], "Ignore if standing still", ["Above threshold: pulse", "motors at cadence"], "Log episode, BLE on request"],
"power": LIPO_CHAIN(300), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-C3 SuperMini", "part": "U1",
          "left": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO10", "MOTOR"), ("GPIO5", "BTN"), ("GPIO0", "VBAT_SENSE"), ("5V", "VBAT")]},
"modules": [
    {"title": "Motion sensor", "part": "LSM6DS3TR-C breakout", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VIN", "3V3"), ("GND", "GND")]},
    {"title": "Motor driver", "part": "AO3400 MOSFET + 1N4148", "side": "R", "pins": [("Gate", "MOTOR"), ("Drain", "M−"), ("Source", "GND")]},
    {"title": "Vibration motors", "part": "M1, M2 in parallel", "side": "R", "pins": [("+", "VBAT"), ("−", "M−")]},
    {"title": "Button", "part": "SW2", "side": "R", "pins": [("1", "BTN"), ("2", "GND")]},
],
"bom": COMMON_C3_BOM(300, 3.00) + [
    ("U2", 1, "LSM6DS3TR-C breakout", "6-axis IMU, I²C", 3.50),
    ("M1, M2", 2, "10 mm coin vibration motor", "3 V ERM", 0.40),
    ("Q1", 1, "AO3400 N-MOSFET", "Low-side motor switch", 0.05),
    ("D1", 1, "1N4148 diode", "Flyback across motors", 0.02),
    ("R3", 1, "100 kΩ resistor", "Gate pull-down", 0.01),
    ("SW2", 1, "6 mm tactile switch", "", 0.05),
    ("Mech", 1, "Hook-and-loop strap 30 mm", "Above the ankle", 1.50),
    ("Mech", 1, "PETG print", "Pod, about 14 g", 0.50),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-06", "slug": "stroke-rehab-glove", "name": "Stroke hand-rehabilitation glove",
"short": "A glove with a bend sensor on each finger that measures range of motion and counts exercise repetitions at home.",
"area": "Neurology and rehabilitation", "status": "Design, rev A", "cost": 33,
"subtitle": "System: finger flexion and wrist rotation in, session record out",
"problem": [
    "After a stroke, recovery of the hand depends on thousands of repetitions in the months after discharge. Almost all of that work happens at home, and the physiotherapist sees the patient for a few minutes every few weeks.",
    "Neither the patient nor the therapist can see whether the hand is actually improving between visits, or whether the exercises are being done at all. A measured trend would let a therapist adjust the programme instead of guessing."
],
"how": [
    "A soft cotton glove carries a flex sensor along the back of each finger and a small pod on the back of the hand. Each sensor changes resistance as the finger bends; the pod reads all five fifty times a second, along with wrist rotation from a motion sensor.",
    "A thirty-second calibration (open hand, then fist) maps each finger to 0 to 100 percent of the patient's own range. The firmware counts a repetition each time a finger goes past 70 percent and back below 30, and keeps per-session totals and peak range for each finger. The record streams over Bluetooth to a phone, which is where the exercise app comes next."
],
"validation": "Comparison of glove-measured joint range against goniometer measurements by a physiotherapist, then a home-use feasibility study tracking adherence for four weeks.",
"users": "Stroke survivors and physiotherapists",
"inputs": [
    {"title": "5 flex sensors", "part": "2.2 in, FS1–FS5", "lines": ["one per finger, 47 kΩ dividers"], "bus": "ADC ×5"},
    {"title": "Motion sensor", "part": "LSM6DS3TR-C, U2", "lines": ["wrist pronation/supination"], "bus": "I²C"},
    {"title": "Button", "part": "SW2", "lines": ["calibrate, start session"], "bus": "GPIO"},
],
"outputs": [
    {"title": "Session record", "part": "BLE to phone", "lines": ["flexion %, reps, peak range"], "bus": "BLE", "wireless": True},
    {"title": "Status LED", "part": "Onboard RGB", "lines": ["calibrating, recording"], "bus": "GPIO"},
],
"mcu": dict(S3, note="ESP32-S3 for ten ADC1 channels"),
"steps": ["Read 5 fingers at 50 Hz", "Smooth, exponential 0.2", ["Map to % of calibrated", "open–fist range"], ["Rep = >70% then <30%,", "per finger"], "Track peak range per session", "Notify BLE at 10 Hz"],
"power": LIPO_CHAIN(500), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-S3 SuperMini", "part": "U1",
          "left": [("GPIO1", "THUMB"), ("GPIO2", "INDEX"), ("GPIO3", "MIDDLE"), ("GPIO4", "RING"), ("GPIO5", "LITTLE"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("GPIO6", "BTN"), ("GPIO7", "VBAT_SENSE"), ("5V", "VBAT")]},
"modules": [
    {"title": "Flex dividers", "part": "FSn to 3V3, 47 kΩ to GND", "side": "L", "pins": [("FS1", "THUMB"), ("FS2", "INDEX"), ("FS3", "MIDDLE"), ("FS4", "RING"), ("FS5", "LITTLE"), ("Top", "3V3"), ("Bottom", "GND")]},
    {"title": "Motion sensor", "part": "LSM6DS3TR-C breakout", "side": "R", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VIN", "3V3"), ("GND", "GND")]},
    {"title": "Button", "part": "SW2", "side": "R", "pins": [("1", "BTN"), ("2", "GND")]},
],
"bom": [
    ("U1", 1, "ESP32-S3 SuperMini", "Microcontroller board, USB-C, onboard RGB LED", 5.50),
    ("U9", 1, "TP4056 USB-C module", "1 A Li-ion charger with DW01 protection", 0.60),
    ("BT1", 1, "LiPo cell 3.7 V 500 mAh", "With JST-PH lead", 3.50),
    ("SW1", 1, "SS12D00 slide switch", "Main power", 0.10),
    ("R8, R9", 2, "100 kΩ resistor", "Battery divider to GPIO7", 0.02),
    ("FS1–FS5", 5, "Flex sensor 2.2 in", "Bend-sensitive resistor", 3.50),
    ("R1–R5", 5, "47 kΩ resistor", "Divider per finger", 0.02),
    ("U2", 1, "LSM6DS3TR-C breakout", "6-axis IMU, I²C", 3.50),
    ("SW2", 1, "6 mm tactile switch", "", 0.05),
    ("Mech", 1, "Cotton glove + sewn sensor sleeves", "Machine-washable with pod removed", 2.00),
    ("Mech", 1, "Ribbon cable 7-way, 15 cm", "Sensors to pod", 0.40),
    ("Mech", 1, "PETG print", "Hand pod", 0.50),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-07", "slug": "anaemia-screener", "name": "Needle-free anaemia screener",
"short": "A fingertip clip that shines five wavelengths through the finger and estimates haemoglobin without a blood sample.",
"area": "Clinic screening", "status": "Design, rev A", "cost": 22,
"subtitle": "System: five-wavelength transmission in, haemoglobin estimate out",
"problem": [
    "About four in ten women of reproductive age in Pakistan are anaemic (WHO, 2019). Anaemia in pregnancy raises the risk of haemorrhage, low birth weight and maternal death, and it is cheap to treat once found.",
    "Finding it usually means a finger prick and a reagent cuvette or a lab, which costs money per test and needs sharps disposal. A test that costs nothing per use could screen every woman at every antenatal visit."
],
"how": [
    "The finger sits in a light-tight clip between five LEDs (530, 590, 660, 810 and 940 nm) and a photodiode with a built-in amplifier. The LEDs fire one at a time, with a dark frame between, about seventy-five times a second for twenty seconds.",
    "Each wavelength produces a pulse waveform. Its pulsing part comes from arterial blood; its steady part from everything else. Ratios of pulsing to steady light across pairs of wavelengths change with haemoglobin concentration, and a regression model turns those ratios into an estimate in g/dL. The screen shows the estimate and flags it against the WHO cut-off for the person's group."
],
"validation": "The regression must be fitted against laboratory haemoglobin across skin tones before the device reports g/dL; until then it shows raw ratios. The planned study pairs readings with venous haemoglobin at an antenatal clinic.",
"users": "Antenatal clinics, lady health visitors, school health programmes",
"inputs": [
    {"title": "Photodetector", "part": "OPT101 into ADS1115, U4 + U2", "lines": ["transmitted light, 16-bit", "860 samples/s"], "bus": "I²C"},
    {"title": "Button", "part": "SW2", "lines": ["start; group select"], "bus": "GPIO"},
    {"title": "Battery monitor", "part": "R8/R9 divider", "lines": ["low-battery warning"], "bus": "ADC"},
],
"outputs": [
    {"title": "LED array", "part": "530/590/660/810/940 nm", "lines": ["one at a time, Q1–Q5"], "bus": "GPIO ×5"},
    {"title": "OLED display", "part": "SSD1306, U3", "lines": ["Hb estimate, WHO flag"], "bus": "I²C"},
    {"title": "Buzzer", "part": "LS1", "lines": ["done"], "bus": "PWM"},
],
"mcu": dict(C3, note="Calibration model kept in flash"),
"steps": [["Cycle dark + 5 LEDs, about", "75 frames/s for 20 s"], "Subtract dark from each", ["Per wavelength: AC (pulse)", "and DC (mean)"], ["Ratios of AC/DC between", "wavelength pairs"], ["Hb = model(ln ratios)", "from calibration"], "Flag against WHO cut-off"],
"power": LIPO_CHAIN(400), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-C3 SuperMini", "part": "U1",
          "left": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO1", "LED_530"), ("GPIO3", "LED_590"), ("GPIO4", "LED_660"), ("GPIO5", "LED_810"), ("GPIO6", "LED_940"), ("GPIO10", "BTN"), ("GPIO7", "BUZZER"), ("GPIO0", "VBAT_SENSE")]},
"modules": [
    {"title": "16-bit ADC", "part": "ADS1115 breakout, 0x48", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("A0", "PD_OUT"), ("VDD", "3V3"), ("GND", "GND")]},
    {"title": "Photodiode amp", "part": "OPT101, 1 MΩ feedback", "side": "L", "pins": [("Vout", "PD_OUT"), ("V+", "3V3"), ("GND", "GND")]},
    {"title": "OLED 0.96 in", "part": "SSD1306, 0x3C", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]},
    {"title": "LED drivers ×5", "part": "2N7002 low-side, LED + R to 3V3", "side": "R", "pins": [("G1", "LED_530"), ("G2", "LED_590"), ("G3", "LED_660"), ("G4", "LED_810"), ("G5", "LED_940"), ("S", "GND")]},
    {"title": "Button", "part": "SW2", "side": "R", "pins": [("1", "BTN"), ("2", "GND")]},
],
"bom": COMMON_C3_BOM(400, 3.20) + [
    ("U2", 1, "ADS1115 breakout", "16-bit ADC, I²C", 2.50),
    ("U4", 1, "OPT101 photodiode + TIA", "DIP-8", 4.50),
    ("D1–D5", 5, "LEDs 530, 590, 660, 810, 940 nm", "3 mm or 5 mm, narrow band", 0.30),
    ("Q1–Q5", 5, "2N7002 N-MOSFET", "LED switches", 0.05),
    ("R10–R14", 5, "Series resistors 68–150 Ω", "Set per LED for equal DC level", 0.02),
    ("U3", 1, "SSD1306 OLED 0.96 in", "128×64, I²C", 2.50),
    ("SW2", 1, "6 mm tactile switch", "", 0.05),
    ("LS1", 1, "Passive piezo buzzer 12 mm", "", 0.30),
    ("Mech", 1, "Black PETG print + foam liner", "Light-tight finger clip", 1.50),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-08", "slug": "open-spirometer", "name": "Open spirometer",
"short": "A 3D-printed flow tube and a differential pressure sensor that measure FEV1, FVC and peak flow from one hard breath out.",
"area": "Clinic screening", "status": "Design, rev A", "cost": 44,
"subtitle": "System: pressure drop across a mesh in, flow-volume curve out",
"problem": [
    "Chronic lung disease is common in Pakistan, driven by tobacco, cooking smoke from wood and dung, and lung damage left behind by tuberculosis. Spirometry, the test that measures how much air the lungs can move and how fast, is how these conditions are diagnosed and graded.",
    "Outside large hospitals, spirometers are rare, and an office unit usually costs several hundred dollars or more. Patients with chronic obstructive lung disease are often labelled with asthma, or with nothing, for years."
],
"how": [
    "The patient blows as hard and long as possible through a disposable mouthpiece into a printed tube with a fine stainless steel mesh across it. Air through the mesh produces a small pressure drop proportional to flow. A Sensirion differential pressure sensor reads that drop two hundred times a second.",
    "Firmware converts pressure to flow using a constant set with a 3-litre calibration syringe, integrates flow into volume, finds the start of the blow by back-extrapolation, and reports FEV1 (volume in the first second), FVC (total volume), their ratio and peak flow. A ratio under 0.70 is flagged as possible obstruction, which then needs a repeat test after a bronchodilator. The full flow-volume curve streams over Bluetooth."
],
"validation": "Calibration and linearity check with a 3-litre syringe at several speeds against the ATS/ERS accuracy limit of ±3 percent, then side-by-side testing against a hospital spirometer in a chest clinic.",
"users": "Chest clinics, TB programmes, general practitioners",
"inputs": [
    {"title": "Differential pressure", "part": "Sensirion SDP810-500Pa, U2", "lines": ["±500 Pa, 200 Hz", "taps either side of mesh"], "bus": "I²C"},
    {"title": "Button", "part": "SW2", "lines": ["zero, start, next blow"], "bus": "GPIO"},
    {"title": "Battery monitor", "part": "R8/R9 divider", "lines": ["low-battery warning"], "bus": "ADC"},
],
"outputs": [
    {"title": "OLED display", "part": "SSD1306, U3", "lines": ["FEV1, FVC, ratio, PEF"], "bus": "I²C"},
    {"title": "Flow-volume curve", "part": "BLE to phone", "lines": ["samples at 200 Hz"], "bus": "BLE", "wireless": True},
    {"title": "Buzzer", "part": "LS1", "lines": ["blow, keep going, stop"], "bus": "PWM"},
],
"mcu": dict(C3, note="Flow constant set with 3 L syringe"),
"steps": ["Zero sensor, no flow", "Read ΔP at 200 Hz", ["Flow = ΔP ÷ R (mesh)", "× BTPS factor"], "Integrate to volume", ["Back-extrapolate start;", "FEV1, FVC, PEF"], "Flag FEV1/FVC < 0.70"],
"power": LIPO_CHAIN(400), "rail": "VBAT to 5V pin, onboard LDO to 3V3",
"board": {"title": "ESP32-C3 SuperMini", "part": "U1",
          "left": [("GPIO8", "SDA"), ("GPIO9", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("GPIO5", "BTN"), ("GPIO7", "BUZZER"), ("GPIO0", "VBAT_SENSE"), ("5V", "VBAT")]},
"modules": [
    {"title": "Pressure sensor", "part": "SDP810-500Pa, 0x25", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VDD", "3V3"), ("GND", "GND")]},
    {"title": "OLED 0.96 in", "part": "SSD1306, 0x3C", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]},
    {"title": "Button", "part": "SW2", "side": "R", "pins": [("1", "BTN"), ("2", "GND")]},
    {"title": "Piezo buzzer", "part": "LS1", "side": "R", "pins": [("+", "BUZZER"), ("−", "GND")]},
],
"bom": COMMON_C3_BOM(400, 3.20) + [
    ("U2", 1, "Sensirion SDP810-500Pa", "Differential pressure, I²C, with tube ports", 30.00),
    ("U3", 1, "SSD1306 OLED 0.96 in", "128×64, I²C", 2.50),
    ("Mech", 1, "Stainless mesh disc, 400 mesh, Ø30 mm", "Flow resistance", 1.20),
    ("Mech", 2, "Silicone tube 3 mm ID, 6 cm", "Pressure taps to sensor", 0.20),
    ("Mech", 1, "Cardboard mouthpiece 30 mm", "Single-use, per patient", 0.10),
    ("SW2", 1, "12 mm tactile switch", "", 0.10),
    ("LS1", 1, "Passive piezo buzzer 12 mm", "", 0.30),
    ("Mech", 1, "PETG print", "Flow head and body", 1.80),
],
},
# ---------------------------------------------------------------------------
{
"id": "BFA-09", "slug": "clubfoot-brace-sensor", "name": "Clubfoot brace adherence sensor",
"short": "A coin-sized temperature logger inside a clubfoot brace that tells the clinic how many hours a day it was worn.",
"area": "Newborns and children", "status": "Design, rev A", "cost": 17,
"subtitle": "System: in-shoe temperature in, daily hours worn out",
"problem": [
    "Clubfoot affects about one in every thousand babies. The Ponseti method corrects almost every case with casts and a small operation, but the correction only holds if the child wears a foot-abduction brace for most of the day for three months and then at night until about age four.",
    "Families stop using the brace for understandable reasons, and relapse follows. At follow-up the clinic has to rely on what the parents remember, so it cannot tell which families need help until the foot has already turned back in."
],
"how": [
    "A sealed capsule the size of a large coin clips inside one of the brace's shoes. A precision temperature sensor reads every ten minutes; between readings the board sleeps on a few microamps. When the shoe is on a foot, its temperature sits close to skin temperature; when it is off, it falls towards room temperature.",
    "The firmware classifies each reading as worn or not worn, with hysteresis so a cool morning does not count as removal, and adds up hours worn per day. At follow-up the nurse presses the capsule's button and reads months of daily totals on a phone over Bluetooth. A charge lasts several months between visits."
],
"validation": "Bench tests against a logged heating pad to set thresholds across room temperatures, then a pilot with families at a Ponseti clinic comparing sensor totals with a daily diary.",
"users": "Ponseti clinics and the families they treat",
"inputs": [
    {"title": "Temperature sensor", "part": "TMP117, U2", "lines": ["±0.1 °C, every 10 min"], "bus": "I²C"},
    {"title": "Button", "part": "SW2", "lines": ["wake radio for clinic read"], "bus": "GPIO"},
],
"outputs": [
    {"title": "Daily log", "part": "BLE to clinic phone", "lines": ["hours worn per day", "raw readings on request"], "bus": "BLE", "wireless": True},
    {"title": "Status LED", "part": "Onboard", "lines": ["one blink: logging"], "bus": "GPIO"},
],
"mcu": NRF,
"steps": ["Wake every 10 minutes", "Read TMP117 one-shot", ["Worn if >30.5 °C, off", "if <28.0 °C (hysteresis)"], "Store byte to flash ring", "Sum hours per day", ["Button: advertise BLE", "for 2 minutes"]],
"power": [("USB-C 5 V", "charge at clinic"), ("XIAO charger", "BQ25101 onboard"), ("LiPo 3.7 V", "BT1, 100 mAh")],
"rail": "VBAT to XIAO, onboard regulator to 3V3",
"board": {"title": "Seeed XIAO nRF52840", "part": "U1",
          "left": [("D4", "SDA"), ("D5", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
          "right": [("D1", "BTN"), ("BAT+", "VBAT"), ("BAT−", "GND")]},
"modules": [
    {"title": "Temperature sensor", "part": "TMP117 breakout, 0x48", "side": "L", "pins": [("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]},
    {"title": "Button", "part": "SW2, sealed", "side": "R", "pins": [("1", "BTN"), ("2", "GND")]},
    {"title": "LiPo 100 mAh", "part": "BT1, 401230", "side": "R", "pins": [("+", "VBAT"), ("−", "GND")]},
],
"bom": [
    ("U1", 1, "Seeed XIAO nRF52840", "BLE board with onboard Li-ion charger", 9.90),
    ("U2", 1, "TMP117 breakout", "±0.1 °C digital temperature sensor", 4.00),
    ("BT1", 1, "LiPo 3.7 V 100 mAh", "401230 cell", 2.20),
    ("SW2", 1, "Sealed tactile switch 6 mm", "IP67", 0.40),
    ("Mech", 1, "PETG print + silicone gasket", "Ø36 mm capsule, clip", 0.60),
],
},
]

BFA01 = {
    "id": "BFA-01", "slug": "bells-palsy-asymmetry", "name": "Facial-asymmetry grading for Bell's palsy",
    "short": "A landmark-based pipeline that measures facial asymmetry from an ordinary photograph, built for clinics without a trained examiner.",
    "area": "Neurology and rehabilitation", "status": "Preprint",
    "preprint": "https://www.researchsquare.com/article/rs-11393331/v1",
    "doi": "10.21203/rs.3.rs-11393331/v1",
}


def bom_total(d):
    return round(sum(q * p for _, q, _, _, p in d["bom"]), 2)


if __name__ == "__main__":
    for d in DEVICES:
        print(d["id"], d["name"], "BOM $", bom_total(d), "stated", d["cost"])
