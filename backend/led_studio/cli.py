"""Developer CLI: list the LampArray devices and light them up for identification.

python -m led_studio.cli list
python -m led_studio.cli identify          # each array in turn, distinct colour
python -m led_studio.cli fill <id> R G B   # e.g. fill 05af:667a:0 255 0 0
python -m led_studio.cli release           # hand control back to firmware
"""

import argparse
import sys
import time

from led_studio.devices.lamparray import LampArray
from led_studio.hid.reports import Rgb, kind_name
from led_studio.hid.transport import HidapiTransport, HidDeviceInfo, enumerate_lamparray_devices

IDENTIFY_COLORS = [Rgb(255, 0, 0), Rgb(0, 255, 0), Rgb(0, 0, 255), Rgb(255, 255, 0)]


def _open(info: HidDeviceInfo) -> LampArray:
    return LampArray.open(HidapiTransport(info))


def cmd_list(_: argparse.Namespace) -> None:
    for info in enumerate_lamparray_devices():
        array = _open(info)
        try:
            a = array.attributes
            print(
                f"{info.id:<16} {info.product:<12} {kind_name(a.kind):<9} "
                f"{a.lamp_count:>3} lamps  {a.width_um / 1000:.0f}x{a.height_um / 1000:.0f} mm"
            )
        finally:
            array.close()


def cmd_identify(args: argparse.Namespace) -> None:
    for info, color in zip(enumerate_lamparray_devices(), IDENTIFY_COLORS, strict=False):
        array = _open(info)
        try:
            print(f"{info.id} ({kind_name(array.kind)}, {array.lamp_count} lamps) -> {color}")
            array.take_control()
            array.fill(color)
            time.sleep(args.seconds)
        finally:
            array.close()
    print("Done. Run `release` to give control back to the firmware.")


def cmd_fill(args: argparse.Namespace) -> None:
    info = next((d for d in enumerate_lamparray_devices() if d.id == args.device), None)
    if info is None:
        sys.exit(f"no LampArray device with id {args.device!r}; see `list`")
    array = _open(info)
    try:
        array.take_control()
        array.fill(Rgb(args.red, args.green, args.blue))
    finally:
        array.close()


def cmd_release(_: argparse.Namespace) -> None:
    for info in enumerate_lamparray_devices():
        array = _open(info)
        try:
            array.release_control()
        finally:
            array.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="led_studio", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(run=cmd_list)
    identify = sub.add_parser("identify")
    identify.add_argument("--seconds", type=float, default=3.0)
    identify.set_defaults(run=cmd_identify)
    fill = sub.add_parser("fill")
    fill.add_argument("device")
    fill.add_argument("red", type=int)
    fill.add_argument("green", type=int)
    fill.add_argument("blue", type=int)
    fill.set_defaults(run=cmd_fill)
    sub.add_parser("release").set_defaults(run=cmd_release)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
