"""Process entry point: open the hardware and serve the API.

python -m led_studio.main
"""

import logging

import uvicorn

from led_studio.api.app import create_app
from led_studio.config import Settings
from led_studio.devices.zone import open_zones
from led_studio.storage.patterns import PatternStore


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = Settings()
    zones = open_zones()
    for zone in zones:
        logging.info("zone %s: %s (%d lamps)", zone.id, zone.name, zone.array.lamp_count)
    app = create_app(zones=zones, store=PatternStore(settings.data_dir), fps=settings.fps)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
