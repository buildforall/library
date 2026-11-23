# Minimal LSM6DS3TR-C accelerometer driver for MicroPython.
# Only what the breath counter needs: +/-2 g at 104 Hz, read in g.

import struct
from micropython import const

_WHO_AM_I = const(0x0F)
_CTRL1_XL = const(0x10)
_CTRL3_C = const(0x12)
_OUTX_L_XL = const(0x28)
_CHIP_ID = const(0x6A)
_LSB_G = 0.061e-3       # g per LSB at +/-2 g


class LSM6DS3:
    def __init__(self, i2c, addr=None):
        self.i2c = i2c
        found = i2c.scan()
        if addr is None:
            addr = 0x6A if 0x6A in found else 0x6B
        self.addr = addr
        if self._read(_WHO_AM_I, 1)[0] != _CHIP_ID:
            raise OSError("LSM6DS3TR-C not found")
        self._write(_CTRL3_C, 0x01)          # software reset
        self._write(_CTRL3_C, 0x44)          # block data update, auto-increment
        self._write(_CTRL1_XL, 0x40)         # 104 Hz, +/-2 g
        self._buf = bytearray(6)

    def _read(self, reg, n):
        return self.i2c.readfrom_mem(self.addr, reg, n)

    def _write(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes((val,)))

    def accel(self):
        self.i2c.readfrom_mem_into(self.addr, _OUTX_L_XL, self._buf)
        x, y, z = struct.unpack("<hhh", self._buf)
        return x * _LSB_G, y * _LSB_G, z * _LSB_G
