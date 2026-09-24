"""User-authored lighting patterns.

A pattern is an ordered stack of layers. Each layer runs one effect over the lamps of the
devices it targets and is alpha-blended over the layers below it. This schema is the API
contract with the frontend and the on-disk format of saved patterns.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

UnitFloat = Annotated[float, Field(ge=0.0, le=1.0)]
Channel = Annotated[int, Field(ge=0, le=255)]

# Upper bounds keep a single pattern renderable at 30 fps; well above any real design.
MAX_LAYERS = 32
MAX_LIST_ITEMS = 64  # gradient stops, wave colours, keyframes
MAX_PAINTED_LAMPS = 512


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Color(_Strict):
    r: Channel
    g: Channel
    b: Channel


class Solid(_Strict):
    type: Literal["solid"] = "solid"
    color: Color


class Gradient(_Strict):
    class Stop(_Strict):
        position: UnitFloat
        color: Color

    type: Literal["gradient"] = "gradient"
    stops: list[Stop] = Field(min_length=2, max_length=MAX_LIST_ITEMS)
    angle_deg: float = 0.0


class Wave(_Strict):
    """Colours cycling along a direction, drifting over time."""

    type: Literal["wave"] = "wave"
    colors: list[Color] = Field(min_length=1, max_length=MAX_LIST_ITEMS)
    speed: float = 0.5  # cycles per second; negative reverses direction
    wavelength: Annotated[float, Field(gt=0.0)] = 1.0  # fraction of the device span per cycle
    angle_deg: float = 0.0


class Breathing(_Strict):
    type: Literal["breathing"] = "breathing"
    color: Color
    period_s: Annotated[float, Field(gt=0.0)] = 3.0
    min_brightness: UnitFloat = 0.0


class Rainbow(_Strict):
    type: Literal["rainbow"] = "rainbow"
    speed: float = 0.2  # hue cycles per second
    scale: float = 1.0  # hue cycles across the device span
    angle_deg: float = 0.0


class Paint(_Strict):
    """Explicit per-lamp colours (per-key painting). Unlisted lamps are transparent."""

    type: Literal["paint"] = "paint"
    colors: dict[int, Color] = Field(default_factory=dict, max_length=MAX_PAINTED_LAMPS)


class Ripple(_Strict):
    type: Literal["ripple"] = "ripple"
    color: Color
    origin_x: UnitFloat = 0.5
    origin_y: UnitFloat = 0.5
    period_s: Annotated[float, Field(gt=0.0)] = 2.0
    width: Annotated[float, Field(gt=0.0)] = 0.15


class Keyframes(_Strict):
    """A timed colour sequence. The last frame's time is the loop length."""

    class Frame(_Strict):
        time_s: Annotated[float, Field(ge=0.0)]
        color: Color

    type: Literal["keyframes"] = "keyframes"
    frames: list[Frame] = Field(min_length=1, max_length=MAX_LIST_ITEMS)
    interpolate: bool = True


Effect = Annotated[
    Solid | Gradient | Wave | Breathing | Rainbow | Paint | Ripple | Keyframes,
    Field(discriminator="type"),
]


class Layer(_Strict):
    effect: Effect
    opacity: UnitFloat = 1.0
    devices: list[str] | None = None  # None targets every device
    enabled: bool = True


class PatternBody(_Strict):
    """Everything the user authors; the id is assigned by storage."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    layers: list[Layer] = Field(default_factory=list, max_length=MAX_LAYERS)
    brightness: UnitFloat = 1.0


class Pattern(PatternBody):
    id: str
