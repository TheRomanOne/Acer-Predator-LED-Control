"""Convert firmware lamp geometry (micrometres) into the renderer's normalised layout."""

from collections.abc import Sequence

from led_studio.hid.reports import LampArrayAttributes, LampAttributes
from led_studio.patterns.layout import DeviceLayout, Lamp


def layout_from_array(
    device_id: str, array: LampArrayAttributes, lamps: Sequence[LampAttributes]
) -> DeviceLayout:
    return DeviceLayout(
        id=device_id,
        lamps=tuple(
            Lamp(
                id=lamp.lamp_id,
                x=_normalise(lamp.x_um, array.width_um),
                y=_normalise(lamp.y_um, array.height_um),
            )
            for lamp in lamps
        ),
    )


def _normalise(value_um: int, extent_um: int) -> float:
    # A flat axis (e.g. a one-row strip) puts every lamp on the centre line.
    return 0.5 if extent_um <= 0 else min(max(value_um / extent_um, 0.0), 1.0)
