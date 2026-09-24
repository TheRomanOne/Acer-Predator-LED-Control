import pytest
from pydantic import ValidationError

from led_studio.patterns.model import Color, Gradient, Layer, Pattern, Solid


def test_pattern_round_trips_through_json() -> None:
    pattern = Pattern(
        id="p1",
        name="Sunset",
        brightness=0.8,
        layers=[
            Layer(effect=Solid(color=Color(r=255, g=80, b=0))),
            Layer(
                effect=Gradient(
                    stops=[
                        Gradient.Stop(position=0, color=Color(r=0, g=0, b=0)),
                        Gradient.Stop(position=1, color=Color(r=0, g=0, b=255)),
                    ],
                    angle_deg=90,
                ),
                opacity=0.5,
                devices=["05af:667a:0"],
            ),
        ],
    )

    restored = Pattern.model_validate_json(pattern.model_dump_json())

    assert restored == pattern
    assert restored.layers[1].effect.type == "gradient"


def test_effect_type_is_a_discriminator() -> None:
    raw = {"id": "x", "name": "x", "layers": [{"effect": {"type": "no-such-effect"}}]}

    with pytest.raises(ValidationError, match="no-such-effect"):
        Pattern.model_validate(raw)


def test_gradient_requires_two_stops() -> None:
    with pytest.raises(ValidationError, match="2"):
        Gradient(stops=[Gradient.Stop(position=0, color=Color(r=1, g=1, b=1))])


def test_color_channels_are_bounded() -> None:
    with pytest.raises(ValidationError):
        Color(r=300, g=0, b=0)


def test_brightness_and_opacity_are_unit_interval() -> None:
    with pytest.raises(ValidationError):
        Pattern(id="x", name="x", layers=[], brightness=1.5)
    with pytest.raises(ValidationError):
        Layer(effect=Solid(color=Color(r=0, g=0, b=0)), opacity=-0.1)
