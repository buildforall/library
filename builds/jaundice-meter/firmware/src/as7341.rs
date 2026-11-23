//! AS7341 11-channel spectral sensor, the parts this meter needs.
//!
//! The chip has six ADCs and more photodiodes than ADCs, so a full read is two
//! passes through the SMUX: F1-F4 first, then F5-F8. Clear and NIR are wired to
//! ADC4 and ADC5 in both passes.

use embedded_hal::delay::DelayNs;
use embedded_hal::i2c::I2c;

const ADDR: u8 = 0x39;

const CONFIG: u8 = 0x70; // bank 1
const LED: u8 = 0x74; // bank 1
const ENABLE: u8 = 0x80;
const ATIME: u8 = 0x81;
const ID: u8 = 0x92;
const CH0_DATA_L: u8 = 0x95;
const STATUS2: u8 = 0xA3;
const CFG0: u8 = 0xA9;
const CFG1: u8 = 0xAA;
const CFG6: u8 = 0xAF;
const ASTEP_L: u8 = 0xCA;

const PON: u8 = 1 << 0;
const SP_EN: u8 = 1 << 1;
const SMUXEN: u8 = 1 << 4;
const AVALID: u8 = 1 << 6;
const REG_BANK: u8 = 1 << 4;
const SMUX_CMD_WRITE: u8 = 2 << 3;
const LED_SEL: u8 = 1 << 3;
const LED_ACT: u8 = 1 << 7;

/// SMUX maps from the AS7341 application note (AN000666).
const SMUX_F1_F4: [u8; 20] = [
    0x30, 0x01, 0x00, 0x00, 0x00, 0x42, 0x00, 0x00, 0x50, 0x00, //
    0x00, 0x00, 0x20, 0x04, 0x00, 0x30, 0x01, 0x50, 0x00, 0x06,
];
const SMUX_F5_F8: [u8; 20] = [
    0x00, 0x00, 0x00, 0x40, 0x02, 0x00, 0x10, 0x03, 0x50, 0x10, //
    0x03, 0x00, 0x00, 0x00, 0x24, 0x00, 0x00, 0x50, 0x00, 0x06,
];

#[derive(Debug)]
pub enum Error<E> {
    Bus(E),
    NotFound,
    Timeout,
}

impl<E> From<E> for Error<E> {
    fn from(e: E) -> Self {
        Error::Bus(e)
    }
}

/// Wavelengths of the nine channels returned by [`As7341::read`], in nm.
/// Index 8 is the near-infrared photodiode (~910 nm).
pub const NM: [f32; 9] = [415.0, 445.0, 480.0, 515.0, 555.0, 590.0, 630.0, 680.0, 910.0];

pub struct As7341<I> {
    i2c: I,
}

impl<I: I2c> As7341<I> {
    pub fn new(i2c: I) -> Self {
        Self { i2c }
    }

    pub fn init(&mut self, delay: &mut impl DelayNs) -> Result<(), Error<I::Error>> {
        if self.read_reg(ID)? >> 2 != 0x09 {
            return Err(Error::NotFound);
        }
        self.write_reg(ENABLE, PON)?;
        delay.delay_ms(2);
        // Integration time = (ATIME + 1) * (ASTEP + 1) * 2.78 us = 50 ms
        self.write_reg(ATIME, 29)?;
        self.i2c.write(ADDR, &[ASTEP_L, (599u16 & 0xFF) as u8, (599u16 >> 8) as u8])?;
        self.write_reg(CFG1, 5)?; // gain 16x
        Ok(())
    }

    /// Onboard LED on or off, at 4 + 2 * drive mA.
    pub fn led(&mut self, on: bool, milliamps: u8) -> Result<(), Error<I::Error>> {
        let drive = milliamps.saturating_sub(4) / 2;
        self.bank(true)?;
        let cfg = self.read_reg(CONFIG)?;
        self.write_reg(CONFIG, if on { cfg | LED_SEL } else { cfg & !LED_SEL })?;
        self.write_reg(LED, if on { LED_ACT | (drive & 0x7F) } else { drive & 0x7F })?;
        self.bank(false)?;
        Ok(())
    }

    /// Reads F1-F8 and NIR, in the order of [`NM`].
    pub fn read(&mut self, delay: &mut impl DelayNs) -> Result<[f32; 9], Error<I::Error>> {
        let low = self.pass(&SMUX_F1_F4, delay)?;
        let high = self.pass(&SMUX_F5_F8, delay)?;
        Ok([
            low[0], low[1], low[2], low[3], //
            high[0], high[1], high[2], high[3], //
            low[5],
        ])
    }

    fn pass(&mut self, smux: &[u8; 20], delay: &mut impl DelayNs) -> Result<[f32; 6], Error<I::Error>> {
        self.write_reg(ENABLE, PON)?;
        self.write_reg(CFG6, SMUX_CMD_WRITE)?;
        let mut buf = [0u8; 21];
        buf[1..].copy_from_slice(smux);
        self.i2c.write(ADDR, &buf)?;
        self.write_reg(ENABLE, PON | SMUXEN)?;
        self.wait(delay, |s| s.read_reg(ENABLE).map(|v| v & SMUXEN == 0))?;

        self.write_reg(ENABLE, PON | SP_EN)?;
        self.wait(delay, |s| s.read_reg(STATUS2).map(|v| v & AVALID != 0))?;

        let mut raw = [0u8; 12];
        self.i2c.write_read(ADDR, &[CH0_DATA_L], &mut raw)?;
        let mut out = [0f32; 6];
        for (i, v) in out.iter_mut().enumerate() {
            *v = u16::from_le_bytes([raw[2 * i], raw[2 * i + 1]]) as f32;
        }
        Ok(out)
    }

    fn wait(
        &mut self,
        delay: &mut impl DelayNs,
        mut done: impl FnMut(&mut Self) -> Result<bool, I::Error>,
    ) -> Result<(), Error<I::Error>> {
        for _ in 0..500 {
            if done(self)? {
                return Ok(());
            }
            delay.delay_ms(1);
        }
        Err(Error::Timeout)
    }

    fn bank(&mut self, high: bool) -> Result<(), I::Error> {
        self.write_reg(CFG0, if high { REG_BANK } else { 0 })
    }

    fn read_reg(&mut self, reg: u8) -> Result<u8, I::Error> {
        let mut b = [0u8];
        self.i2c.write_read(ADDR, &[reg], &mut b)?;
        Ok(b[0])
    }

    fn write_reg(&mut self, reg: u8, val: u8) -> Result<(), I::Error> {
        self.i2c.write(ADDR, &[reg, val])
    }
}
