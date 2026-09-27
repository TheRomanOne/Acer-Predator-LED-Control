"""The Sunrex keyboard's vendor interface: its MagKey zone (A/W/S/D) and active lighting mode."""

import time
from collections.abc import Callable, Iterable

from led_studio.hid.sunrex import (
    HOST_MODE,
    REPORT_GAP_S,
    STATE_REPORT_ID,
    STATE_REPORT_SIZE,
    SUNREX_VENDOR_ID,
    SUNREX_VENDOR_USAGE_PAGE,
    MagKeyEffect,
    pack_magkey_effect,
    unpack_active_mode,
)
from led_studio.hid.transport import HidDeviceInfo, HidTransport


def vendor_interface_for(
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


class KeyboardVendorInterface:
    def __init__(
        self, transport: HidTransport, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._transport = transport
        self._sleep = sleep

    def firmware_effect(self) -> int | None:
        """The keyboard-wide firmware effect overriding LampArray updates, if any."""
        mode = unpack_active_mode(
            self._transport.get_feature_report(STATE_REPORT_ID, STATE_REPORT_SIZE)
        )
        return None if mode == HOST_MODE else mode

    def disable_magkey_effect(self) -> None:
        """Switch the MagKey mode off so A/W/S/D follow the LampArray like every other key."""
        reports = pack_magkey_effect(MagKeyEffect.OFF, brightness_pct=0, color=None)
        for index, report in enumerate(reports):
            self._transport.send_feature_report(report)
            if index + 1 < len(reports):
                self._sleep(REPORT_GAP_S)

    def close(self) -> None:
        self._transport.close()
