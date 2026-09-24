from led_studio.devices.layout import layout_from_array
from led_studio.patterns.layout import Lamp
from tests.fakes import make_array, make_lamp


def test_layout_normalises_lamp_positions_to_array_bounds() -> None:
    array = make_array(lamp_count=2)  # 340000 x 105000 um
    lamps = [make_lamp(0, x_um=0, y_um=0), make_lamp(1, x_um=170000, y_um=105000)]

    layout = layout_from_array("dev", array, lamps)

    assert layout.id == "dev"
    assert layout.lamps == (Lamp(0, 0.0, 0.0), Lamp(1, 0.5, 1.0))


def test_zero_sized_axis_maps_to_centre() -> None:
    array = make_array(lamp_count=1).__class__(
        lamp_count=1, width_um=0, height_um=0, depth_um=0, kind=1, min_update_interval_us=1
    )

    layout = layout_from_array("dev", array, [make_lamp(0, x_um=0, y_um=0)])

    assert layout.lamps == (Lamp(0, 0.5, 0.5),)
