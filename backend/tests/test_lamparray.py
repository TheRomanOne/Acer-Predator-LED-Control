import pytest

from led_studio.devices.lamparray import LampArray
from led_studio.hid.reports import LampArrayKind, Rgb
from tests.fakes import FakeLampArrayTransport, make_array, make_lamp


def open_fake(lamp_count: int = 3) -> tuple[LampArray, FakeLampArrayTransport]:
    transport = FakeLampArrayTransport(
        array=make_array(lamp_count, kind=LampArrayKind.KEYBOARD),
        lamps=[make_lamp(i, x_um=i * 1000) for i in range(lamp_count)],
    )
    return LampArray.open(transport), transport


def test_open_reads_layout_from_device() -> None:
    array, transport = open_fake(lamp_count=3)

    assert array.lamp_count == 3
    assert array.kind == LampArrayKind.KEYBOARD
    assert [lamp.x_um for lamp in array.lamps] == [0, 1000, 2000]
    assert transport.get_requests[0] == (0x02, 23)
    assert (0x22, 29) in transport.get_requests
    assert transport.sent[:3] == [b"\x20\x00\x00", b"\x20\x01\x00", b"\x20\x02\x00"]


def test_fill_uses_one_range_update_over_all_lamps() -> None:
    array, transport = open_fake(lamp_count=3)
    transport.sent.clear()

    array.fill(Rgb(255, 0, 128))

    assert transport.sent == [bytes([0x60, 0x01, 0, 0, 2, 0, 255, 0, 128, 0xFF])]


def test_set_lamps_chunks_by_slot_count_and_flags_last_chunk() -> None:
    array, transport = open_fake(lamp_count=20)
    transport.sent.clear()

    array.set_lamps({i: Rgb(i, 0, 0) for i in range(10)})

    assert len(transport.sent) == 2
    first, second = transport.sent
    assert first[:3] == bytes([0x50, 8, 0])  # 8 lamps, not last
    assert second[:3] == bytes([0x50, 2, 1])  # 2 lamps, last
    assert second[3:7] == bytes([8, 0, 9, 0])


def test_set_lamps_with_nothing_to_do_sends_nothing() -> None:
    array, transport = open_fake()
    transport.sent.clear()

    array.set_lamps({})

    assert transport.sent == []


def test_set_lamps_rejects_unknown_lamp_id() -> None:
    array, _ = open_fake(lamp_count=3)

    with pytest.raises(ValueError, match="lamp 3"):
        array.set_lamps({3: Rgb(0, 0, 0)})


def test_take_and_release_control() -> None:
    array, transport = open_fake()
    transport.sent.clear()

    array.take_control()
    array.release_control()

    assert transport.sent == [b"\x70\x00", b"\x70\x01"]


def test_close_closes_transport() -> None:
    array, transport = open_fake()

    array.close()

    assert transport.closed
