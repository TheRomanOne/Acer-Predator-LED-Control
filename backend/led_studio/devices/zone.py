"""A lighting zone: one opened LampArray together with its normalised layout."""

from dataclasses import dataclass, replace

from led_studio.devices.lamparray import LampArray
from led_studio.devices.layout import layout_from_array
from led_studio.devices.magkey import MagKeyController, magkey_interface_for
from led_studio.hid.descriptor import LIGHTING_USAGE_PAGE
from led_studio.hid.transport import HidapiTransport, enumerate_hid_devices
from led_studio.patterns.layout import DeviceLayout


@dataclass(frozen=True, slots=True)
class Zone:
    id: str
    name: str
    array: LampArray
    layout: DeviceLayout
    # Keyboards with MagKey caps paint A/W/S/D themselves unless that mode is switched off.
    magkey: MagKeyController | None = None

    def with_magkey(self, magkey: MagKeyController) -> "Zone":
        return replace(self, magkey=magkey)

    def take_control(self) -> None:
        """Stop every firmware effect on this zone so host updates are shown on all lamps."""
        self.array.take_control()
        if self.magkey is not None:
            self.magkey.disable_effect()

    def release_control(self) -> None:
        # The MagKey mode stays off: the firmware's own effect then covers A/W/S/D as well.
        self.array.release_control()

    def close(self) -> None:
        self.array.close()
        if self.magkey is not None:
            self.magkey.close()


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
        vendor = magkey_interface_for(info, devices)
        if vendor is not None:
            zone = zone.with_magkey(MagKeyController(HidapiTransport(vendor)))
        zones.append(zone)
    return zones
