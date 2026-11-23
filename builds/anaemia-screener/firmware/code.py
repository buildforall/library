# Needle-free anaemia screener, CircuitPython on an ESP32-C3 SuperMini.
#
# Pins: SDA 8, SCL 9, LEDs 1/3/4/5/6 (530/590/660/810/940 nm), button 10,
# buzzer 7, battery divider 0.
#
# Press: measure for 20 s. Hold 1.5 s: change patient group.
# Until model.json holds fitted coefficients, the screen shows the ratios and
# every reading is printed to the serial console for the calibration dataset.

import array
import json
import time

import analogio
import board
import busio
import digitalio
import displayio
import i2cdisplaybus
import microcontroller
import pwmio
import terminalio
from microcontroller import pin

import adafruit_displayio_ssd1306
from adafruit_display_text import label

import hb
from ads1115 import ADS1115

RECORD_S = 20
MAX_FRAMES = 1200

displayio.release_displays()
i2c = busio.I2C(pin.GPIO9, pin.GPIO8, frequency=400_000)
display = adafruit_displayio_ssd1306.SSD1306(
    i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C), width=128, height=64
)
lines = [label.Label(terminalio.FONT, text="", x=0, y=4 + 12 * i) for i in range(5)]
root = displayio.Group()
for line in lines:
    root.append(line)
display.root_group = root

leds = []
for p in (pin.GPIO1, pin.GPIO3, pin.GPIO4, pin.GPIO5, pin.GPIO6):
    d = digitalio.DigitalInOut(p)
    d.switch_to_output(False)
    leds.append(d)

button = digitalio.DigitalInOut(pin.GPIO10)
button.switch_to_input(pull=digitalio.Pull.UP)
buzzer = pwmio.PWMOut(pin.GPIO7, frequency=2000, duty_cycle=0, variable_frequency=True)
vbat = analogio.AnalogIn(pin.GPIO0)

# Patient group survives power-off in the first byte of non-volatile memory.
group = microcontroller.nvm[0] % len(hb.GROUPS)

try:
    with open("/model.json") as f:
        model = json.load(f)["coefficients"]
except (OSError, ValueError, KeyError):
    model = None


def beep(freq, ms):
    buzzer.frequency = freq
    buzzer.duty_cycle = 32768
    time.sleep(ms / 1000)
    buzzer.duty_cycle = 0


def battery_v():
    return vbat.value / 65535 * vbat.reference_voltage * 2


def screen(*text):
    head = "Hb  " + hb.GROUPS[group]
    if battery_v() < 3.45:
        head = head[:16] + "  LOW"
    lines[0].text = head
    for i in range(1, 5):
        lines[i].text = text[i - 1] if i - 1 < len(text) else ""


def frame(adc, out):
    """Dark reading, then each LED in turn, all dark-subtracted."""
    dark = adc.read()
    for i, led in enumerate(leds):
        led.value = True
        out[i] = adc.read() - dark
        led.value = False


def measure(adc):
    screen("Measuring 20 s...", "Keep still.")
    beep(1800, 60)
    sig = [array.array("f", bytes(4 * MAX_FRAMES)) for _ in range(5)]
    f = [0.0] * 5
    n = 0
    start = time.monotonic()
    while time.monotonic() - start < RECORD_S and n < MAX_FRAMES:
        frame(adc, f)
        for i in range(5):
            sig[i][n] = f[i]
        n += 1
    fs = n / (time.monotonic() - start)

    ac, dc = [], []
    for i in range(5):
        a, d = hb.ac_dc(sig[i][:n], fs)
        ac.append(a)
        dc.append(d)
    if hb.weak(ac, dc):
        screen("Weak signal.", "Reseat finger,", "press to retry.")
        beep(500, 400)
        return

    x = hb.ratios(ac, dc)
    print(
        "frames,%d,fs,%.1f," % (n, fs)
        + ",".join("ac%d,%.2f,dc%d,%.1f" % (hb.NM[i], ac[i], hb.NM[i], dc[i]) for i in range(5))
        + ","
        + ",".join("x%d,%.4f" % (hb.NM[i], x[i]) for i in range(4))
    )

    if model:
        est = hb.estimate(model, x)
        cut = hb.CUTOFFS[group]
        screen(
            "Hb est %.1f g/dL" % est,
            ("Below %.0f: REFER" if est < cut else "At or above %.0f") % cut,
            "Screening only.",
            "Confirm with lab.",
        )
        beep(2600 if est < cut else 1500, 300)
    else:
        screen(
            "Not calibrated:",
            "530 %.3f 590 %.3f" % (x[0], x[1]),
            "660 %.3f 810 %.3f" % (x[2], x[3]),
            "Logged to serial.",
        )
        beep(1500, 200)


def main():
    global group
    try:
        adc = ADS1115(i2c)
    except OSError:
        screen("ADC not found.")
        while True:
            time.sleep(1)

    screen("Finger into the clip,", "hand still.", "Press: start", "Hold: change group")
    while True:
        if button.value:
            time.sleep(0.01)
            continue
        t0 = time.monotonic()
        while not button.value:
            time.sleep(0.005)
        if time.monotonic() - t0 > 1.5:
            group = (group + 1) % len(hb.GROUPS)
            microcontroller.nvm[0] = group
            screen("Group changed.", "", "Press: start")
        else:
            measure(adc)


main()
