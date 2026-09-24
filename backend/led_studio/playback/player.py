"""Drives the zones with rendered frames, sending only what changed since the last frame."""

import time
from collections.abc import Callable, Sequence

from led_studio.devices.zone import Zone
from led_studio.hid.reports import Rgb
from led_studio.patterns.model import Pattern
from led_studio.patterns.render import render_frame

Frame = dict[str, list[Rgb]]
BLACK = Rgb(0, 0, 0)


class Player:
    def __init__(self, zones: Sequence[Zone], clock: Callable[[], float] = time.monotonic) -> None:
        self._zones = {zone.id: zone for zone in zones}
        self._clock = clock
        self._started_at = 0.0
        self._shown: dict[str, list[Rgb]] = {}  # what each zone currently displays
        self.current: Pattern | None = None
        self.last_frame: Frame = {}

    @property
    def zones(self) -> list[Zone]:
        return list(self._zones.values())

    def play(self, pattern: Pattern) -> None:
        if self.current is None:
            for zone in self._zones.values():
                zone.array.take_control()
        self.current = pattern
        self._started_at = self._clock()

    def reassert_control(self) -> None:
        """Retake the zones from competing software (e.g. the vendor lighting service).

        Whatever it displayed in the meantime is unknown, so the next frame repaints fully.
        """
        if self.current is None:
            return
        for zone in self._zones.values():
            zone.array.take_control()
        self._shown.clear()

    def elapsed(self) -> float:
        return self._clock() - self._started_at

    def render(self, t: float | None = None) -> Frame:
        if self.current is None:
            return {}
        layouts = [zone.layout for zone in self._zones.values()]
        self.last_frame = render_frame(self.current, layouts, self.elapsed() if t is None else t)
        return self.last_frame

    def push(self, zone_id: str, colors: list[Rgb]) -> None:
        zone = self._zones[zone_id]
        shown = self._shown.get(zone_id)
        if shown == colors:
            return
        if all(c == colors[0] for c in colors):
            zone.array.fill(colors[0])
        else:
            changed = {
                lamp_id: color
                for lamp_id, color in enumerate(colors)
                if shown is None or shown[lamp_id] != color
            }
            zone.array.set_lamps(changed)
        self._shown[zone_id] = colors

    def render_and_push(self, t: float | None = None) -> Frame:
        frame = self.render(t)
        for zone_id, colors in frame.items():
            self.push(zone_id, colors)
        return frame

    def stop(self) -> None:
        if self.current is None:
            return
        for zone in self._zones.values():
            self.push(zone.id, [BLACK] * zone.array.lamp_count)
            zone.array.release_control()
        self.current = None
        self.last_frame = {}
        self._shown.clear()

    def close(self) -> None:
        self.stop()
        for zone in self._zones.values():
            zone.array.close()
