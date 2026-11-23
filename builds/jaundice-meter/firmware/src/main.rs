//! Transcutaneous jaundice meter, ESP32-C3 SuperMini.
//!
//! Pins: SDA 8, SCL 9, probe switch 5, MODE 6, buzzer 7, battery divider 0.
//!
//! The probe is pressed on the forehead or sternum three times. Each press reads
//! nine spectral bands with the LED on and off, subtracts the dark frame, and
//! compares against a white reference taken on PTFE. The mean of the three
//! jaundice indices is shown, and converted to mg/dL once a calibration exists.

#![no_std]
#![no_main]

mod as7341;
mod optics;

use core::cell::RefCell;
use core::fmt::Write as _;

use embedded_graphics::mono_font::MonoTextStyle;
use embedded_graphics::mono_font::ascii::FONT_6X10;
use embedded_graphics::pixelcolor::BinaryColor;
use embedded_graphics::prelude::*;
use embedded_graphics::text::{Baseline, Text};
use embedded_hal_bus::i2c::RefCellDevice;
use esp_backtrace as _;
use esp_hal::analog::adc::{Adc, AdcCalCurve, AdcConfig, Attenuation};
use esp_hal::delay::Delay;
use esp_hal::gpio::{Input, InputConfig, Level, Output, OutputConfig, Pull};
use esp_hal::i2c::master::{Config as I2cConfig, I2c};
use esp_hal::time::Rate;
use esp_hal::{main, peripherals::ADC1};
use esp_println::println;
use esp_storage::FlashStorage;
use heapless::String;
use ssd1306::{I2CDisplayInterface, Ssd1306, prelude::*};

use as7341::As7341;

esp_bootloader_esp_idf::esp_app_desc!();

/// Raw flash offset for the white reference: the start of the (unused) NVS
/// partition in the default ESP-IDF partition table.
const WHITE_OFFSET: u32 = 0x9000;
const WHITE_MAGIC: u32 = 0x4A41_554E; // "JAUN"
const LED_MA: u8 = 10;

#[derive(Clone, Copy, PartialEq)]
enum Mode {
    Measure,
    WhiteReference,
}

fn load_white(flash: &mut FlashStorage) -> Option<[f32; 9]> {
    let mut buf = [0u8; 40];
    flash.read(WHITE_OFFSET, &mut buf).ok()?;
    if u32::from_le_bytes(buf[0..4].try_into().ok()?) != WHITE_MAGIC {
        return None;
    }
    let mut w = [0f32; 9];
    for (i, v) in w.iter_mut().enumerate() {
        *v = f32::from_le_bytes(buf[4 + 4 * i..8 + 4 * i].try_into().ok()?);
    }
    Some(w)
}

fn save_white(flash: &mut FlashStorage, w: &[f32; 9]) {
    let mut buf = [0u8; 40];
    buf[0..4].copy_from_slice(&WHITE_MAGIC.to_le_bytes());
    for (i, v) in w.iter().enumerate() {
        buf[4 + 4 * i..8 + 4 * i].copy_from_slice(&v.to_le_bytes());
    }
    if flash.write(WHITE_OFFSET, &buf).is_err() {
        println!("white reference: flash write failed");
    }
}

/// Square wave on the buzzer pin. Blocking, which is fine for short beeps.
fn beep(pin: &mut Output, delay: &Delay, hz: u32, ms: u32) {
    let half_us = 500_000 / hz;
    for _ in 0..(hz * ms / 1000) {
        pin.set_high();
        delay.delay_micros(half_us);
        pin.set_low();
        delay.delay_micros(half_us);
    }
}

#[main]
fn main() -> ! {
    let p = esp_hal::init(esp_hal::Config::default());
    let delay = Delay::new();

    let i2c = I2c::new(p.I2C0, I2cConfig::default().with_frequency(Rate::from_khz(400)))
        .unwrap()
        .with_sda(p.GPIO8)
        .with_scl(p.GPIO9);
    let bus = RefCell::new(i2c);

    let mut display = Ssd1306::new(
        I2CDisplayInterface::new(RefCellDevice::new(&bus)),
        DisplaySize128x64,
        DisplayRotation::Rotate0,
    )
    .into_buffered_graphics_mode();
    display.init().unwrap();

    let probe = Input::new(p.GPIO5, InputConfig::default().with_pull(Pull::Up));
    let mode_btn = Input::new(p.GPIO6, InputConfig::default().with_pull(Pull::Up));
    let mut buzzer = Output::new(p.GPIO7, Level::Low, OutputConfig::default());

    let mut adc_cfg = AdcConfig::new();
    let mut vbat_pin = adc_cfg.enable_pin_with_cal::<_, AdcCalCurve<ADC1>>(p.GPIO0, Attenuation::_11dB);
    let mut adc = Adc::new(p.ADC1, adc_cfg);

    let mut flash = FlashStorage::new(p.FLASH);
    let mut white = load_white(&mut flash);

    let style = MonoTextStyle::new(&FONT_6X10, BinaryColor::On);
    let mut mode = Mode::Measure;
    let mut readings: [f32; 3] = [0.0; 3];
    let mut n = 0usize;

    let mut show = |mode: Mode, lines: [&str; 3], low_battery: bool| {
        display.clear(BinaryColor::Off).ok();
        let title = if mode == Mode::Measure { "Measure" } else { "White reference" };
        Text::with_baseline(title, Point::new(0, 0), style, Baseline::Top).draw(&mut display).ok();
        if low_battery {
            Text::with_baseline("LOW", Point::new(110, 0), style, Baseline::Top).draw(&mut display).ok();
        }
        for (i, l) in lines.iter().enumerate() {
            Text::with_baseline(l, Point::new(0, 18 + 16 * i as i32), style, Baseline::Top)
                .draw(&mut display)
                .ok();
        }
        display.flush().ok();
    };

    let mut sensor = As7341::new(RefCellDevice::new(&bus));
    let mut d = delay;
    if sensor.init(&mut d).is_err() {
        show(mode, ["Spectral sensor", "not found.", ""], false);
        loop {
            delay.delay_millis(1000);
        }
    }
    println!("jaundice meter ready, channels (nm): {:?}", as7341::NM);

    let mut battery_low = || {
        let mv = nb::block!(adc.read_oneshot(&mut vbat_pin)).unwrap_or(0) as u32;
        mv * 2 < 3450
    };

    let idle = |mode: Mode, white: &Option<[f32; 9]>, n: usize, buf: &mut String<24>| -> [&'static str; 2] {
        buf.clear();
        let _ = write!(buf, "Reading {} of 3", n + 1);
        match (mode, white) {
            (Mode::WhiteReference, _) => ["Cap on probe, press", "on PTFE. MODE: back"],
            (Mode::Measure, None) => ["No white reference.", "Press MODE first."],
            (Mode::Measure, Some(_)) => ["Press probe on", "forehead or sternum."],
        }
    };

    let mut line3: String<24> = String::new();
    let [a, b] = idle(mode, &white, n, &mut line3);
    show(mode, [a, b, if white.is_some() { line3.as_str() } else { "" }], battery_low());

    let mut last_mode = true;
    loop {
        let m = mode_btn.is_high();
        if !m && last_mode {
            mode = if mode == Mode::Measure { Mode::WhiteReference } else { Mode::Measure };
            n = 0;
            let [a, b] = idle(mode, &white, n, &mut line3);
            show(mode, [a, b, if mode == Mode::Measure && white.is_some() { line3.as_str() } else { "" }], battery_low());
            delay.delay_millis(200);
        }
        last_mode = m;

        if probe.is_high() {
            delay.delay_millis(10);
            continue;
        }
        delay.delay_millis(150); // spring settles, skin blanches
        if probe.is_high() {
            continue;
        }

        // Three dark-subtracted frames, averaged
        let mut sig = [0f32; 9];
        let mut ok = true;
        for _ in 0..3 {
            let dark = sensor.led(false, LED_MA).and_then(|_| sensor.read(&mut d));
            let lit = sensor
                .led(true, LED_MA)
                .and_then(|_| {
                    d.delay_millis(20);
                    sensor.read(&mut d)
                });
            let _ = sensor.led(false, LED_MA);
            match (dark, lit) {
                (Ok(dk), Ok(lt)) => {
                    for i in 0..9 {
                        sig[i] += (lt[i] - dk[i]) / 3.0;
                    }
                }
                _ => ok = false,
            }
        }
        if !ok {
            show(mode, ["Sensor read failed.", "", ""], battery_low());
            delay.delay_millis(1000);
        } else if mode == Mode::WhiteReference {
            save_white(&mut flash, &sig);
            white = Some(sig);
            beep(&mut buzzer, &delay, 2000, 150);
            show(mode, ["White reference", "saved.", "MODE: back"], battery_low());
        } else if let Some(w) = white {
            let idx = optics::jaundice_index(&sig, &w);
            readings[n] = idx;
            n += 1;
            beep(&mut buzzer, &delay, 1800, 80);
            println!("raw,{:?},index,{:.4}", sig, idx);
            if n == 3 {
                let mean = readings.iter().sum::<f32>() / 3.0;
                let mut l1: String<24> = String::new();
                let mut l2: String<24> = String::new();
                let _ = write!(l1, "Index {:.3}", mean);
                match optics::to_mg_dl(mean) {
                    Some(mg) => {
                        let _ = write!(l2, "TcB est {:.1} mg/dL", mg);
                    }
                    None => {
                        let _ = write!(l2, "Not yet calibrated");
                    }
                }
                show(mode, [l1.as_str(), l2.as_str(), "Lift probe to reset"], battery_low());
                beep(&mut buzzer, &delay, 2400, 300);
                n = 0;
                while probe.is_low() {
                    delay.delay_millis(10);
                }
                while probe.is_high() && mode_btn.is_high() {
                    delay.delay_millis(10);
                }
            }
        }
        while probe.is_low() {
            delay.delay_millis(10);
        }
        let [a, b] = idle(mode, &white, n, &mut line3);
        show(mode, [a, b, if mode == Mode::Measure && white.is_some() { line3.as_str() } else { "" }], battery_low());
    }
}
