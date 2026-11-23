# Breath counter for childhood pneumonia, MicroPython on an ESP32-C3 SuperMini.
#
# Pins: SDA 8, SCL 9, START 5, AGE 6, buzzer 7, battery divider on 0.
# Needs ssd1306.py on the board:  mpremote mip install ssd1306

import time
from machine import ADC, I2C, PWM, Pin
import ssd1306

import breath
from lsm6ds3 import LSM6DS3

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400_000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
btn_start = Pin(5, Pin.IN, Pin.PULL_UP)
btn_age = Pin(6, Pin.IN, Pin.PULL_UP)
buzzer = PWM(Pin(7), freq=2000, duty_u16=0)
vbat = ADC(Pin(0), atten=ADC.ATTN_11DB)

PERIOD_US = 1_000_000 // breath.FS


def beep(freq, ms):
    buzzer.freq(freq)
    buzzer.duty_u16(32768)
    time.sleep_ms(ms)
    buzzer.duty_u16(0)


def battery_v():
    return vbat.read_uv() * 2 / 1e6


class Button:
    def __init__(self, pin):
        self.pin, self.last, self.t = pin, 1, 0

    def pressed(self):
        now = self.pin.value()
        if now != self.last and time.ticks_diff(time.ticks_ms(), self.t) > 30:
            self.t, self.last = time.ticks_ms(), now
            return now == 0
        return False


def big(n, x, y):
    # 3x text by scaling the 8x8 font through a scratch framebuffer
    import framebuf
    s = str(n)
    buf = framebuf.FrameBuffer(bytearray(8 * len(s)), 8 * len(s), 8, framebuf.MONO_VLSB)
    buf.text(s, 0, 0, 1)
    for px in range(8 * len(s)):
        for py in range(8):
            if buf.pixel(px, py):
                oled.fill_rect(x + px * 3, y + py * 3, 3, 3, 1)


def draw(state, band, session):
    oled.fill(0)
    oled.text("Breaths", 0, 0)
    if battery_v() < 3.45:
        oled.text("LOW", 104, 0)
    if state == breath.IDLE:
        oled.text(breath.AGE_BANDS[band], 0, 14)
        oled.text("Cut-off %d/min" % breath.CUTOFFS[band], 0, 26)
        oled.text("AGE   change", 0, 42)
        oled.text("START count", 0, 54)
    elif state == breath.SETTLE:
        oled.text("Hold still", 0, 22)
        left = breath.SETTLE_S - session.n // breath.FS
        oled.text("Starting in %d" % max(left, 1), 0, 38)
    elif state == breath.COUNTING:
        big(session.live_count, 0, 18)
        oled.text("%d/60 s" % session.seconds_counted, 72, 22)
        if session.moving:
            oled.text("moving", 72, 40)
    elif state == breath.RESULT:
        big(session.result, 0, 14)
        oled.text("per min", 72, 22)
        oled.text("FAST BREATHING" if session.fast else "Not fast for age", 0, 50)
    elif state == breath.ABORTED:
        oled.text("Too much", 0, 18)
        oled.text("movement.", 0, 30)
        oled.text("Settle, START", 0, 48)
    oled.show()


def main():
    try:
        imu = LSM6DS3(i2c)
    except OSError:
        oled.fill(0)
        oled.text("Motion sensor", 0, 20)
        oled.text("missing", 0, 32)
        oled.show()
        return

    start, age = Button(btn_start), Button(btn_age)
    band, state, session = 2, breath.IDLE, None
    draw(state, band, session)
    next_tick = time.ticks_us()
    last_draw = time.ticks_ms()

    while True:
        if age.pressed() and state in (breath.IDLE, breath.RESULT, breath.ABORTED):
            band, state = (band + 1) % 3, breath.IDLE
            draw(state, band, session)
        if start.pressed():
            if state in (breath.SETTLE, breath.COUNTING):
                state = breath.IDLE
            else:
                session = breath.Session(band)
                state = breath.SETTLE
                beep(1800, 80)
            draw(state, band, session)
            next_tick = time.ticks_us()

        if state not in (breath.SETTLE, breath.COUNTING):
            time.sleep_ms(10)
            continue

        if time.ticks_diff(time.ticks_us(), next_tick) < 0:
            continue
        next_tick = time.ticks_add(next_tick, PERIOD_US)

        before = state
        state = session.feed(*imu.accel())
        if before == breath.SETTLE and state == breath.COUNTING:
            beep(2200, 60)
        elif state == breath.RESULT:
            beep(2600, 600) if session.fast else beep(1400, 200)
            print("result,%s,%d" % (breath.AGE_BANDS[band], session.result))
            draw(state, band, session)
        elif state == breath.ABORTED:
            beep(600, 400)
            draw(state, band, session)
        elif time.ticks_diff(time.ticks_ms(), last_draw) > 200:
            last_draw = time.ticks_ms()
            draw(state, band, session)


main()
