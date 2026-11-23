//! Jaundice index from skin reflectance.
//!
//! Optical density in the bilirubin band (445-480 nm) minus the green band
//! (555 nm), with melanin's share removed. Melanin absorbance falls roughly as
//! wavelength^-3.48, so its amplitude can be estimated from the 630/680 nm
//! difference, where bilirubin and haemoglobin absorb little.

use libm::{log10f, powf};

fn melanin(nm: f32) -> f32 {
    powf(nm / 500.0, -3.48)
}

pub fn optical_density(signal: &[f32; 9], white: &[f32; 9]) -> [f32; 9] {
    let mut od = [0f32; 9];
    for i in 0..9 {
        let r = (signal[i] / white[i].max(1.0)).clamp(1e-4, 10.0);
        od[i] = -log10f(r);
    }
    od
}

pub fn jaundice_index(signal: &[f32; 9], white: &[f32; 9]) -> f32 {
    let od = optical_density(signal, white);
    let mel_amp = (od[6] - od[7]) / (melanin(630.0) - melanin(680.0));
    let blue = 0.5 * (od[1] + od[2]);
    let green = od[4];
    let mel_blue_green = mel_amp * (0.5 * (melanin(445.0) + melanin(480.0)) - melanin(555.0));
    (blue - green) - mel_blue_green
}

/// Linear map from index to transcutaneous bilirubin, fitted against serum
/// bilirubin in the calibration study described in the README. `None` until
/// that study has been done; the meter then shows the raw index only.
pub const CALIBRATION: Option<(f32, f32)> = None;

pub fn to_mg_dl(index: f32) -> Option<f32> {
    CALIBRATION.map(|(a, b)| a + b * index)
}
