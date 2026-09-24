"""Asyncio ticker that renders on the event loop and pushes zones to hardware in parallel."""

import asyncio
import logging
import time
from collections.abc import Callable

from led_studio.hid.reports import Rgb
from led_studio.playback.player import Frame, Player

log = logging.getLogger(__name__)

_IDLE_POLL_S = 0.05
# The vendor lighting service can silently switch a zone back to its own effect; retaking
# control this often keeps the outage short and costs one full repaint per interval.
DEFAULT_REASSERT_CONTROL_S = 1.0


class PlaybackLoop:
    def __init__(
        self,
        player: Player,
        fps: int,
        on_frame: Callable[[Frame], None],
        reassert_control_s: float = DEFAULT_REASSERT_CONTROL_S,
    ) -> None:
        self._player = player
        self._interval = 1.0 / fps
        self._on_frame = on_frame
        self._reassert_interval = reassert_control_s
        self._last_reassert = time.monotonic()

    async def run(self) -> None:
        while True:
            if self._player.current is None:
                await asyncio.sleep(_IDLE_POLL_S)
                continue
            started = time.monotonic()
            if started - self._last_reassert >= self._reassert_interval:
                await asyncio.to_thread(self._player.reassert_control)
                self._last_reassert = started
            frame = self._player.render()
            await asyncio.gather(
                *(self._push(zone_id, colors) for zone_id, colors in frame.items())
            )
            self._on_frame(frame)
            await asyncio.sleep(max(0.0, self._interval - (time.monotonic() - started)))

    async def _push(self, zone_id: str, colors: list[Rgb]) -> None:
        # Each zone is its own HID handle, so the (blocking) USB writes overlap across zones.
        try:
            await asyncio.to_thread(self._player.push, zone_id, colors)
        except OSError:
            log.exception("zone %s rejected a frame; continuing", zone_id)
