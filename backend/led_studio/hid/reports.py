"""Packing and unpacking of HID LampArray feature reports (HUT 1.5 §25).

All reports are little-endian and carry their report ID as the first byte, which is the
convention hidapi uses for both get_feature_report and send_feature_report.
"""

import struct
from dataclasses import dataclass
from enum import IntEnum, IntFlag

FULL_INTENSITY = 0xFF


class LampArrayKind(IntEnum):
    KEYBOARD = 1
    MOUSE = 2
    GAME_CONTROLLER = 3
    PERIPHERAL = 4
    SCENE = 5
    NOTIFICATION = 6
    CHASSIS = 7
    WEARABLE = 8
    FURNITURE = 9
    ART = 10


def kind_name(kind: int) -> str:
    """Human label for a LampArrayKind, tolerating values outside the spec."""
    try:
        return LampArrayKind(kind).name.lower()
    except ValueError:
        return f"kind-{kind}"


class LampPurpose(IntFlag):
    CONTROL = 0x01
    ACCENT = 0x02
    BRANDING = 0x04
    STATUS = 0x08
    ILLUMINATION = 0x10
    PRESENTATION = 0x20


@dataclass(frozen=True, slots=True)
class Rgb:
    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        for name, value in (("red", self.red), ("green", self.green), ("blue", self.blue)):
            if not 0 <= value <= 255:
                raise ValueError(f"{name} channel must be 0-255, got {value}")


@dataclass(frozen=True, slots=True)
class LampArrayAttributes:
    lamp_count: int
    width_um: int
    height_um: int
    depth_um: int
    kind: int  # LampArrayKind when known; firmware may report values outside the enum
    min_update_interval_us: int


@dataclass(frozen=True, slots=True)
class LampAttributes:
    lamp_id: int
    x_um: int
    y_um: int
    z_um: int
    update_latency_us: int
    purposes: LampPurpose
    red_levels: int
    green_levels: int
    blue_levels: int
    intensity_levels: int
    is_programmable: bool
    input_binding: int


_ARRAY_ATTRIBUTES = struct.Struct("<HIIIII")
_LAMP_ATTRIBUTES = struct.Struct("<HIIIIIBBBBBB")
_LAMP_ID = struct.Struct("<H")
_RANGE_UPDATE = struct.Struct("<BHH")

# Total report sizes including the report ID byte. Some firmware (the Sunrex keyboard) stalls
# a GET_REPORT whose requested length differs from the report's real size, so callers must
# request exactly these.
ARRAY_ATTRIBUTES_REPORT_SIZE = 1 + _ARRAY_ATTRIBUTES.size
LAMP_ATTRIBUTES_REPORT_SIZE = 1 + _LAMP_ATTRIBUTES.size


def _payload(report: bytes, expected_id: int, payload_struct: struct.Struct) -> bytes:
    if not report or report[0] != expected_id:
        got = report[0] if report else None
        raise ValueError(f"unexpected report ID {got!r}, expected {expected_id:#x}")
    payload = report[1 : 1 + payload_struct.size]
    if len(payload) < payload_struct.size:
        raise ValueError(
            f"report {expected_id:#x} too short: {len(payload)} bytes, need {payload_struct.size}"
        )
    return payload


def unpack_array_attributes(report: bytes, report_id: int) -> LampArrayAttributes:
    fields = _ARRAY_ATTRIBUTES.unpack(_payload(report, report_id, _ARRAY_ATTRIBUTES))
    count, width, height, depth, kind, interval = fields
    return LampArrayAttributes(
        lamp_count=count,
        width_um=width,
        height_um=height,
        depth_um=depth,
        kind=_known_kind(kind),
        min_update_interval_us=interval,
    )


def unpack_lamp_attributes(report: bytes, report_id: int) -> LampAttributes:
    fields = _LAMP_ATTRIBUTES.unpack(_payload(report, report_id, _LAMP_ATTRIBUTES))
    lamp_id, x, y, z, latency, purposes, red, green, blue, intensity, programmable, binding = fields
    return LampAttributes(
        lamp_id=lamp_id,
        x_um=x,
        y_um=y,
        z_um=z,
        update_latency_us=latency,
        purposes=LampPurpose(purposes),
        red_levels=red,
        green_levels=green,
        blue_levels=blue,
        intensity_levels=intensity,
        is_programmable=bool(programmable),
        input_binding=binding,
    )


def _known_kind(kind: int) -> int:
    try:
        return LampArrayKind(kind)
    except ValueError:
        return kind


def pack_attributes_request(report_id: int, lamp_id: int) -> bytes:
    return bytes([report_id]) + _LAMP_ID.pack(lamp_id)


def pack_control(report_id: int, autonomous: bool) -> bytes:
    return bytes([report_id, int(autonomous)])


def pack_range_update(report_id: int, start: int, end: int, color: Rgb, last: bool) -> bytes:
    return bytes([report_id]) + _RANGE_UPDATE.pack(int(last), start, end) + _color_bytes(color)


def pack_multi_update(
    report_id: int, slots: int, updates: list[tuple[int, Rgb]], last: bool
) -> bytes:
    if len(updates) > slots:
        raise ValueError(f"{len(updates)} updates exceed the report's {slots} slots")
    ids = b"".join(_LAMP_ID.pack(lamp_id) for lamp_id, _ in updates)
    colors = b"".join(_color_bytes(color) for _, color in updates)
    unused = slots - len(updates)
    return (
        bytes([report_id, len(updates), int(last)])
        + ids
        + bytes(_LAMP_ID.size * unused)
        + colors
        + bytes(4 * unused)
    )


def _color_bytes(color: Rgb) -> bytes:
    return bytes([color.red, color.green, color.blue, FULL_INTENSITY])
