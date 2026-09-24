"""FastAPI application. Hardware and storage are injected so tests run against fakes."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Iterator, Sequence

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status

from led_studio.api.schemas import (
    ApplyIn,
    DeviceOut,
    FrameOut,
    PlaybackOut,
    StatusOut,
    ZoneHealthOut,
    frame_out,
)
from led_studio.devices.zone import Zone
from led_studio.patterns.model import Pattern, PatternBody
from led_studio.playback.loop import PlaybackLoop
from led_studio.playback.player import Frame, Player
from led_studio.storage.patterns import PatternNotFound, PatternStore

log = logging.getLogger(__name__)

PREVIEW_ID = "preview"  # id of the unsaved pattern being edited live


class FrameBroadcaster:
    """Fan-out of rendered frames to WebSocket clients; slow clients only ever see the latest."""

    def __init__(self) -> None:
        self._queues: set[asyncio.Queue[FrameOut]] = set()

    def publish(self, frame: Frame) -> None:
        wire = frame_out(frame)
        for queue in self._queues:
            with contextlib.suppress(asyncio.QueueEmpty):
                queue.get_nowait()  # drop the stale frame
            queue.put_nowait(wire)

    @contextlib.contextmanager
    def subscribe(self) -> Iterator[asyncio.Queue[FrameOut]]:
        queue: asyncio.Queue[FrameOut] = asyncio.Queue(maxsize=1)
        self._queues.add(queue)
        try:
            yield queue
        finally:
            self._queues.discard(queue)


def create_app(zones: Sequence[Zone], store: PatternStore, fps: int) -> FastAPI:
    player = Player(zones)
    broadcaster = FrameBroadcaster()
    loop = PlaybackLoop(player, fps, broadcaster.publish)

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        _restore_active_pattern(player, store)
        task = asyncio.create_task(loop.run())
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            player.close()

    app = FastAPI(title="LED Studio", lifespan=lifespan)

    @app.get("/api/devices")
    def list_devices() -> list[DeviceOut]:
        return [DeviceOut.from_zone(zone) for zone in player.zones]

    @app.get("/api/patterns")
    def list_patterns() -> list[Pattern]:
        return store.list()

    @app.post("/api/patterns", status_code=status.HTTP_201_CREATED)
    def create_pattern(body: PatternBody) -> Pattern:
        return store.create(body)

    @app.get("/api/patterns/{pattern_id}")
    def get_pattern(pattern_id: str) -> Pattern:
        return _get_or_404(store, pattern_id)

    @app.put("/api/patterns/{pattern_id}")
    def update_pattern(pattern_id: str, body: PatternBody) -> Pattern:
        _get_or_404(store, pattern_id)
        pattern = store.update(pattern_id, body)
        if player.current is not None and player.current.id == pattern_id:
            player.play(pattern)
        return pattern

    @app.delete("/api/patterns/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_pattern(pattern_id: str) -> None:
        _get_or_404(store, pattern_id)
        if player.current is not None and player.current.id == pattern_id:
            _stop(player, store)
        store.delete(pattern_id)

    @app.get("/api/playback")
    def get_playback() -> PlaybackOut:
        return _playback_out(player)

    @app.get("/api/status")
    def get_status() -> StatusOut:
        return StatusOut(
            playback=_playback_out(player),
            fps=round(loop.measured_fps, 1),
            zones=[
                ZoneHealthOut(id=zone_id, **vars(health))
                for zone_id, health in player.health.items()
            ],
        )

    @app.post("/api/playback/apply")
    def apply_pattern(body: ApplyIn) -> PlaybackOut:
        player.play(_get_or_404(store, body.pattern_id))
        store.set_active_pattern_id(body.pattern_id)
        return _playback_out(player)

    @app.post("/api/playback/preview")
    def preview_pattern(body: PatternBody) -> PlaybackOut:
        player.play(Pattern(id=PREVIEW_ID, **body.model_dump()))
        return _playback_out(player)

    @app.post("/api/playback/stop")
    def stop_playback() -> PlaybackOut:
        _stop(player, store)
        return _playback_out(player)

    @app.websocket("/api/ws/frames")
    async def stream_frames(websocket: WebSocket) -> None:
        await websocket.accept()
        with broadcaster.subscribe() as queue:
            try:
                while True:
                    await websocket.send_json(await queue.get())
            except WebSocketDisconnect:
                pass

    return app


def _restore_active_pattern(player: Player, store: PatternStore) -> None:
    active = store.active_pattern_id()
    if active is None:
        return
    try:
        player.play(store.get(active))
    except (PatternNotFound, ValueError):
        log.warning("active pattern %s could not be restored", active)
        store.set_active_pattern_id(None)


def _stop(player: Player, store: PatternStore) -> None:
    player.stop()
    store.set_active_pattern_id(None)


def _playback_out(player: Player) -> PlaybackOut:
    current = player.current
    if current is None:
        return PlaybackOut(pattern_id=None, preview=False)
    is_preview = current.id == PREVIEW_ID
    return PlaybackOut(pattern_id=None if is_preview else current.id, preview=is_preview)


def _get_or_404(store: PatternStore, pattern_id: str) -> Pattern:
    try:
        return store.get(pattern_id)
    except PatternNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"pattern {pattern_id} not found") from exc
