// Stroke hand-rehabilitation glove
// Build for All, open hardware. MIT licence. https://github.com/buildforall/library
//
// Board: ESP32-S3 SuperMini ("ESP32S3 Dev Module", USB CDC On Boot: Enabled)
// Libraries: Adafruit LSM6DS; BLE from the ESP32 Arduino core 4.x
//
// Reads five flex sensors and wrist rotation. Hold the button 2 s to calibrate:
// open hand for 3 s, then a fist for 3 s. Each finger is then reported as 0-100 %
// of the wearer's own range; a repetition is a pass above 70 % and back below 30 %.
// Short press starts or ends a session. Not a medical device until validated.

#include <Wire.h>
#include <Preferences.h>
#include <Adafruit_LSM6DS3TRC.h>
#include <BLE.h>

const int PIN_FINGER[5] = {1, 2, 3, 4, 5};     // thumb, index, middle, ring, little
const int PIN_SDA = 8, PIN_SCL = 9, PIN_BTN = 6, PIN_VBAT = 7, PIN_RGB = 48;
const char *FINGER[5] = {"thumb", "index", "middle", "ring", "little"};
const float FS = 50.0f, ALPHA = 0.2f, UP = 70.0f, DOWN = 30.0f;

Adafruit_LSM6DS3TRC imu;
Preferences prefs;
BLECharacteristic liveChr, sessionChr;
bool bleReady = false;

float smooth[5], openMv[5], fistMv[5];
bool calibrated = false, inSession = false, bent[5];
uint16_t reps[5];
float peak[5];
uint32_t sessionStart = 0;

void led(uint8_t r, uint8_t g, uint8_t b) { rgbLedWrite(PIN_RGB, r, g, b); }

float readFinger(int i) { return analogReadMilliVolts(PIN_FINGER[i]); }

float percent(int i) {
  float span = fistMv[i] - openMv[i];
  if (fabsf(span) < 30) return 0;                // sensor not moving: bad calibration
  return constrain(100.0f * (smooth[i] - openMv[i]) / span, 0.0f, 100.0f);
}

void average(float out[5], uint32_t ms) {
  float acc[5] = {0}; int n = 0; uint32_t t0 = millis();
  while (millis() - t0 < ms) { for (int i = 0; i < 5; i++) acc[i] += readFinger(i); n++; delay(20); }
  for (int i = 0; i < 5; i++) out[i] = acc[i] / n;
}

void calibrate() {
  led(0, 0, 40); delay(1500);                    // blue: open your hand
  average(openMv, 3000);
  led(40, 20, 0); delay(1500);                   // amber: make a fist
  average(fistMv, 3000);
  prefs.begin("bfa06", false);
  prefs.putBytes("open", openMv, sizeof(openMv));
  prefs.putBytes("fist", fistMv, sizeof(fistMv));
  prefs.end();
  calibrated = true;
  led(0, 40, 0); delay(600); led(0, 0, 0);
}

String sessionSummary() {
  String s = "finger,reps,peak_pct\n";
  for (int i = 0; i < 5; i++) s += String(FINGER[i]) + "," + reps[i] + "," + String(peak[i], 0) + "\n";
  s += "duration_s," + String(inSession ? (millis() - sessionStart) / 1000 : 0) + "\n";
  return s;
}

void startBle() {
  BLE.begin("BFA glove");
  BLEServer srv = BLE.createServer();
  BLEService svc = srv.createService(BLEUUID("6e4b0600-bfa0-4b1d-9a10-000000000006"));
  liveChr = svc.createCharacteristic(BLEUUID("6e4b0601-bfa0-4b1d-9a10-000000000006"), BLEProperty::Read | BLEProperty::Notify, BLEPermission::ReadWriteOpen);
  sessionChr = svc.createCharacteristic(BLEUUID("6e4b0602-bfa0-4b1d-9a10-000000000006"), BLEProperty::Read, BLEPermission::ReadWriteOpen);
  sessionChr.setValue(sessionSummary());
  srv.onDisconnect([](BLEServer s, const BLEConnInfo &c, uint8_t r) { s.startAdvertising(); });
  srv.start();
  BLEAdvertising adv = BLE.getAdvertising();
  adv.addServiceUUID(BLEUUID("6e4b0600-bfa0-4b1d-9a10-000000000006"));
  adv.start();
  bleReady = true;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN, INPUT_PULLUP);
  analogReadResolution(12);
  for (int i = 0; i < 5; i++) analogSetPinAttenuation(PIN_FINGER[i], ADC_11db);
  Wire.begin(PIN_SDA, PIN_SCL);
  if (imu.begin_I2C()) { imu.setAccelRange(LSM6DS_ACCEL_RANGE_2_G); imu.setAccelDataRate(LSM6DS_RATE_104_HZ); }
  prefs.begin("bfa06", true);
  calibrated = prefs.getBytes("open", openMv, sizeof(openMv)) == sizeof(openMv) &&
               prefs.getBytes("fist", fistMv, sizeof(fistMv)) == sizeof(fistMv);
  prefs.end();
  for (int i = 0; i < 5; i++) smooth[i] = readFinger(i);
  startBle();
  led(calibrated ? 0 : 40, calibrated ? 20 : 0, 0);  // red until calibrated
}

void loop() {
  static uint32_t btnDown = 0, lastTick = 0, lastNotify = 0;
  bool b = digitalRead(PIN_BTN) == LOW;
  if (b && !btnDown) btnDown = millis();
  if (!b && btnDown) {
    uint32_t held = millis() - btnDown; btnDown = 0;
    if (held > 2000) calibrate();
    else if (held > 40 && calibrated) {
      inSession = !inSession;
      if (inSession) { memset(reps, 0, sizeof(reps)); memset(peak, 0, sizeof(peak)); memset(bent, 0, sizeof(bent)); sessionStart = millis(); }
      else sessionChr.setValue(sessionSummary());
      led(0, inSession ? 40 : 0, 0);
    }
  }

  if (millis() - lastTick < 1000 / FS) return;
  lastTick = millis();
  for (int i = 0; i < 5; i++) smooth[i] += ALPHA * (readFinger(i) - smooth[i]);
  if (!calibrated) return;

  uint8_t pct[5];
  for (int i = 0; i < 5; i++) {
    float p = percent(i);
    pct[i] = (uint8_t)p;
    if (inSession) {
      peak[i] = max(peak[i], p);
      if (!bent[i] && p > UP) bent[i] = true;
      else if (bent[i] && p < DOWN) { bent[i] = false; reps[i]++; }
    }
  }

  int8_t roll = 0;
  sensors_event_t a, g, t;
  if (imu.getEvent(&a, &g, &t)) roll = (int8_t)constrain(degrees(atan2f(a.acceleration.y, a.acceleration.z)) / 1.5f, -120, 120);

  if (bleReady && millis() - lastNotify >= 100) {        // 10 Hz: 5 x flexion %, roll (1.5 deg units), 5 x reps
    lastNotify = millis();
    uint8_t pkt[16];
    memcpy(pkt, pct, 5); pkt[5] = (uint8_t)roll;
    for (int i = 0; i < 5; i++) { pkt[6 + 2 * i] = reps[i] & 0xFF; pkt[7 + 2 * i] = reps[i] >> 8; }
    liveChr.setValue(pkt, sizeof(pkt));
    liveChr.notify();
  }
}
