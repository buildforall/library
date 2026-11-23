"""Regenerates the READMEs and parts lists from tools/devices.py.

    python3 tools/build_library.py                  # all builds
    python3 tools/build_library.py jaundice-meter   # one build
    python3 tools/build_library.py --enclosures     # also re-export STEP/STL (needs cadquery)

Writes, per build: README.md and hardware/bom.csv; with --enclosures,
enclosure/*.step and enclosure/*.stl as well. Firmware is written by hand
and is not touched.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import devices  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# How each build's firmware is laid out, flashed and tested. The toolchain
# suits the board and the job: Python where the maths benefits from quick
# iteration, C or Rust where timing or memory is tight, Zephyr on the nRF52840.
FIRMWARE = {
    "breath-counter": dict(
        lang="MicroPython",
        tree=[
            ("main.py", "runs at boot: buttons, screen, buzzer"),
            ("breath.py", "filtering and breath counting, no hardware calls"),
            ("lsm6ds3.py", "accelerometer driver"),
            ("tests/", "pytest, synthetic breathing signals"),
        ],
        flash="Install MicroPython for the ESP32-C3 (the *ESP32_GENERIC_C3* image from micropython.org), then from `firmware/` run `mpremote mip install ssd1306` and `mpremote cp main.py breath.py lsm6ds3.py :`. Reset the board.",
        test="cd firmware && pytest tests/",
    ),
    "jaundice-meter": dict(
        lang="Rust",
        tree=[
            ("Cargo.toml", "esp-hal, no_std"),
            ("src/main.rs", "probe, buttons, screen, measurement loop"),
            ("src/as7341.rs", "spectral sensor driver"),
            ("src/optics.rs", "optical density, melanin correction, jaundice index"),
        ],
        flash="Install Rust with rustup and then espflash (`cargo install espflash`). From `firmware/`, `cargo run --release` builds for the ESP32-C3, flashes over USB and opens the serial monitor. The serum-bilirubin calibration goes in `CALIBRATION` in `src/optics.rs`.",
        test=None,
    ),
    "capillary-refill-timer": dict(
        lang="C, ESP-IDF",
        tree=[
            ("main/main.c", "hardware set-up, screens, the measurement loop"),
            ("main/crt.c, crt.h", "the refill state machine, no hardware calls"),
            ("main/max30102.c", "optical sensor driver"),
            ("main/oled.c", "display driver and 6x8 font"),
            ("tests/", "host tests with simulated refills"),
        ],
        flash="With ESP-IDF 5.x: `idf.py set-target esp32c3`, then `idf.py build flash monitor` from `firmware/`. Or with PlatformIO: `pio run -t upload`. The force band is set in `main/crt.h`.",
        test="make -C firmware/tests",
    ),
    "freezing-of-gait-anklet": dict(
        lang="C++, PlatformIO",
        tree=[
            ("platformio.ini", "board and library versions"),
            ("src/main.cpp", "sensor, motors, button, Bluetooth"),
            ("lib/FreezeIndex/", "freeze index, cadence and cue logic"),
            ("test/test_freeze_index/", "unit tests that run on a computer"),
        ],
        flash="With PlatformIO, from `firmware/`: `pio run -e supermini -t upload`. The libraries (Adafruit LSM6DS, NimBLE-Arduino) are fetched on the first build.",
        test="cd firmware && pio test -e native",
    ),
    "stroke-rehab-glove": dict(
        lang="Arduino",
        tree=[("rehab_glove/rehab_glove.ino", "the whole sketch")],
        flash="Arduino IDE 2 with Espressif's **esp32** core 4.x. Board: *ESP32S3 Dev Module*, with *USB CDC On Boot* enabled. Library from the Library Manager: Adafruit LSM6DS. Bluetooth comes with the core.",
        test=None,
    ),
    "anaemia-screener": dict(
        lang="CircuitPython",
        tree=[
            ("code.py", "runs at boot: LEDs, button, screen"),
            ("hb.py", "AC/DC separation and log ratios, no hardware calls"),
            ("ads1115.py", "16-bit ADC driver"),
            ("model.example.json", "where fitted coefficients go"),
            ("tests/", "pytest, synthetic pulse signals"),
        ],
        flash="Install CircuitPython 9 or later for the ESP32-C3, copy `code.py`, `hb.py` and `ads1115.py` to the board, and install the two display libraries with `circup install -r requirements.txt`. Once coefficients have been fitted, copy `model.example.json` to `model.json` on the board and fill them in.",
        test="cd firmware && pytest tests/",
    ),
    "open-spirometer": dict(
        lang="C++17, ESP-IDF",
        tree=[
            ("main/main.cpp", "set-up, calibration, measurement"),
            ("main/spirometry.hpp", "flow, volume, back-extrapolation, BTPS"),
            ("main/sdp810.cpp", "pressure sensor driver"),
            ("main/curve_service.cpp", "Bluetooth LE service (NimBLE)"),
            ("main/display.cpp", "display driver"),
            ("tests/", "host tests with simulated blows"),
        ],
        flash="With ESP-IDF 5.x: `idf.py set-target esp32c3`, then `idf.py build flash monitor` from `firmware/`. Or with PlatformIO: `pio run -t upload`.",
        test="make -C firmware/tests",
    ),
    "clubfoot-brace-sensor": dict(
        lang="Zephyr RTOS",
        tree=[
            ("prj.conf", "Bluetooth, I2C, LittleFS"),
            ("boards/xiao_ble.overlay", "sensor, button and log partition on the XIAO"),
            ("src/main.c", "sampling, log file, Bluetooth service"),
            ("src/wearlog.c", "encoding and daily summaries, no hardware calls"),
            ("tests/", "host tests for the summaries"),
        ],
        flash="With Zephyr 4.x and west: `west build -b xiao_ble firmware`. Double-tap the XIAO's reset button and copy `build/zephyr/zephyr.uf2` to the drive that appears. `boards/nrf52840dk_nrf52840.overlay` builds the same app for an nRF52840 DK on the bench.",
        test="make -C firmware/tests",
    ),
}

ASSEMBLY = {
    "breath-counter": [
        "Stick the motion sensor flat to the floor of the base with foam tape, X axis along the long side. It must not rattle.",
        "Seat the OLED behind the window and the two buttons in the lid; the buzzer sits under the small vent.",
        "Thread a 25 mm elastic band through both side lugs.",
        "Test on yourself: lie down, put the puck on your abdomen, count your own breaths for a minute and compare. Then try breathing fast.",
    ],
    "jaundice-meter": [
        "Print the body in black PETG so no outside light reaches the sensor; paint the inside of the nose matte black if you print in white.",
        "Mount the AS7341 board at the back of the nose, sensor and LED facing the aperture.",
        "Fit the spring between the nose and the micro switch so it only trips when the tip is pressed firmly against skin.",
        "Glue the PTFE disc into the cap. Press MODE, push the probe into the cap and the white reference is saved. Redo it weekly.",
    ],
    "capillary-refill-timer": [
        "Glue the clear window into the cradle with the MAX30102 directly underneath, facing up.",
        "Stack the force sensor under the plunger head so the whole press goes through it.",
        "Bed the thermistor beside the window with a little thermal paste.",
        "Set the force band: rest 1 kg, then 2 kg on the plunger, note the millivolts in the serial log and put them in `CRT_FSR_LOW_MV` and `CRT_FSR_HIGH_MV`.",
    ],
    "freezing-of-gait-anklet": [
        "Glue both vibration motors to the inner (skin) face of the pod.",
        "Wear it on the outside of the leg, a hand's width above the ankle bone, strap snug.",
        "Start with a threshold of 2.0. With the neurologist, connect over Bluetooth (nRF Connect works) and write T and a number, such as T2.4, to the settings characteristic to tune it.",
    ],
    "stroke-rehab-glove": [
        "Sew a fabric sleeve along the back of each finger and slide a flex sensor in, printed side up, connector at the knuckle.",
        "Run the ribbon from the sensors to the pod. The pod lifts off so the glove can be washed.",
        "Calibrate per patient: hold the button 2 s. Blue: open the hand. Amber: make a fist. Green: saved.",
        "A short press starts or ends a session. Live data and the session summary are readable over Bluetooth.",
    ],
    "anaemia-screener": [
        "Put the five LEDs in a row in the upper shell, pointing down through the finger, with the OPT101 opposite in the lower shell.",
        "Line the finger channel with black foam so it closes around the finger and blocks room light.",
        "With a finger in, pick each LED's series resistor so the DC levels in the serial log come out similar (about 1.5 to 2.5 V).",
        "Every reading prints AC, DC and the four log ratios to the serial console. Pair them with a lab haemoglobin to build the calibration set.",
    ],
    "open-spirometer": [
        "Clamp the stainless mesh disc in the flange between the two halves of the flow tube.",
        "Connect the mouth-side tap to the sensor's + port and the other tap to the − port.",
        "Calibrate before first use and weekly: hold the button while switching on, then push a 3 L syringe through at a steady speed.",
        "New cardboard mouthpiece and a nose clip for every patient.",
    ],
    "clubfoot-brace-sensor": [
        "Flash and test before sealing; the LED blinks once at every reading.",
        "Press the TMP117 against the capsule wall that faces the foot, with a dab of thermal paste.",
        "Close the cap over the gasket and clip the capsule inside the brace shoe, behind the heel.",
        "At follow-up: press the button, connect over Bluetooth, turn on notifications for the data characteristic and write S for the daily summary.",
    ],
}


def md_table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def export_enclosures(d):
    import cadquery as cq
    import enclosures

    enc = os.path.join(ROOT, "builds", d["slug"], "enclosure")
    os.makedirs(enc, exist_ok=True)
    for old in os.listdir(enc):
        os.remove(os.path.join(enc, old))
    _, parts = enclosures.BUILDERS[d["slug"]]()
    for name, solid in parts.items():
        cq.exporters.export(solid, os.path.join(enc, f"{name}.step"))
        cq.exporters.export(solid, os.path.join(enc, f"{name}.stl"), tolerance=0.05, angularTolerance=0.2)


def enclosure_parts(slug):
    enc = os.path.join(ROOT, "builds", slug, "enclosure")
    return sorted({os.path.splitext(f)[0] for f in os.listdir(enc)}) if os.path.isdir(enc) else []


def build(d, with_enclosures=False):
    slug = d["slug"]
    folder = os.path.join(ROOT, "builds", slug)
    hw = os.path.join(folder, "hardware")
    os.makedirs(hw, exist_ok=True)
    with open(os.path.join(hw, "bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ref", "qty", "part", "notes", "unit_usd"])
        for ref, q, part, note, p in d["bom"]:
            w.writerow([ref, q, part, note, f"{p:.2f}"])
    if with_enclosures:
        export_enclosures(d)

    fw = FIRMWARE[slug]
    width = max(len(name) for name, _ in fw["tree"]) + 3
    tree = [f"│   {'└' if i == len(fw['tree']) - 1 else '├'}── {name.ljust(width)}{note}"
            for i, (name, note) in enumerate(fw["tree"])]
    parts = enclosure_parts(slug)
    pins = d["board"]["left"] + d["board"]["right"]
    total = devices.bom_total(d)
    lines = [
        f'# {d["name"]}', "",
        d["short"], "",
        f'**Who it is for:** {d["users"]}  ',
        f'**Board:** {d["mcu"]["title"]}  ',
        f'**Firmware:** {fw["lang"]}  ',
        f'**Parts:** about ${total:.0f} for one unit at 2026 retail prices', "",
        "> This is a design that has not yet been tested on patients. Do not use it to make decisions about anyone's care until the testing described at the end of this page has been done.", "",
        "## Why", "", *[p + "\n" for p in d["problem"]],
        "## How it works", "", *[p + "\n" for p in d["how"]],
        "## What is in this folder", "",
        "```",
        f"{slug}/",
        "├── firmware/",
        *tree,
        "├── hardware/",
        "│   └── bom.csv         parts list with prices",
        "└── enclosure/          STEP to edit, STL to print",
        *[f"    {'└' if i == len(parts) - 1 else '├'}── {p}.step / .stl" for i, p in enumerate(parts)],
        "```", "",
        "## Wiring", "",
        md_table(pins, ["Board pin", "Connects to"]), "",
        "## Parts", "",
        md_table([(r, q, p, n) for r, q, p, n, _ in d["bom"]], ["Ref", "Qty", "Part", "Notes"]), "",
        f"Prices for each line are in `hardware/bom.csv`; the total is about ${total:.0f}.", "",
        "## Build", "",
        "1. Print the parts in `enclosure/` in PETG at 0.2 mm layers with three walls.",
        "2. Wire everything as in the table above. Keep the I²C wires under 10 cm.",
        f"3. Flash the firmware. {fw['flash']}",
        *[f"{i}. {s}" for i, s in enumerate(ASSEMBLY[slug], 4)], "",
    ]
    if fw["test"]:
        lines += ["The signal processing has tests that run on a computer, no hardware needed:", "",
                  "```", fw["test"], "```", ""]
    lines += [
        "## Testing before clinical use", "", d["validation"], "",
        "If you build one, open an issue with what worked and what did not. Test data is the most useful thing anyone can send back.", "",
    ]
    open(os.path.join(folder, "README.md"), "w").write("\n".join(lines))
    return folder


def build_bells():
    b = devices.BFA01
    folder = os.path.join(ROOT, "builds", "bells-palsy-asymmetry")
    os.makedirs(folder, exist_ok=True)
    open(os.path.join(folder, "README.md"), "w").write(f"""# Facial-asymmetry grading for Bell's palsy

{b['short']}

**Paper:** Ahmed Sultan and Ahsan Numan, *A Machine Learning System for Quantifying Facial Asymmetry in Bell's Palsy across Underrepresented Phenotypes*. Accepted for publication in the Annals of KEMU. Preprint: Research Square, 2026, [doi:{b['doi']}](https://doi.org/{b['doi']})

## Method

1. MediaPipe Face Mesh places 478 landmarks on a frontal photograph.
2. A facial midline is fitted by least squares through 28 landmarks that lie on it.
3. Eleven regional indices compare paired landmarks on either side of that line: brows, eyes, nose, mouth and jaw.
4. Their mean is the global asymmetry index.

## What the paper shows

Before trying the method on patients, the paper measures how it behaves on 10,954 faces without palsy from the FairFace validation set, balanced across seven groups.

- Faces were detected in 90.1 % of images; failure rates ran from 5.9 % to 12.7 % depending on the group.
- Median global asymmetry on these faces was 0.187. Group differences were statistically detectable but tiny (ε² ≈ 0.003).
- Flagging thresholds set per group ranged from 0.601 to 0.654, around a pooled 0.636.
- The inner corner of the eye came out most asymmetric in every group. The paper traces this to an unstable denominator in that index, not to real asymmetry.

How well the index picks up Bell's palsy itself is the next study, with the Department of Neurology at King Edward Medical University.

## Code

The analysis code goes in this folder once the paper is published.
""")


def build_root():
    rows = [("[Facial-asymmetry grading for Bell's palsy](builds/bells-palsy-asymmetry)", "Neurology", "Phone or laptop", "Python")]
    for d in devices.DEVICES:
        rows.append((f"[{d['name']}](builds/{d['slug']})", d["area"], d["mcu"]["title"], FIRMWARE[d["slug"]]["lang"]))
    open(os.path.join(ROOT, "README.md"), "w").write(f"""# Build for All library

This is where Build for All keeps what it designs: wiring, parts lists, printable enclosures and firmware, for anyone to build, test, change and use.

Build for All is a global student-run innovation lab from Pakistan, with chapters in 19 countries and territories. Each build starts from a problem seen up close, in a clinic, a classroom or at home. Publishing all of it means the next person starts where the last one stopped.

## Builds

{md_table(rows, ["Build", "Area", "Runs on", "Firmware"])}

Each folder has its own README with the problem, how the build works, wiring, parts, step-by-step assembly and the testing it still needs.

## Layout

```
builds/<name>/
├── README.md
├── firmware/       source, build files and tests for that board's toolchain
├── hardware/       parts list
└── enclosure/      STEP to edit, STL to print
tools/              scripts that generate the parts lists, READMEs and enclosures
```

Firmware is written for whatever suits the board and the job, so the toolchains differ from build to build; each README says how to flash it. Parts lists, READMEs and enclosures are generated from `tools/devices.py` and `tools/enclosures.py`:

```
python3 tools/build_library.py                 # READMEs and parts lists
pip install cadquery
python3 tools/build_library.py --enclosures    # STEP and STL as well
```

## A note on safety

These are engineering designs from a student lab, not certified medical devices. None should be used to make a decision about someone's care until it has passed the testing listed in its folder. Test results go back into the folder as they come in.

## Contributing

Ports to other boards, better enclosures, corrections and especially test data are welcome as pull requests or issues. For anything larger, write to info@buildforall.net.

## Licence

Firmware and tools are MIT (`LICENSE`). Hardware designs and enclosures are CERN-OHL-P-2.0 (`LICENSE-HARDWARE`).
""")


if __name__ == "__main__":
    args = sys.argv[1:]
    with_enc = "--enclosures" in args
    want = [a for a in args if not a.startswith("--")]
    for d in devices.DEVICES:
        if not want or d["slug"] in want:
            print("built", build(d, with_enc))
    if not want:
        build_bells()
        build_root()
