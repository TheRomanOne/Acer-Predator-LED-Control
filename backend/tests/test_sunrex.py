import pytest

from led_studio.hid.reports import Rgb
from led_studio.hid.sunrex import HOST_MODE, MagKeyEffect, pack_magkey_effect, unpack_active_mode

HEADER_1 = bytes([0x00, 0xB1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4E])
HEADER_2 = bytes([0x00, 0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF5])


def test_static_white_matches_the_decompiled_sequence() -> None:
    # Vector from the decompiled SunrexUSBKeyboard.dll (predator-sense magic_rgb.rs tests).
    reports = pack_magkey_effect(
        MagKeyEffect.STATIC, brightness_pct=100, color=Rgb(255, 255, 255), speed=4
    )

    assert reports[:2] == [HEADER_1, HEADER_2]
    assert reports[2] == bytes([0x00, 0x08, 0x02, 0x41, 0x06, 100, 0x00, 0x00, 0x4A])
    assert reports[3] == bytes([0x00, 0x14, 0x00, 0x01, 255, 255, 255, 0x00, 0xED])


def test_off_is_a_full_four_report_command_with_the_mag_flag_set() -> None:
    reports = pack_magkey_effect(MagKeyEffect.OFF, brightness_pct=0, color=Rgb(0, 0, 0))

    assert len(reports) == 4 and all(len(r) == 9 for r in reports)
    assert reports[2] == bytes([0x00, 0x08, 0x02, 0x40, 0x0A, 0x00, 0x00, 0x00, 0xAB])
    assert reports[3] == bytes([0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0xEA])


def test_brightness_and_speed_are_clamped_to_the_wire_range() -> None:
    reports = pack_magkey_effect(
        MagKeyEffect.STATIC, brightness_pct=250, color=Rgb(0, 0, 0), speed=99
    )

    assert reports[2][4] == 1  # speed 9 -> 10 - 9
    assert reports[2][5] == 100


def test_active_mode_is_byte_3_of_the_state_report() -> None:
    # Read from the PH16-73 keyboard while LED Studio was in control.
    assert unpack_active_mode(bytes.fromhex("00 88 00 33 03 32 00 00 00")) == HOST_MODE


def test_short_state_report_is_rejected() -> None:
    with pytest.raises(ValueError, match="state report"):
        unpack_active_mode(bytes([0x00, 0x88]))
