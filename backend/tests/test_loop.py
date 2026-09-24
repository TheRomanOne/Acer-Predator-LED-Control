import asyncio

import pytest

from led_studio.patterns.model import Layer, Pattern, Rainbow
from led_studio.playback.loop import PlaybackLoop
from led_studio.playback.player import Frame, Player
from tests.fakes import make_fake_zone


@pytest.mark.asyncio
async def test_loop_pushes_frames_at_the_requested_rate_and_notifies_listeners() -> None:
    zone, transport = make_fake_zone(lamp_count=4)
    player = Player([zone])
    received: list[Frame] = []
    loop = PlaybackLoop(player, fps=100, on_frame=received.append)
    player.play(Pattern(id="p", name="p", layers=[Layer(effect=Rainbow(speed=5.0))]))

    task = asyncio.create_task(loop.run())
    await asyncio.sleep(0.15)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert 5 <= len(received) <= 20
    assert any(r[0] == 0x50 for r in transport.sent)


@pytest.mark.asyncio
async def test_loop_periodically_reasserts_control_against_competing_software() -> None:
    zone, transport = make_fake_zone(lamp_count=2)
    player = Player([zone])
    loop = PlaybackLoop(player, fps=100, on_frame=lambda f: None, reassert_control_s=0.03)
    player.play(Pattern(id="p", name="p", layers=[Layer(effect=Rainbow(speed=0.0))]))
    transport.sent.clear()

    task = asyncio.create_task(loop.run())
    await asyncio.sleep(0.15)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    control_writes = [r for r in transport.sent if r == b"\x70\x00"]
    assert 2 <= len(control_writes) <= 6
    # a static pattern is still repainted after each re-assert
    assert len([r for r in transport.sent if r[0] == 0x50]) >= len(control_writes)


@pytest.mark.asyncio
async def test_loop_is_idle_when_nothing_is_playing() -> None:
    zone, transport = make_fake_zone()
    loop = PlaybackLoop(Player([zone]), fps=100, on_frame=lambda f: None)

    task = asyncio.create_task(loop.run())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert transport.sent == []


@pytest.mark.asyncio
async def test_a_failing_zone_does_not_kill_the_loop() -> None:
    good, good_transport = make_fake_zone("good")
    bad, bad_transport = make_fake_zone("bad")

    def explode(report: bytes) -> None:
        raise OSError("device unplugged")

    player = Player([good, bad])
    loop = PlaybackLoop(player, fps=100, on_frame=lambda f: None)
    player.play(Pattern(id="p", name="p", layers=[Layer(effect=Rainbow(speed=5.0))]))
    bad_transport.send_feature_report = explode  # type: ignore[method-assign]  # unplug mid-run

    task = asyncio.create_task(loop.run())
    await asyncio.sleep(0.1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert len([r for r in good_transport.sent if r[0] == 0x50]) > 1
