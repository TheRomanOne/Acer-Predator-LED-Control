from led_studio.devices.lamparray import LampArray
from led_studio.hid.reports import LampArrayKind, Rgb
from led_studio.patterns.layout import DeviceLayout, Lamp
from led_studio.patterns.model import Color, Layer, Paint, Pattern, Solid
from led_studio.playback.player import Player, Zone
from tests.fakes import FakeLampArrayTransport, make_array, make_lamp

RED = Rgb(255, 0, 0)
RED_COLOR = Color(r=255, g=0, b=0)


def make_zone(zone_id: str = "z", lamp_count: int = 3) -> tuple[Zone, FakeLampArrayTransport]:
    transport = FakeLampArrayTransport(
        array=make_array(lamp_count, kind=LampArrayKind.CHASSIS),
        lamps=[make_lamp(i) for i in range(lamp_count)],
    )
    array = LampArray.open(transport)
    layout = DeviceLayout(id=zone_id, lamps=tuple(Lamp(i, i / 2, 0.5) for i in range(lamp_count)))
    transport.sent.clear()
    return Zone(id=zone_id, name="Fake", array=array, layout=layout), transport


def solid(color: Color = RED_COLOR) -> Pattern:
    return Pattern(id="p", name="p", layers=[Layer(effect=Solid(color=color))])


def test_play_takes_control_and_stop_releases_it() -> None:
    zone, transport = make_zone()
    player = Player([zone])

    player.play(solid())
    player.stop()

    assert transport.sent[0] == b"\x70\x00"
    assert transport.sent[-1] == b"\x70\x01"
    assert player.current is None


def test_uniform_frame_is_sent_as_a_single_fill() -> None:
    zone, transport = make_zone(lamp_count=3)
    player = Player([zone])
    player.play(solid())

    player.render_and_push(t=0.0)

    fills = [r for r in transport.sent if r[0] == 0x60]
    assert len(fills) == 1 and fills[0][6:9] == bytes([255, 0, 0])
    assert not any(r[0] == 0x50 for r in transport.sent)


def test_unchanged_frame_sends_nothing() -> None:
    zone, transport = make_zone()
    player = Player([zone])
    player.play(solid())
    player.render_and_push(t=0.0)
    transport.sent.clear()

    player.render_and_push(t=0.1)

    assert transport.sent == []


def test_only_changed_lamps_are_sent_after_the_first_frame() -> None:
    zone, transport = make_zone(lamp_count=3)
    player = Player([zone])
    player.play(solid())
    player.render_and_push(t=0.0)
    transport.sent.clear()

    player.play(
        Pattern(
            id="p2",
            name="p2",
            layers=[
                Layer(effect=Solid(color=Color(r=255, g=0, b=0))),
                Layer(effect=Paint(colors={1: Color(r=0, g=0, b=255)})),
            ],
        )
    )
    player.render_and_push(t=0.0)

    multi = [r for r in transport.sent if r[0] == 0x50]
    assert len(multi) == 1
    assert multi[0][1] == 1  # one lamp in the update
    assert multi[0][3:5] == bytes([1, 0])  # lamp id 1


def test_switching_pattern_repaints_zones_with_the_new_colours() -> None:
    zone, transport = make_zone()
    player = Player([zone])
    player.play(solid())
    player.render_and_push(t=0.0)
    transport.sent.clear()

    player.play(solid(Color(r=0, g=255, b=0)))
    player.render_and_push(t=5.0)

    assert any(r[0] == 0x60 and r[6:9] == bytes([0, 255, 0]) for r in transport.sent)


def test_stop_blanks_the_zones_before_releasing() -> None:
    zone, transport = make_zone()
    player = Player([zone])
    player.play(solid())
    player.render_and_push(t=0.0)
    transport.sent.clear()

    player.stop()

    assert transport.sent[0][0] == 0x60 and transport.sent[0][6:9] == bytes(3)
    assert transport.sent[-1] == b"\x70\x01"


def test_reassert_control_retakes_zones_and_forces_a_full_repaint() -> None:
    zone, transport = make_zone(lamp_count=3)
    player = Player([zone])
    player.play(solid())
    player.render_and_push(t=0.0)
    transport.sent.clear()

    player.reassert_control()
    player.render_and_push(t=0.1)

    assert transport.sent[0] == b"\x70\x00"
    assert any(r[0] == 0x60 and r[6:9] == bytes([255, 0, 0]) for r in transport.sent[1:])


def test_reassert_control_is_a_no_op_when_idle() -> None:
    zone, transport = make_zone()
    player = Player([zone])

    player.reassert_control()

    assert transport.sent == []


def test_frames_are_rendered_relative_to_play_start() -> None:
    zone, _ = make_zone()
    player = Player([zone], clock=lambda: 100.0)

    player.play(solid())

    assert player.elapsed() == 0.0


def test_last_frame_is_exposed_for_ui_preview() -> None:
    zone, _ = make_zone(lamp_count=2)
    player = Player([zone])
    player.play(solid())

    frame = player.render_and_push(t=0.0)

    assert frame == {"z": [RED, RED]}
    assert player.last_frame == frame


def test_play_and_reassert_switch_the_magkey_zone_off_each_time() -> None:
    from led_studio.devices.magkey import MagKeyController
    from led_studio.hid.sunrex import MagKeyEffect, pack_magkey_effect
    from tests.fakes import FakeVendorTransport

    zone, _ = make_zone()
    vendor = FakeVendorTransport()
    player = Player([zone.with_magkey(MagKeyController(vendor, sleep=lambda _: None))])
    off = pack_magkey_effect(MagKeyEffect.OFF, brightness_pct=0, color=None)

    player.play(solid())
    player.reassert_control()

    assert vendor.sent == off + off
