"""A single HID LampArray (keyboard, light bar, logo, ...) addressed by lamp index."""

from collections.abc import Mapping

from led_studio.hid.descriptor import LampArrayReportIds, parse_lamparray_descriptor
from led_studio.hid.reports import (
    ARRAY_ATTRIBUTES_REPORT_SIZE,
    LAMP_ATTRIBUTES_REPORT_SIZE,
    LampArrayAttributes,
    LampAttributes,
    Rgb,
    pack_attributes_request,
    pack_control,
    pack_multi_update,
    pack_range_update,
    unpack_array_attributes,
    unpack_lamp_attributes,
)
from led_studio.hid.transport import HidTransport


class LampArray:
    def __init__(
        self,
        transport: HidTransport,
        report_ids: LampArrayReportIds,
        attributes: LampArrayAttributes,
        lamps: tuple[LampAttributes, ...],
    ) -> None:
        self._transport = transport
        self._ids = report_ids
        self.attributes = attributes
        self.lamps = lamps

    @classmethod
    def open(cls, transport: HidTransport) -> "LampArray":
        """Read the report layout and the full lamp geometry from the device."""
        ids = parse_lamparray_descriptor(transport.report_descriptor())
        attributes = unpack_array_attributes(
            transport.get_feature_report(ids.attributes, ARRAY_ATTRIBUTES_REPORT_SIZE),
            ids.attributes,
        )
        lamps = []
        for lamp_id in range(attributes.lamp_count):
            transport.send_feature_report(pack_attributes_request(ids.attributes_request, lamp_id))
            lamps.append(
                unpack_lamp_attributes(
                    transport.get_feature_report(
                        ids.attributes_response, LAMP_ATTRIBUTES_REPORT_SIZE
                    ),
                    ids.attributes_response,
                )
            )
        return cls(transport, ids, attributes, tuple(lamps))

    @property
    def lamp_count(self) -> int:
        return self.attributes.lamp_count

    @property
    def kind(self) -> int:
        return self.attributes.kind

    def take_control(self) -> None:
        """Stop the firmware's built-in effect so host updates are shown."""
        self._transport.send_feature_report(pack_control(self._ids.control, autonomous=False))

    def release_control(self) -> None:
        self._transport.send_feature_report(pack_control(self._ids.control, autonomous=True))

    def fill(self, color: Rgb) -> None:
        self._transport.send_feature_report(
            pack_range_update(
                self._ids.range_update, start=0, end=self.lamp_count - 1, color=color, last=True
            )
        )

    def set_lamps(self, colors: Mapping[int, Rgb]) -> None:
        """Update individual lamps; the frame is displayed once the last chunk arrives."""
        unknown = [lamp_id for lamp_id in colors if not 0 <= lamp_id < self.lamp_count]
        if unknown:
            raise ValueError(f"lamp {unknown[0]} does not exist (array has {self.lamp_count})")
        updates = list(colors.items())
        slots = self._ids.multi_update_slots
        for start in range(0, len(updates), slots):
            chunk = updates[start : start + slots]
            self._transport.send_feature_report(
                pack_multi_update(
                    self._ids.multi_update,
                    slots=slots,
                    updates=chunk,
                    last=start + slots >= len(updates),
                )
            )

    def close(self) -> None:
        self._transport.close()
