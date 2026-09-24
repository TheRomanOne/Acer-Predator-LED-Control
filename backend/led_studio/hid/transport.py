"""OS-level HID access. This is the only module that touches hidapi.

hidapi uses the native HID stack on Windows and hidraw on Linux, so a single adapter covers both
platforms. Everything above this layer works with plain bytes and is tested with fakes.
"""

from dataclasses import dataclass
from typing import Protocol

import hid

from led_studio.hid.descriptor import LIGHTING_USAGE_PAGE


class HidError(OSError):
    """A HID operation failed at the OS or device level."""


class HidTransport(Protocol):
    def report_descriptor(self) -> bytes: ...

    def get_feature_report(self, report_id: int, length: int) -> bytes: ...

    def send_feature_report(self, report: bytes) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class HidDeviceInfo:
    path: bytes
    vendor_id: int
    product_id: int
    interface_number: int
    product: str

    @property
    def id(self) -> str:
        """Stable identifier: same device keeps the same id across app restarts."""
        return f"{self.vendor_id:04x}:{self.product_id:04x}:{self.interface_number}"


def enumerate_lamparray_devices() -> list[HidDeviceInfo]:
    return [
        HidDeviceInfo(
            path=info["path"],
            vendor_id=info["vendor_id"],
            product_id=info["product_id"],
            interface_number=info["interface_number"],
            product=info["product_string"] or "",
        )
        for info in hid.enumerate()
        if info["usage_page"] == LIGHTING_USAGE_PAGE
    ]


class HidapiTransport:
    def __init__(self, info: HidDeviceInfo) -> None:
        self._info = info
        self._device = hid.device()
        try:
            self._device.open_path(info.path)
        except OSError as exc:
            raise HidError(f"cannot open {info.id} ({info.product}): {exc}") from exc

    def report_descriptor(self) -> bytes:
        return bytes(self._device.get_report_descriptor())

    def get_feature_report(self, report_id: int, length: int) -> bytes:
        try:
            return bytes(self._device.get_feature_report(report_id, length))
        except OSError as exc:
            raise HidError(
                f"{self._info.id}: get feature {report_id:#x} ({length} bytes) failed: "
                f"{exc} [{self._device.error()}]"
            ) from exc

    def send_feature_report(self, report: bytes) -> None:
        try:
            self._device.send_feature_report(report)
        except OSError as exc:
            raise HidError(
                f"{self._info.id}: send feature {report[0]:#x} failed: {exc} "
                f"[{self._device.error()}]"
            ) from exc

    def close(self) -> None:
        self._device.close()
