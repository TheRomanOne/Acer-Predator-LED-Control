import pytest

from led_studio.hid.reports import Rgb
from led_studio.patterns.layout import DeviceLayout, Lamp
from led_studio.patterns.model import (
    Breathing,
    Color,
    Gradient,
    Keyframes,
    Layer,
    Paint,
    Pattern,
    Rainbow,
    Ripple,
    Solid,
    Wave,
)
from led_studio.patterns.render import render_frame

# A 3-lamp strip along X and a single-lamp logo.
STRIP = DeviceLayout(id="strip", lamps=(Lamp(0, 0.0, 0.5), Lamp(1, 0.5, 0.5), Lamp(2, 1.0, 0.5)))
LOGO = DeviceLayout(id="logo", lamps=(Lamp(0, 0.5, 0.5),))
RED = Color(r=255, g=0, b=0)
BLUE = Color(r=0, g=0, b=255)
BLACK = Color(r=0, g=0, b=0)


def pattern(*layers: Layer, brightness: float = 1.0) -> Pattern:
    return Pattern(id="t", name="t", layers=list(layers), brightness=brightness)


def test_empty_pattern_renders_black_for_every_lamp() -> None:
    frame = render_frame(pattern(), [STRIP, LOGO], t=0)

    assert frame == {"strip": [Rgb(0, 0, 0)] * 3, "logo": [Rgb(0, 0, 0)]}


def test_solid_applies_to_all_devices_unless_targeted() -> None:
    targeted = Layer(effect=Solid(color=RED), devices=["logo"])
    frame = render_frame(pattern(targeted), [STRIP, LOGO], t=0)

    assert frame["logo"] == [Rgb(255, 0, 0)]
    assert frame["strip"] == [Rgb(0, 0, 0)] * 3


def test_brightness_scales_output() -> None:
    frame = render_frame(pattern(Layer(effect=Solid(color=RED)), brightness=0.5), [LOGO], t=0)

    assert frame["logo"] == [Rgb(128, 0, 0)]


def test_layers_blend_by_opacity_in_order() -> None:
    base = Layer(effect=Solid(color=RED))
    overlay = Layer(effect=Solid(color=BLUE), opacity=0.5)
    frame = render_frame(pattern(base, overlay), [LOGO], t=0)

    assert frame["logo"] == [Rgb(128, 0, 128)]


def test_disabled_layer_is_skipped() -> None:
    frame = render_frame(pattern(Layer(effect=Solid(color=RED), enabled=False)), [LOGO], t=0)

    assert frame["logo"] == [Rgb(0, 0, 0)]


def test_gradient_interpolates_along_angle() -> None:
    gradient = Gradient(
        stops=[Gradient.Stop(position=0, color=BLACK), Gradient.Stop(position=1, color=RED)],
        angle_deg=0,
    )
    frame = render_frame(pattern(Layer(effect=gradient)), [STRIP], t=0)

    assert frame["strip"] == [Rgb(0, 0, 0), Rgb(128, 0, 0), Rgb(255, 0, 0)]


def test_wave_moves_with_time() -> None:
    wave = Wave(colors=[RED, BLUE], speed=1.0, wavelength=1.0, angle_deg=0)
    at_start = render_frame(pattern(Layer(effect=wave)), [STRIP], t=0)["strip"]
    half_cycle_later = render_frame(pattern(Layer(effect=wave)), [STRIP], t=0.5)["strip"]

    assert at_start[0] == Rgb(255, 0, 0)
    assert half_cycle_later[0] == Rgb(0, 0, 255)
    # one full cycle later the frame repeats
    assert render_frame(pattern(Layer(effect=wave)), [STRIP], t=1.0)["strip"] == at_start


def test_breathing_dims_to_floor_at_half_period() -> None:
    breathing = Breathing(color=RED, period_s=2.0, min_brightness=0.2)
    peak = render_frame(pattern(Layer(effect=breathing)), [LOGO], t=0)["logo"][0]
    trough = render_frame(pattern(Layer(effect=breathing)), [LOGO], t=1.0)["logo"][0]

    assert peak == Rgb(255, 0, 0)
    assert trough == Rgb(51, 0, 0)


def test_rainbow_cycles_hue_across_space_and_time() -> None:
    rainbow = Rainbow(speed=0.0, scale=1.0, angle_deg=0)
    frame = render_frame(pattern(Layer(effect=rainbow)), [STRIP], t=0)["strip"]

    assert frame[0] == Rgb(255, 0, 0)  # hue 0
    assert frame[1] == Rgb(0, 255, 255)  # hue 0.5
    moved = Rainbow(speed=0.5, scale=1.0, angle_deg=0)
    assert render_frame(pattern(Layer(effect=moved)), [STRIP], t=1.0)["strip"][0] == Rgb(
        0, 255, 255
    )


def test_paint_sets_only_listed_lamps_and_leaves_others_transparent() -> None:
    base = Layer(effect=Solid(color=BLUE))
    paint = Layer(effect=Paint(colors={1: RED}), devices=["strip"])
    frame = render_frame(pattern(base, paint), [STRIP], t=0)["strip"]

    assert frame == [Rgb(0, 0, 255), Rgb(255, 0, 0), Rgb(0, 0, 255)]


def test_ripple_is_bright_on_the_ring_and_transparent_elsewhere() -> None:
    ripple = Ripple(color=RED, origin_x=0.0, origin_y=0.5, period_s=1.0, width=0.1)
    # at t=0.5 the ring radius is half the max radius (1.5 * 0.5 = 0.75)
    frame = render_frame(pattern(Layer(effect=ripple)), [STRIP], t=0.5)["strip"]

    assert frame[0] == Rgb(0, 0, 0)
    assert frame[2] == Rgb(0, 0, 0)
    ring = Ripple(color=RED, origin_x=0.0, origin_y=0.5, period_s=1.0, width=0.1)
    on_ring = render_frame(pattern(Layer(effect=ring)), [STRIP], t=1 / 3)["strip"]
    assert on_ring[1] == Rgb(255, 0, 0)


def test_keyframes_interpolate_and_loop() -> None:
    frames = Keyframes(
        frames=[Keyframes.Frame(time_s=0, color=BLACK), Keyframes.Frame(time_s=2, color=RED)],
        interpolate=True,
    )
    layer = Layer(effect=frames)

    assert render_frame(pattern(layer), [LOGO], t=1.0)["logo"] == [Rgb(128, 0, 0)]
    assert render_frame(pattern(layer), [LOGO], t=1.5)["logo"] == [Rgb(191, 0, 0)]
    # the last frame's time is the loop length: the sequence restarts from the first frame
    assert render_frame(pattern(layer), [LOGO], t=2.0)["logo"] == [Rgb(0, 0, 0)]
    assert render_frame(pattern(layer), [LOGO], t=3.0)["logo"] == [Rgb(128, 0, 0)]

    stepped = Layer(effect=frames.model_copy(update={"interpolate": False}))
    assert render_frame(pattern(stepped), [LOGO], t=1.0)["logo"] == [Rgb(0, 0, 0)]


@pytest.mark.parametrize("angle", [0, 45, 90, 180, 270])
def test_projection_stays_in_unit_interval_for_corners(angle: float) -> None:
    corners = DeviceLayout(
        id="c", lamps=(Lamp(0, 0, 0), Lamp(1, 1, 0), Lamp(2, 0, 1), Lamp(3, 1, 1))
    )
    gradient = Gradient(
        stops=[Gradient.Stop(position=0, color=BLACK), Gradient.Stop(position=1, color=RED)],
        angle_deg=angle,
    )
    frame = render_frame(pattern(Layer(effect=gradient)), [corners], t=0)["c"]

    assert all(0 <= c.red <= 255 for c in frame)
    assert Rgb(0, 0, 0) in frame
    assert Rgb(255, 0, 0) in frame
