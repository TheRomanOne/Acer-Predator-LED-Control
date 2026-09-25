"""Sunrex vendor lighting protocol, used for the keyboard's MagKey zone.

On the PH16-73 the swappable MagKey caps (A/W/S/D) have their own lighting mode, separate from
the per-key LampArray: PredatorSense sets it through `SunrexUSBKeyboard.dll` on the keyboard's
vendor interface (usage page 0xFF02, unnumbered 8-byte feature reports). While that mode is
anything but Off, the firmware paints those four keys itself and ignores LampArray updates for
them. The wire format below is the one decompiled from that DLL by the predator-sense project
(`magic_rgb.rs`) and was confirmed on this laptop: Off hands A/W/S/D back to the LampArray.

Every command is four 9-byte feature reports (leading 0x00 = no report ID), sent ~15 ms apart,
each ending in a checksum that is the bitwise NOT of the wrapped sum of specific bytes.
"""

from enum import IntEnum

from led_studio.hid.reports import Rgb

SUNREX_VENDOR_ID = 0x05AF
SUNREX_VENDOR_USAGE_PAGE = 0xFF02
REPORT_GAP_S = 0.015  # the vendor driver sleeps this long between the reports of one command

_MAX_BRIGHTNESS_PCT = 100
_MAX_SPEED = 9
_MAG_ZONE = 0x01  # byte 3 of the colour report: target the MagKey zone

_HEADERS = [
    bytes([0x00, 0xB1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4E]),
    bytes([0x00, 0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF5]),
]


class MagKeyEffect(IntEnum):
    """Firmware effect codes for the MagKey zone (`MAG_*` in the vendor driver)."""

    OFF = 0x40
    STATIC = 0x41
    BREATHING = 0x42
    WAVE = 0x43


def pack_magkey_effect(
    effect: MagKeyEffect, brightness_pct: int, color: Rgb | None, speed: int = 0
) -> list[bytes]:
    """The four feature reports that put the MagKey zone into `effect`."""
    speed_byte = 10 - min(max(speed, 0), _MAX_SPEED)
    brightness = min(max(brightness_pct, 0), _MAX_BRIGHTNESS_PCT)
    rgb = color or Rgb(0, 0, 0)
    effect_report = bytes(
        [0x00, 0x08, 0x02, effect, speed_byte, brightness, 0x00, 0x00]
    ) + _checksum(speed_byte, brightness, effect, 0x0A)
    color_report = bytes(
        [0x00, 0x14, 0x00, _MAG_ZONE, rgb.red, rgb.green, rgb.blue, 0x00]
    ) + _checksum(_MAG_ZONE, rgb.red, rgb.green, rgb.blue, 0x14)
    return [*_HEADERS, effect_report, color_report]


def _checksum(*values: int) -> bytes:
    return bytes([~sum(values) & 0xFF])
