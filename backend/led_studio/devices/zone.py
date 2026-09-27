"""A lighting zone: one opened LampArray together with its normalised layout."""

import logging
from dataclasses import dataclass, replace

from led_studio.devices.keyboard_vendor import KeyboardVendorInterface, vendor_interface_for
from led_studio.devices.lamparray import LampArray
from led_studio.devices.layout import layout_from_array
from led_studio.hid.descriptor import LIGHTING_USAGE_PAGE
from led_studio.hid.transport import HidapiTransport, enumerate_hid_devices
from led_studio.patterns.layout import DeviceLayout

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Zone:
    id: str
    name: str
    array: LampArray
    layout: DeviceLayout
    # Sunrex keyboards run firmware effects (keyboard-wide and MagKey) that override the
    # LampArray; their vendor interface reports and switches those off.
    vendor: KeyboardVendorInterface | None = None

    def with_vendor(self, vendor: KeyboardVendorInterface) -> "Zone":
        return replace(self, vendor=vendor)

    def take_control(self) -> None:
        """Stop every firmware effect on this zone so host updates are shown on all lamps."""
        if self.vendor is None:
            self.array.take_control()
            return
        effect = self.vendor.firmware_effect()
        if effect is not None:
            # The firmware ignores a repeated host-control request while its own effect runs;
            # only a firmware -> host transition hands the keys back to the LampArray.
            log.info("zone %s: firmware effect %#04x took over; handing back", self.id, effect)
            self.array.release_control()
        self.array.take_control()
        self.vendor.disable_magkey_effect()

    def release_control(self) -> None:
        # The MagKey mode stays off: the firmware's own effect then covers A/W/S/D as well.
        self.array.release_control()

    def close(self) -> None:
        self.array.close()
        if self.vendor is not None:
            self.vendor.close()


def open_zones() -> list[Zone]:
    """Open every LampArray on the machine. Zones that fail to open are skipped, not fatal."""
    devices = enumerate_hid_devices()
    zones = []
    for info in devices:
        if info.usage_page != LIGHTING_USAGE_PAGE:
            continue
        array = LampArray.open(HidapiTransport(info))
        zone = Zone(
            id=info.id,
            name=" ".join(info.product.split()) or info.id,  # firmware pads "Pmma  Logo"
            array=array,
            layout=layout_from_array(info.id, array.attributes, array.lamps),
        )
        vendor = vendor_interface_for(info, devices)
        if vendor is not None:
            zone = zone.with_vendor(KeyboardVendorInterface(HidapiTransport(vendor)))
        zones.append(zone)
    return zones
