"""Wire types for the HTTP/WebSocket API that are not already pattern models."""

from pydantic import BaseModel

from led_studio.devices.zone import Zone
from led_studio.hid.reports import kind_name
from led_studio.playback.player import Frame


class LampOut(BaseModel):
    id: int
    x: float
    y: float
    key: int  # HID keyboard usage bound to this lamp, 0 when none


class DeviceOut(BaseModel):
    id: str
    name: str
    kind: str
    lamp_count: int
    width_mm: float
    height_mm: float
    lamps: list[LampOut]

    @classmethod
    def from_zone(cls, zone: Zone) -> "DeviceOut":
        attrs = zone.array.attributes
        return cls(
            id=zone.id,
            name=zone.name,
            kind=kind_name(attrs.kind),
            lamp_count=attrs.lamp_count,
            width_mm=attrs.width_um / 1000,
            height_mm=attrs.height_um / 1000,
            lamps=[
                LampOut(id=lamp.id, x=lamp.x, y=lamp.y, key=attrs_lamp.input_binding)
                for lamp, attrs_lamp in zip(zone.layout.lamps, zone.array.lamps, strict=True)
            ],
        )


class PlaybackOut(BaseModel):
    pattern_id: str | None
    preview: bool


class ApplyIn(BaseModel):
    pattern_id: str


FrameOut = dict[str, list[tuple[int, int, int]]]


def frame_out(frame: Frame) -> FrameOut:
    return {
        zone_id: [(c.red, c.green, c.blue) for c in colors] for zone_id, colors in frame.items()
    }
