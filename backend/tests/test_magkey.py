from led_studio.devices.magkey import MagKeyController, magkey_interface_for
from led_studio.hid.sunrex import MagKeyEffect, pack_magkey_effect
from led_studio.hid.transport import HidDeviceInfo
from tests.fakes import FakeVendorTransport, make_fake_zone

OFF_SEQUENCE = pack_magkey_effect(MagKeyEffect.OFF, brightness_pct=0, color=None)


def make_info(interface: int, usage_page: int, product_id: int = 0x667A) -> HidDeviceInfo:
    return HidDeviceInfo(
        path=f"path-{interface}".encode(),
        vendor_id=0x05AF,
        product_id=product_id,
        interface_number=interface,
        product="Keyboard",
        usage_page=usage_page,
    )


def test_disable_effect_sends_the_off_sequence_with_gaps_between_reports() -> None:
    transport = FakeVendorTransport()
    sleeps: list[float] = []
    controller = MagKeyController(transport, sleep=sleeps.append)

    controller.disable_effect()

    assert transport.sent == OFF_SEQUENCE
    assert sleeps == [0.015, 0.015, 0.015]


def test_close_closes_the_vendor_transport() -> None:
    transport = FakeVendorTransport()

    MagKeyController(transport, sleep=lambda _: None).close()

    assert transport.closed


def test_magkey_interface_is_the_vendor_page_of_the_same_keyboard() -> None:
    keyboard = make_info(0, 0x59)
    vendor = make_info(3, 0xFF02)
    other_keyboard_vendor = make_info(3, 0xFF02, product_id=0x666A)
    infos = [make_info(1, 0xFF00), other_keyboard_vendor, keyboard, vendor]

    assert magkey_interface_for(keyboard, infos) is vendor


def test_no_magkey_interface_for_other_vendors() -> None:
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

    assert magkey_interface_for(ring, [ring, unrelated]) is None


def test_zone_take_control_also_switches_the_magkey_zone_off() -> None:
    zone, transport = make_fake_zone()
    vendor = FakeVendorTransport()
    zone = zone.with_magkey(MagKeyController(vendor, sleep=lambda _: None))

    zone.take_control()
    zone.release_control()
    zone.close()

    assert transport.sent == [b"\x70\x00", b"\x70\x01"]
    assert vendor.sent == OFF_SEQUENCE
    assert transport.closed and vendor.closed


def test_zone_without_magkey_only_drives_the_lamparray() -> None:
    zone, transport = make_fake_zone()

    zone.take_control()
    zone.release_control()

    assert transport.sent == [b"\x70\x00", b"\x70\x01"]
