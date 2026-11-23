// Bluetooth LE service (NimBLE) that streams the last flow-volume curve.
//
// Service    6e4b0800-bfa0-4b1d-9a10-000000000008
// Curve      6e4b0801-bfa0-4b1d-9a10-000000000008  read, notify
// Each notification holds up to 8 pairs of int16 little-endian:
// volume in mL, flow in mL/s, every 5th sample (40 Hz).
#pragma once

namespace curve_service {

void start(const char *device_name);
void send(const float *volume_l, const float *flow_lps, int n);

}  // namespace curve_service
