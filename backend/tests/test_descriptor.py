import pytest

from led_studio.hid.descriptor import LampArrayReportIds, parse_lamparray_descriptor


def _item(prefix: int, *data: int) -> bytes:
    return bytes([prefix, *data])


# A minimal but realistic LampArray application collection, following HUT 1.5 §25.
# Report IDs and the 8-slot multi-update mirror what the Sunrex keyboard exposes.
LAMPARRAY_DESCRIPTOR = b"".join(
    [
        _item(0x05, 0x59),  # Usage Page (Lighting And Illumination)
        _item(0x09, 0x01),  # Usage (LampArray)
        _item(0xA1, 0x01),  # Collection (Application)
        # --- LampArrayAttributesReport (feature, id 2) ---
        _item(0x85, 0x02),  # Report ID (2)
        _item(0x09, 0x02),  # Usage (LampArrayAttributesReport)
        _item(0xA1, 0x02),  # Collection (Logical)
        _item(0x09, 0x03),  # Usage (LampCount)
        _item(0x75, 0x10),  # Report Size (16)
        _item(0x95, 0x01),  # Report Count (1)
        _item(0xB1, 0x03),  # Feature
        _item(0x09, 0x04),  # Usage (BoundingBoxWidthInMicrometers)
        _item(0x09, 0x05),
        _item(0x09, 0x06),
        _item(0x09, 0x07),  # Usage (LampArrayKind)
        _item(0x09, 0x08),  # Usage (MinUpdateIntervalInMicroseconds)
        _item(0x75, 0x20),  # Report Size (32)
        _item(0x95, 0x05),  # Report Count (5)
        _item(0xB1, 0x03),
        _item(0xC0),
        # --- LampAttributesRequestReport (feature, id 0x20) ---
        _item(0x85, 0x20),
        _item(0x09, 0x20),
        _item(0xA1, 0x02),
        _item(0x09, 0x21),  # Usage (LampId)
        _item(0x75, 0x10),
        _item(0x95, 0x01),
        _item(0xB1, 0x02),
        _item(0xC0),
        # --- LampAttributesResponseReport (feature, id 0x22) ---
        _item(0x85, 0x22),
        _item(0x09, 0x22),
        _item(0xA1, 0x02),
        _item(0x09, 0x21),
        _item(0x75, 0x10),
        _item(0x95, 0x01),
        _item(0xB1, 0x03),
        _item(0xC0),
        # --- LampMultiUpdateReport (feature, id 0x50, 8 slots) ---
        _item(0x85, 0x50),
        _item(0x09, 0x50),
        _item(0xA1, 0x02),
        _item(0x09, 0x55),  # Usage (LampCount)
        _item(0x09, 0x51),  # Usage (LampUpdateFlags)
        _item(0x75, 0x08),
        _item(0x95, 0x02),
        _item(0xB1, 0x02),
        _item(0x09, 0x21),  # Usage (LampId) x8
        _item(0x75, 0x10),
        _item(0x95, 0x08),
        _item(0xB1, 0x02),
        _item(0x09, 0x52),  # Usage (RedUpdateChannel)
        _item(0x75, 0x08),
        _item(0x95, 0x20),
        _item(0xB1, 0x02),
        _item(0xC0),
        # --- LampRangeUpdateReport (feature, id 0x60) ---
        _item(0x85, 0x60),
        _item(0x09, 0x60),
        _item(0xA1, 0x02),
        _item(0x09, 0x51),
        _item(0x75, 0x08),
        _item(0x95, 0x01),
        _item(0xB1, 0x02),
        _item(0xC0),
        # --- LampArrayControlReport (feature, id 0x70) ---
        _item(0x85, 0x70),
        _item(0x09, 0x70),
        _item(0xA1, 0x02),
        _item(0x09, 0x71),  # Usage (AutonomousMode)
        _item(0x75, 0x08),
        _item(0x95, 0x01),
        _item(0xB1, 0x02),
        _item(0xC0),
        _item(0xC0),  # End Collection (Application)
    ]
)


def test_parses_all_report_ids_and_multi_update_slots() -> None:
    ids = parse_lamparray_descriptor(LAMPARRAY_DESCRIPTOR)

    assert ids == LampArrayReportIds(
        attributes=0x02,
        attributes_request=0x20,
        attributes_response=0x22,
        multi_update=0x50,
        range_update=0x60,
        control=0x70,
        multi_update_slots=8,
    )


def test_descriptor_without_lamparray_collection_is_rejected() -> None:
    keyboard_only = b"".join(
        [
            _item(0x05, 0x01),  # Usage Page (Generic Desktop)
            _item(0x09, 0x06),  # Usage (Keyboard)
            _item(0xA1, 0x01),
            _item(0xC0),
        ]
    )
    with pytest.raises(ValueError, match="LampArray"):
        parse_lamparray_descriptor(keyboard_only)


def test_missing_required_report_is_reported_by_name() -> None:
    control_start = LAMPARRAY_DESCRIPTOR.rfind(_item(0x85, 0x70))
    without_control = LAMPARRAY_DESCRIPTOR[:control_start] + _item(0xC0)

    with pytest.raises(ValueError, match="LampArrayControlReport"):
        parse_lamparray_descriptor(without_control)


def test_extended_32bit_usage_items_are_understood() -> None:
    # Some firmware encodes usages as (page << 16 | usage) with a 4-byte usage item.
    extended = LAMPARRAY_DESCRIPTOR.replace(_item(0x09, 0x70), _item(0x0B, 0x70, 0x00, 0x59, 0x00))

    assert parse_lamparray_descriptor(extended).control == 0x70
