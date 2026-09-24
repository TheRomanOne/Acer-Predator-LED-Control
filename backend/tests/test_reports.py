import pytest

from led_studio.hid.reports import (
    LampArrayAttributes,
    LampArrayKind,
    LampAttributes,
    LampPurpose,
    Rgb,
    pack_attributes_request,
    pack_control,
    pack_multi_update,
    pack_range_update,
    unpack_array_attributes,
    unpack_lamp_attributes,
)

# Report payloads as they come back from hidapi: report ID first, then little-endian fields.


def test_unpack_array_attributes() -> None:
    payload = bytes([0x02]) + (
        (103).to_bytes(2, "little")
        + (339450).to_bytes(4, "little")
        + (104950).to_bytes(4, "little")
        + (0).to_bytes(4, "little")
        + (1).to_bytes(4, "little")
        + (33000).to_bytes(4, "little")
    )

    assert unpack_array_attributes(payload, report_id=0x02) == LampArrayAttributes(
        lamp_count=103,
        width_um=339450,
        height_um=104950,
        depth_um=0,
        kind=LampArrayKind.KEYBOARD,
        min_update_interval_us=33000,
    )


def test_unknown_kind_is_preserved_not_rejected() -> None:
    unknown_kind = (99).to_bytes(4, "little")
    payload = bytes([0x02]) + (7).to_bytes(2, "little") + bytes(12) + unknown_kind + bytes(4)

    assert unpack_array_attributes(payload, report_id=0x02).kind == 99


def test_unpack_lamp_attributes() -> None:
    payload = bytes([0x22]) + (
        (5).to_bytes(2, "little")
        + (94725).to_bytes(4, "little")
        + (5250).to_bytes(4, "little")
        + (0).to_bytes(4, "little")
        + (5000).to_bytes(4, "little")
        + (LampPurpose.CONTROL | LampPurpose.ACCENT).to_bytes(4, "little")
        + bytes([255, 255, 255, 1, 1, 0x1E])
    )

    assert unpack_lamp_attributes(payload, report_id=0x22) == LampAttributes(
        lamp_id=5,
        x_um=94725,
        y_um=5250,
        z_um=0,
        update_latency_us=5000,
        purposes=LampPurpose.CONTROL | LampPurpose.ACCENT,
        red_levels=255,
        green_levels=255,
        blue_levels=255,
        intensity_levels=1,
        is_programmable=True,
        input_binding=0x1E,
    )


def test_unpack_rejects_wrong_report_id() -> None:
    with pytest.raises(ValueError, match="report ID"):
        unpack_array_attributes(bytes([0x05]) + bytes(22), report_id=0x02)


def test_unpack_rejects_short_payload() -> None:
    with pytest.raises(ValueError, match="short"):
        unpack_lamp_attributes(bytes([0x22]) + bytes(10), report_id=0x22)


def test_pack_attributes_request() -> None:
    assert pack_attributes_request(0x20, lamp_id=0x0102) == bytes([0x20, 0x02, 0x01])


def test_pack_control() -> None:
    assert pack_control(0x70, autonomous=False) == bytes([0x70, 0x00])
    assert pack_control(0x70, autonomous=True) == bytes([0x70, 0x01])


def test_pack_range_update() -> None:
    report = pack_range_update(0x60, start=0, end=102, color=Rgb(10, 20, 30), last=True)

    assert report == bytes([0x60, 0x01, 0x00, 0x00, 0x66, 0x00, 10, 20, 30, 0xFF])


def test_pack_multi_update_fills_unused_slots_with_zeros() -> None:
    report = pack_multi_update(
        0x50,
        slots=4,
        updates=[(3, Rgb(1, 2, 3)), (7, Rgb(4, 5, 6))],
        last=False,
    )

    ids = bytes([3, 0, 7, 0, 0, 0, 0, 0])
    colors = bytes([1, 2, 3, 0xFF, 4, 5, 6, 0xFF]) + bytes(8)
    assert report == bytes([0x50, 2, 0x00]) + ids + colors


def test_pack_multi_update_rejects_too_many_updates() -> None:
    with pytest.raises(ValueError, match="slots"):
        pack_multi_update(0x50, slots=2, updates=[(0, Rgb(0, 0, 0))] * 3, last=True)


def test_rgb_validates_channel_range() -> None:
    with pytest.raises(ValueError):
        Rgb(256, 0, 0)
    with pytest.raises(ValueError):
        Rgb(0, -1, 0)
