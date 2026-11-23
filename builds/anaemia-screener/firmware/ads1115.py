# ADS1115 in single-shot mode, AIN0 to ground, +/-4.096 V, 860 samples/s.
# Small enough to read in one sitting; the screener needs nothing else.

import time

_CONVERSION = 0x00
_CONFIG = 0x01
# OS=start | MUX=AIN0-GND | PGA=+/-4.096 V | single-shot | 860 SPS | comparator off
_START = 0xC3E3


class ADS1115:
    def __init__(self, i2c, address=0x48):
        self.i2c = i2c
        self.address = address
        self._cmd = bytearray((_CONFIG, _START >> 8, _START & 0xFF))
        self._reg = bytearray(1)
        self._buf = bytearray(2)
        while not i2c.try_lock():
            pass
        try:
            if address not in i2c.scan():
                raise OSError("ADS1115 not found at 0x%02X" % address)
        finally:
            i2c.unlock()

    def read(self):
        """One conversion, signed 16-bit counts (125 uV each at this gain)."""
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.address, self._cmd)
            self._reg[0] = _CONFIG
            for _ in range(20):
                time.sleep(0.0005)
                self.i2c.writeto_then_readfrom(self.address, self._reg, self._buf)
                if self._buf[0] & 0x80:   # OS bit set: conversion done
                    break
            self._reg[0] = _CONVERSION
            self.i2c.writeto_then_readfrom(self.address, self._reg, self._buf)
        finally:
            self.i2c.unlock()
        v = (self._buf[0] << 8) | self._buf[1]
        return v - 65536 if v & 0x8000 else v
