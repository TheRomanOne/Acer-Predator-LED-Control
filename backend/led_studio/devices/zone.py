"""A lighting zone: one opened LampArray together with its normalised layout."""

from dataclasses import dataclass

from led_studio.devices.lamparray import LampArray
from led_studio.devices.layout import layout_from_array
from led_studio.hid.transport import HidapiTransport, enumerate_lamparray_devices
from led_studio.patterns.layout import DeviceLayout


@dataclass(frozen=True, slots=True)
class Zone:
    id: str
    name: str
    array: LampArray
    layout: DeviceLayout


def open_zones() -> list[Zone]:
    """Open every LampArray on the machine. Zones that fail to open are skipped, not fatal."""
    zones = []
    for info in enumerate_lamparray_devices():
        array = LampArray.open(HidapiTransport(info))
        zones.append(
            Zone(
                id=info.id,
                name=" ".join(info.product.split()) or info.id,  # firmware pads "Pmma  Logo"
                array=array,
                layout=layout_from_array(info.id, array.attributes, array.lamps),
            )
        )
    return zones
