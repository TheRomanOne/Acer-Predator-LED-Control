"""In-memory emulation of a HID LampArray device, for tests above the transport layer."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from led_studio.devices.lamparray import LampArray
from led_studio.devices.layout import layout_from_array
from led_studio.devices.zone import Zone
from led_studio.hid.descriptor import LampArrayReportIds
from led_studio.hid.reports import LampArrayAttributes, LampAttributes
from led_studio.hid.sunrex import HOST_MODE, STATE_REPORT_ID
from tests.test_descriptor import LAMPARRAY_DESCRIPTOR

STANDARD_IDS = LampArrayReportIds(
    attributes=0x02,
    attributes_request=0x20,
    attributes_response=0x22,
    multi_update=0x50,
    range_update=0x60,
    control=0x70,
    multi_update_slots=8,
)


def make_lamp(lamp_id: int, x_um: int = 0, y_um: int = 0, purposes: int = 1) -> LampAttributes:
    return LampAttributes(
        lamp_id=lamp_id,
        x_um=x_um,
        y_um=y_um,
        z_um=0,
        update_latency_us=4000,
        purposes=purposes,  # type: ignore[arg-type]
        red_levels=255,
        green_levels=255,
        blue_levels=255,
        intensity_levels=255,
        is_programmable=True,
        input_binding=0,
    )


def make_array(lamp_count: int, kind: int = 1) -> LampArrayAttributes:
    return LampArrayAttributes(
        lamp_count=lamp_count,
        width_um=340000,
        height_um=105000,
        depth_um=0,
        kind=kind,
        min_update_interval_us=33000,
    )


def make_fake_zone(
    zone_id: str = "z", name: str = "Fake", lamp_count: int = 3, kind: int = 7
) -> tuple[Zone, FakeLampArrayTransport]:
    """An opened Zone backed by an in-memory device, with the open handshake already cleared."""
    transport = FakeLampArrayTransport(
        array=make_array(lamp_count, kind=kind),
        lamps=[make_lamp(i, x_um=i * 1000, purposes=1) for i in range(lamp_count)],
    )
    array = LampArray.open(transport)
    transport.sent.clear()
    transport.get_requests.clear()
    zone = Zone(
        id=zone_id,
        name=name,
        array=array,
        layout=layout_from_array(zone_id, array.attributes, array.lamps),
    )
    return zone, transport


@dataclass
class FakeLampArrayTransport:
    array: LampArrayAttributes
    lamps: list[LampAttributes]
    descriptor: bytes = LAMPARRAY_DESCRIPTOR
    ids: LampArrayReportIds = STANDARD_IDS
    sent: list[bytes] = field(default_factory=list)
    get_requests: list[tuple[int, int]] = field(default_factory=list)
    closed: bool = False
    _requested_lamp: int = 0

    def report_descriptor(self) -> bytes:
        return self.descriptor

    def get_feature_report(self, report_id: int, length: int) -> bytes:
        self.get_requests.append((report_id, length))
        if report_id == self.ids.attributes:
            a = self.array
            payload = struct.pack(
                "<HIIIII",
                a.lamp_count,
                a.width_um,
                a.height_um,
                a.depth_um,
                a.kind,
                a.min_update_interval_us,
            )
        elif report_id == self.ids.attributes_response:
            lamp = self.lamps[self._requested_lamp]
            payload = struct.pack(
                "<HIIIIIBBBBBB",
                lamp.lamp_id,
                lamp.x_um,
                lamp.y_um,
                lamp.z_um,
                lamp.update_latency_us,
                int(lamp.purposes),
                lamp.red_levels,
                lamp.green_levels,
                lamp.blue_levels,
                lamp.intensity_levels,
                int(lamp.is_programmable),
                lamp.input_binding,
            )
        else:
            raise OSError(f"fake device: report {report_id:#x} is not readable")
        report = bytes([report_id]) + payload
        if length != len(report):
            raise OSError(f"fake device: wrong length {length} for report {report_id:#x}")
        return report

    def send_feature_report(self, report: bytes) -> None:
        self.sent.append(report)
        if report[0] == self.ids.attributes_request:
            self._requested_lamp = int.from_bytes(report[1:3], "little")

    def close(self) -> None:
        self.closed = True


@dataclass
class FakeVendorTransport:
    """The Sunrex keyboard's vendor interface: records commands, reports `mode` as active."""

    mode: int = HOST_MODE
    sent: list[bytes] = field(default_factory=list)
    closed: bool = False

    def report_descriptor(self) -> bytes:
        return b""

    def get_feature_report(self, report_id: int, length: int) -> bytes:
        # Shape of the state report read from the PH16-73 keyboard (mode in byte 3).
        report = bytes([0x00, 0x88, 0x00, self.mode, 0x03, 0x32, 0x00, 0x00, 0x00])
        if (report_id, length) != (STATE_REPORT_ID, len(report)):
            raise OSError(f"fake vendor interface: no report {report_id:#x} of {length} bytes")
        return report

    def send_feature_report(self, report: bytes) -> None:
        self.sent.append(report)

    def close(self) -> None:
        self.closed = True
