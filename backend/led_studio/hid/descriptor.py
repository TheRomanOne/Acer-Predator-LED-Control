"""Locate the LampArray feature reports inside a HID report descriptor.

Report IDs are assigned by firmware and differ between vendors (Sunrex keyboard vs Darfon
chassis controllers), so they are read from the descriptor instead of being hard-coded.
"""

from collections.abc import Iterator
from dataclasses import dataclass

LIGHTING_USAGE_PAGE = 0x59

_USAGE_LAMP_ARRAY = 0x01
_USAGE_LAMP_ID = 0x21
_REPORT_USAGES = {
    0x02: "attributes",
    0x20: "attributes_request",
    0x22: "attributes_response",
    0x50: "multi_update",
    0x60: "range_update",
    0x70: "control",
}
_REPORT_NAMES = {
    "attributes": "LampArrayAttributesReport",
    "attributes_request": "LampAttributesRequestReport",
    "attributes_response": "LampAttributesResponseReport",
    "multi_update": "LampMultiUpdateReport",
    "range_update": "LampRangeUpdateReport",
    "control": "LampArrayControlReport",
}

# Short item prefix decoding: bSize (bits 0-1), bType (bits 2-3), bTag (bits 4-7).
_TYPE_MAIN, _TYPE_GLOBAL, _TYPE_LOCAL = 0, 1, 2
_MAIN_FEATURE, _MAIN_COLLECTION, _MAIN_END_COLLECTION = 0xB, 0xA, 0xC
_GLOBAL_USAGE_PAGE, _GLOBAL_REPORT_ID, _GLOBAL_REPORT_COUNT = 0x0, 0x8, 0x9
_LOCAL_USAGE = 0x0
_LONG_ITEM_PREFIX = 0xFE


@dataclass(frozen=True, slots=True)
class LampArrayReportIds:
    attributes: int
    attributes_request: int
    attributes_response: int
    multi_update: int
    range_update: int
    control: int
    multi_update_slots: int


def parse_lamparray_descriptor(descriptor: bytes) -> LampArrayReportIds:
    found: dict[str, int] = {}
    multi_update_slots = 0
    saw_lamparray = False

    usage_page = 0
    report_id = 0
    report_count = 0
    pending_usages: list[tuple[int, int]] = []  # (page, usage) locals since the last main item
    current_report: str | None = None  # which LampArray report collection we are inside
    collection_depth = 0
    report_collection_depth: int | None = None

    for tag, item_type, data in _iter_short_items(descriptor):
        if item_type == _TYPE_GLOBAL:
            if tag == _GLOBAL_USAGE_PAGE:
                usage_page = data
            elif tag == _GLOBAL_REPORT_ID:
                report_id = data
            elif tag == _GLOBAL_REPORT_COUNT:
                report_count = data
            continue

        if item_type == _TYPE_LOCAL:
            if tag == _LOCAL_USAGE:
                pending_usages.append(_split_usage(data, usage_page))
            continue

        if item_type != _TYPE_MAIN:
            continue

        if tag == _MAIN_COLLECTION:
            collection_depth += 1
            lighting_usages = [u for page, u in pending_usages if page == LIGHTING_USAGE_PAGE]
            if _USAGE_LAMP_ARRAY in lighting_usages:
                saw_lamparray = True
            report_usage = next((u for u in lighting_usages if u in _REPORT_USAGES), None)
            if report_usage is not None and current_report is None:
                current_report = _REPORT_USAGES[report_usage]
                report_collection_depth = collection_depth
        elif tag == _MAIN_END_COLLECTION:
            if collection_depth == report_collection_depth:
                current_report = None
                report_collection_depth = None
            collection_depth -= 1
        elif tag == _MAIN_FEATURE and current_report is not None:
            found.setdefault(current_report, report_id)
            has_lamp_id = any(
                page == LIGHTING_USAGE_PAGE and u == _USAGE_LAMP_ID for page, u in pending_usages
            )
            if current_report == "multi_update" and has_lamp_id:
                multi_update_slots = report_count
        pending_usages.clear()

    if not saw_lamparray:
        raise ValueError("descriptor contains no LampArray application collection")
    missing = [_REPORT_NAMES[name] for name in _REPORT_NAMES if name not in found]
    if missing:
        raise ValueError(f"LampArray descriptor is missing {', '.join(missing)}")
    if multi_update_slots == 0:
        raise ValueError("LampMultiUpdateReport declares no LampId slots")

    return LampArrayReportIds(**found, multi_update_slots=multi_update_slots)


def _split_usage(data: int, usage_page: int) -> tuple[int, int]:
    """A 32-bit usage item carries its own page in the upper 16 bits."""
    if data > 0xFFFF:
        return data >> 16, data & 0xFFFF
    return usage_page, data


def _iter_short_items(descriptor: bytes) -> Iterator[tuple[int, int, int]]:
    index = 0
    while index < len(descriptor):
        prefix = descriptor[index]
        index += 1
        if prefix == _LONG_ITEM_PREFIX:
            if index >= len(descriptor):
                raise ValueError("truncated long item in report descriptor")
            index += 2 + descriptor[index]
            continue
        size = prefix & 0x03
        if size == 3:
            size = 4
        item_type = (prefix >> 2) & 0x03
        tag = prefix >> 4
        data_bytes = descriptor[index : index + size]
        if len(data_bytes) != size:
            raise ValueError("truncated item in report descriptor")
        index += size
        yield tag, item_type, int.from_bytes(data_bytes, "little")
