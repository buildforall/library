# Build for All library

This is where Build for All keeps what it designs: wiring, parts lists, printable enclosures and firmware, for anyone to build, test, change and use.

Build for All is a global student-run innovation lab from Pakistan, with chapters in 19 countries and territories. Each build starts from a problem seen up close, in a clinic, a classroom or at home. Publishing all of it means the next person starts where the last one stopped.

## Builds

| Build | Area | Runs on | Firmware |
|---|---|---|---|
| [Facial-asymmetry grading for Bell's palsy](builds/bells-palsy-asymmetry) | Neurology | Phone or laptop | Python |
| [Breath counter for childhood pneumonia](builds/breath-counter) | Newborns and children | ESP32-C3 SuperMini | MicroPython |
| [Transcutaneous jaundice meter](builds/jaundice-meter) | Newborns and children | ESP32-C3 SuperMini | Rust |
| [Capillary refill timer](builds/capillary-refill-timer) | Newborns and children | ESP32-C3 SuperMini | C, ESP-IDF |
| [Freezing-of-gait anklet](builds/freezing-of-gait-anklet) | Neurology and rehabilitation | ESP32-C3 SuperMini | C++, PlatformIO |
| [Stroke hand-rehabilitation glove](builds/stroke-rehab-glove) | Neurology and rehabilitation | ESP32-S3 SuperMini | Arduino |
| [Needle-free anaemia screener](builds/anaemia-screener) | Clinic screening | ESP32-C3 SuperMini | CircuitPython |
| [Open spirometer](builds/open-spirometer) | Clinic screening | ESP32-C3 SuperMini | C++17, ESP-IDF |
| [Clubfoot brace adherence sensor](builds/clubfoot-brace-sensor) | Newborns and children | Seeed XIAO nRF52840 | Zephyr RTOS |

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
