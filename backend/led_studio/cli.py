"""Developer CLI: list the LampArray zones and light them up for identification.

python -m led_studio.cli list
python -m led_studio.cli identify          # each zone in turn, distinct colour
python -m led_studio.cli fill <id> R G B   # e.g. fill 05af:667a:0 255 0 0
python -m led_studio.cli release           # hand control back to firmware
"""

import argparse
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from led_studio.devices.zone import Zone, open_zones
from led_studio.hid.reports import Rgb, kind_name

IDENTIFY_COLORS = [Rgb(255, 0, 0), Rgb(0, 255, 0), Rgb(0, 0, 255), Rgb(255, 255, 0)]


@contextmanager
def zones() -> Iterator[list[Zone]]:
    opened = open_zones()
    try:
        yield opened
    finally:
        for zone in opened:
            zone.array.close()


def describe(zone: Zone) -> str:
    a = zone.array.attributes
    return (
        f"{zone.id:<16} {zone.name:<14} {kind_name(a.kind):<9} {a.lamp_count:>3} lamps  "
        f"{a.width_um / 1000:.0f}x{a.height_um / 1000:.0f} mm"
    )


def cmd_list(_: argparse.Namespace) -> None:
    with zones() as opened:
        for zone in opened:
            print(describe(zone))


def cmd_identify(args: argparse.Namespace) -> None:
    with zones() as opened:
        for zone, color in zip(opened, IDENTIFY_COLORS, strict=False):
            print(f"{describe(zone)} -> {color}")
            zone.array.take_control()
            zone.array.fill(color)
            time.sleep(args.seconds)
    print("Done. Run `release` to give control back to the firmware.")


def cmd_fill(args: argparse.Namespace) -> None:
    with zones() as opened:
        zone = next((z for z in opened if z.id == args.device), None)
        if zone is None:
            sys.exit(f"no LampArray zone with id {args.device!r}; see `list`")
        zone.array.take_control()
        zone.array.fill(Rgb(args.red, args.green, args.blue))


def cmd_release(_: argparse.Namespace) -> None:
    with zones() as opened:
        for zone in opened:
            zone.array.release_control()


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
    run: Callable[[argparse.Namespace], None] = args.run
    run(args)


if __name__ == "__main__":
    main()
