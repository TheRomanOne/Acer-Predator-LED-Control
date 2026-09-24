"""Device geometry as the renderer sees it: lamps at normalised positions."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Lamp:
    id: int
    x: float  # 0..1 across the device width
    y: float  # 0..1 across the device height


@dataclass(frozen=True, slots=True)
class DeviceLayout:
    id: str
    lamps: tuple[Lamp, ...]
