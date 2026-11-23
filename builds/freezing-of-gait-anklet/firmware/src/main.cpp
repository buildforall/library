// Freezing-of-gait anklet, ESP32-C3 SuperMini, PlatformIO + Arduino.
//
// Pins: SDA 8, SCL 9, motor driver 10, button 5, battery divider 0.
//
// When the freeze index crosses the wearer's threshold, the motors pulse at
// their own walking cadence until the index falls, plus 3 s.
// Button: short press toggles a manual cue; hold 2 s to open Bluetooth for
// reading the episode log and setting the threshold.

#include <Adafruit_LSM6DS3TRC.h>
#include <Arduino.h>
#include <NimBLEDevice.h>
#include <Preferences.h>
#include <Wire.h>

#include "FreezeIndex.h"

namespace pins {
constexpr int kSda = 8, kScl = 9, kMotor = 10, kButton = 5, kBattery = 0;
}

constexpr const char *kService = "6e4b0500-bfa0-4b1d-9a10-000000000005";
constexpr const char *kLogChar = "6e4b0501-bfa0-4b1d-9a10-000000000005";
constexpr const char *kCfgChar = "6e4b0502-bfa0-4b1d-9a10-000000000005";

Adafruit_LSM6DS3TRC imu;
Preferences prefs;
fog::FreezeIndex detector;
fog::CueController cue;
bool manualCue = false;
NimBLECharacteristic *logChar = nullptr;

void saveState() {
    prefs.begin("anklet", false);
    prefs.putUShort("n", cue.count);
    prefs.putBytes("log", cue.episodes, sizeof(cue.episodes[0]) * cue.count);
    prefs.putFloat("thr", cue.threshold);
    prefs.end();
}

void loadState() {
    prefs.begin("anklet", true);
    cue.count = min<int>(prefs.getUShort("n", 0), fog::CueController::kMaxEpisodes);
    if (cue.count) prefs.getBytes("log", cue.episodes, sizeof(cue.episodes[0]) * cue.count);
    cue.threshold = prefs.getFloat("thr", 2.0f);
    prefs.end();
}

String logCsv() {
    String s = "start_s,duration_s\n";
    for (int i = 0; i < cue.count; i++)
        s += String(cue.episodes[i].startS) + "," + String(cue.episodes[i].durationS) + "\n";
    return s;
}

// Writes to the config characteristic: "T2.3" sets the threshold, "C" clears the log.
class ConfigWrite : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic *c, NimBLEConnInfo &) override {
        std::string v = c->getValue();
        if (!v.empty() && v[0] == 'T') cue.threshold = atof(v.c_str() + 1);
        if (v == "C") cue.count = 0;
        saveState();
        if (logChar) logChar->setValue(logCsv().c_str());
    }
};

void startBluetooth() {
    if (logChar) return;
    NimBLEDevice::init("BFA anklet");
    NimBLEServer *server = NimBLEDevice::createServer();
    server->advertiseOnDisconnect(true);
    NimBLEService *svc = server->createService(kService);
    logChar = svc->createCharacteristic(kLogChar, NIMBLE_PROPERTY::READ);
    NimBLECharacteristic *cfg = svc->createCharacteristic(kCfgChar, NIMBLE_PROPERTY::WRITE);
    static ConfigWrite onConfig;
    cfg->setCallbacks(&onConfig);
    logChar->setValue(logCsv().c_str());
    server->start();
    NimBLEAdvertising *adv = NimBLEDevice::getAdvertising();
    adv->addServiceUUID(kService);
    adv->start();
}

void pulse(int ms) {
    digitalWrite(pins::kMotor, HIGH);
    delay(ms);
    digitalWrite(pins::kMotor, LOW);
}

void setup() {
    Serial.begin(115200);
    pinMode(pins::kMotor, OUTPUT);
    digitalWrite(pins::kMotor, LOW);
    pinMode(pins::kButton, INPUT_PULLUP);
    analogReadResolution(12);
    Wire.begin(pins::kSda, pins::kScl);
    loadState();
    while (!imu.begin_I2C()) {   // one short buzz a second until the IMU answers
        pulse(100);
        delay(900);
    }
    imu.setAccelRange(LSM6DS_ACCEL_RANGE_4_G);
    imu.setAccelDataRate(LSM6DS_RATE_104_HZ);
    pulse(150);   // power-on
}

void loop() {
    static uint32_t lastTick = 0, buttonDown = 0, lastBattery = 0;

    bool pressed = digitalRead(pins::kButton) == LOW;
    if (pressed && !buttonDown) buttonDown = millis();
    if (!pressed && buttonDown) {
        uint32_t held = millis() - buttonDown;
        buttonDown = 0;
        if (held > 2000) startBluetooth();
        else if (held > 40) manualCue = !manualCue;
    }

    uint32_t now = micros();
    if (now - lastTick >= (uint32_t)(1e6f / fog::kSampleHz)) {
        lastTick = now;
        sensors_event_t a, g, t;
        imu.getEvent(&a, &g, &t);
        float mag = sqrtf(a.acceleration.x * a.acceleration.x + a.acceleration.y * a.acceleration.y +
                          a.acceleration.z * a.acceleration.z) / 9.80665f;
        if (detector.push(mag)) {
            const fog::Analysis &r = detector.last();
            if (cue.update(r, millis())) {
                saveState();
                if (logChar) logChar->setValue(logCsv().c_str());
            }
            Serial.printf("fi,%.2f,power,%.4f,cadence,%.0f,cue,%d\n", r.freezeIndex, r.power,
                          detector.cadence(), cue.cueOn());
        }
    }
    digitalWrite(pins::kMotor, cue.motor(cue.cueOn() || manualCue, detector.cadence(), millis()) ? HIGH : LOW);

    if (millis() - lastBattery > 60000) {   // three short pulses: charge me
        lastBattery = millis();
        if (analogReadMilliVolts(pins::kBattery) * 2 < 3450 && !cue.cueOn())
            for (int i = 0; i < 3; i++) { pulse(60); delay(120); }
    }
}
