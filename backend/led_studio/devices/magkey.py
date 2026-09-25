"""The keyboard's MagKey zone (A/W/S/D), reached through the Sunrex vendor interface."""

import time
from collections.abc import Callable, Iterable

from led_studio.hid.sunrex import (
    REPORT_GAP_S,
    SUNREX_VENDOR_ID,
    SUNREX_VENDOR_USAGE_PAGE,
    MagKeyEffect,
    pack_magkey_effect,
)
from led_studio.hid.transport import HidDeviceInfo, HidTransport


def magkey_interface_for(
    keyboard: HidDeviceInfo, devices: Iterable[HidDeviceInfo]
) -> HidDeviceInfo | None:
    """The vendor interface of the same Sunrex keyboard as `keyboard`, if it has one."""
    if keyboard.vendor_id != SUNREX_VENDOR_ID:
        return None
    return next(
        (
            info
            for info in devices
            if info.vendor_id == keyboard.vendor_id
            and info.product_id == keyboard.product_id
            and info.usage_page == SUNREX_VENDOR_USAGE_PAGE
        ),
        None,
    )


class MagKeyController:
    def __init__(
        self, transport: HidTransport, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._transport = transport
        self._sleep = sleep

    def disable_effect(self) -> None:
        """Switch the MagKey mode off so A/W/S/D follow the LampArray like every other key."""
        reports = pack_magkey_effect(MagKeyEffect.OFF, brightness_pct=0, color=None)
        for index, report in enumerate(reports):
            self._transport.send_feature_report(report)
            if index + 1 < len(reports):
                self._sleep(REPORT_GAP_S)

    def close(self) -> None:
        self._transport.close()
