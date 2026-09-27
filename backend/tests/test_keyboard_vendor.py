from led_studio.devices.keyboard_vendor import KeyboardVendorInterface, vendor_interface_for
from led_studio.hid.sunrex import MagKeyEffect, pack_magkey_effect
from led_studio.hid.transport import HidDeviceInfo
from tests.fakes import FakeVendorTransport, make_fake_zone

OFF_SEQUENCE = pack_magkey_effect(MagKeyEffect.OFF, brightness_pct=0, color=None)
TAKE, RELEASE = b"\x70\x00", b"\x70\x01"
STATIC = 0x01


def make_info(interface: int, usage_page: int, product_id: int = 0x667A) -> HidDeviceInfo:
    return HidDeviceInfo(
        path=f"path-{interface}".encode(),
        vendor_id=0x05AF,
        product_id=product_id,
        interface_number=interface,
        product="Keyboard",
        usage_page=usage_page,
    )


def make_vendor(transport: FakeVendorTransport) -> KeyboardVendorInterface:
    return KeyboardVendorInterface(transport, sleep=lambda _: None)


def test_disable_magkey_effect_sends_the_off_sequence_with_gaps_between_reports() -> None:
    transport = FakeVendorTransport()
    sleeps: list[float] = []
    vendor = KeyboardVendorInterface(transport, sleep=sleeps.append)

    vendor.disable_magkey_effect()

    assert transport.sent == OFF_SEQUENCE
    assert sleeps == [0.015, 0.015, 0.015]


def test_no_firmware_effect_while_the_keyboard_shows_host_updates() -> None:
    assert make_vendor(FakeVendorTransport()).firmware_effect() is None


def test_firmware_effect_reports_the_overriding_mode() -> None:
    assert make_vendor(FakeVendorTransport(mode=STATIC)).firmware_effect() == STATIC


def test_close_closes_the_vendor_transport() -> None:
    transport = FakeVendorTransport()

    make_vendor(transport).close()

    assert transport.closed


def test_vendor_interface_is_the_vendor_page_of_the_same_keyboard() -> None:
    keyboard = make_info(0, 0x59)
    vendor = make_info(3, 0xFF02)
    other_keyboard_vendor = make_info(3, 0xFF02, product_id=0x666A)
    infos = [make_info(1, 0xFF00), other_keyboard_vendor, keyboard, vendor]

    assert vendor_interface_for(keyboard, infos) is vendor


def test_no_vendor_interface_for_other_vendors() -> None:
    ring = HidDeviceInfo(
        path=b"ring",
        vendor_id=0x0D62,
        product_id=0xA20A,
        interface_number=1,
        product="Ring",
        usage_page=0x59,
    )
    unrelated = HidDeviceInfo(
        path=b"x",
        vendor_id=0x0D62,
        product_id=0xA20A,
        interface_number=0,
        product="Ring",
        usage_page=0xFF02,
    )

    assert vendor_interface_for(ring, [ring, unrelated]) is None


def test_zone_take_control_also_switches_the_magkey_zone_off() -> None:
    zone, transport = make_fake_zone()
    vendor = FakeVendorTransport()
    zone = zone.with_vendor(make_vendor(vendor))

    zone.take_control()
    zone.release_control()
    zone.close()

    assert transport.sent == [TAKE, RELEASE]
    assert vendor.sent == OFF_SEQUENCE
    assert transport.closed and vendor.closed


def test_zone_take_control_hands_over_from_a_firmware_effect_first() -> None:
    zone, transport = make_fake_zone()
    zone = zone.with_vendor(make_vendor(FakeVendorTransport(mode=STATIC)))

    zone.take_control()

    assert transport.sent == [RELEASE, TAKE]


def test_zone_without_vendor_interface_only_drives_the_lamparray() -> None:
    zone, transport = make_fake_zone()

    zone.take_control()
    zone.release_control()

    assert transport.sent == [TAKE, RELEASE]
