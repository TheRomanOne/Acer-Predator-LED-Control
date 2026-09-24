"""Pure frame rendering: (pattern, device layouts, time) -> colour per lamp.

Colours are handled as floats in 0..1 until the final quantisation so that blending and
brightness do not accumulate rounding error.
"""

import colorsys
import math
from collections.abc import Sequence
from functools import singledispatch

from led_studio.hid.reports import Rgb
from led_studio.patterns.layout import DeviceLayout, Lamp
from led_studio.patterns.model import (
    Breathing,
    Color,
    Gradient,
    Keyframes,
    Paint,
    Pattern,
    Rainbow,
    Ripple,
    Solid,
    Wave,
)

FloatRgb = tuple[float, float, float]
Sample = tuple[FloatRgb, float] | None  # (colour, alpha); None = fully transparent

_BLACK: FloatRgb = (0.0, 0.0, 0.0)
_RIPPLE_MAX_RADIUS = 1.5  # enough to cross a unit square from any corner


def render_frame(
    pattern: Pattern, layouts: Sequence[DeviceLayout], t: float
) -> dict[str, list[Rgb]]:
    frame: dict[str, list[Rgb]] = {}
    for layout in layouts:
        colors = [_BLACK] * len(layout.lamps)
        for layer in pattern.layers:
            if not layer.enabled or (layer.devices is not None and layout.id not in layer.devices):
                continue
            for index, lamp in enumerate(layout.lamps):
                sample = _sample(layer.effect, lamp, t)
                if sample is None:
                    continue
                color, alpha = sample
                colors[index] = _blend(colors[index], color, alpha * layer.opacity)
        frame[layout.id] = [_quantise(c, pattern.brightness) for c in colors]
    return frame


def _blend(under: FloatRgb, over: FloatRgb, alpha: float) -> FloatRgb:
    return (
        under[0] * (1 - alpha) + over[0] * alpha,
        under[1] * (1 - alpha) + over[1] * alpha,
        under[2] * (1 - alpha) + over[2] * alpha,
    )


def _quantise(color: FloatRgb, brightness: float) -> Rgb:
    return Rgb(*(round(min(max(c * brightness, 0.0), 1.0) * 255) for c in color))


def _to_float(color: Color) -> FloatRgb:
    return (color.r / 255, color.g / 255, color.b / 255)


def _scale(color: FloatRgb, factor: float) -> FloatRgb:
    return (color[0] * factor, color[1] * factor, color[2] * factor)


def _lerp(a: FloatRgb, b: FloatRgb, f: float) -> FloatRgb:
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f)


def _project(lamp: Lamp, angle_deg: float) -> float:
    """Position of the lamp along a direction, normalised so the unit square spans 0..1."""
    cos, sin = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    corners = [x * cos + y * sin for x in (0.0, 1.0) for y in (0.0, 1.0)]
    lo, hi = min(corners), max(corners)
    if hi - lo < 1e-9:
        return 0.5
    return (lamp.x * cos + lamp.y * sin - lo) / (hi - lo)


def _cyclic_color(colors: list[Color], phase: float) -> FloatRgb:
    """Interpolate through the colour list and back to the first at phase 1."""
    if len(colors) == 1:
        return _to_float(colors[0])
    scaled = (phase % 1.0) * len(colors)
    index = int(scaled)
    return _lerp(
        _to_float(colors[index]), _to_float(colors[(index + 1) % len(colors)]), scaled - index
    )


@singledispatch
def _sample(effect: object, lamp: Lamp, t: float) -> Sample:
    raise TypeError(f"no renderer for effect {type(effect).__name__}")


@_sample.register
def _(effect: Solid, lamp: Lamp, t: float) -> Sample:
    return _to_float(effect.color), 1.0


@_sample.register
def _(effect: Gradient, lamp: Lamp, t: float) -> Sample:
    u = _project(lamp, effect.angle_deg)
    stops = sorted(effect.stops, key=lambda s: s.position)
    if u <= stops[0].position:
        return _to_float(stops[0].color), 1.0
    for left, right in zip(stops, stops[1:], strict=False):
        if u <= right.position:
            span = right.position - left.position
            f = 0.0 if span == 0 else (u - left.position) / span
            return _lerp(_to_float(left.color), _to_float(right.color), f), 1.0
    return _to_float(stops[-1].color), 1.0


@_sample.register
def _(effect: Wave, lamp: Lamp, t: float) -> Sample:
    phase = _project(lamp, effect.angle_deg) / effect.wavelength - t * effect.speed
    return _cyclic_color(effect.colors, phase), 1.0


@_sample.register
def _(effect: Breathing, lamp: Lamp, t: float) -> Sample:
    level = 0.5 + 0.5 * math.cos(2 * math.pi * t / effect.period_s)
    factor = effect.min_brightness + (1 - effect.min_brightness) * level
    return _scale(_to_float(effect.color), factor), 1.0


@_sample.register
def _(effect: Rainbow, lamp: Lamp, t: float) -> Sample:
    hue = (_project(lamp, effect.angle_deg) * effect.scale + t * effect.speed) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (r, g, b), 1.0


@_sample.register
def _(effect: Paint, lamp: Lamp, t: float) -> Sample:
    color = effect.colors.get(lamp.id)
    return None if color is None else (_to_float(color), 1.0)


@_sample.register
def _(effect: Ripple, lamp: Lamp, t: float) -> Sample:
    radius = (t / effect.period_s % 1.0) * _RIPPLE_MAX_RADIUS
    distance = math.hypot(lamp.x - effect.origin_x, lamp.y - effect.origin_y)
    intensity = max(0.0, 1.0 - abs(distance - radius) / effect.width)
    return None if intensity == 0 else (_to_float(effect.color), intensity)


@_sample.register
def _(effect: Keyframes, lamp: Lamp, t: float) -> Sample:
    frames = sorted(effect.frames, key=lambda f: f.time_s)
    loop_length = frames[-1].time_s
    local = t % loop_length if loop_length > 0 else 0.0
    current = frames[0]
    for frame in frames:
        if frame.time_s > local:
            if not effect.interpolate:
                break
            span = frame.time_s - current.time_s
            f = 0.0 if span == 0 else (local - current.time_s) / span
            return _lerp(_to_float(current.color), _to_float(frame.color), f), 1.0
        current = frame
    return _to_float(current.color), 1.0
