from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from led_studio.api.app import create_app
from led_studio.patterns.model import PatternBody
from led_studio.storage.patterns import PatternStore
from tests.fakes import FakeLampArrayTransport, make_fake_zone

SOLID_RED = {
    "name": "Red",
    "layers": [{"effect": {"type": "solid", "color": {"r": 255, "g": 0, "b": 0}}}],
}


@pytest.fixture
def transports() -> dict[str, FakeLampArrayTransport]:
    return {}


@pytest.fixture
def store(tmp_path: Path) -> PatternStore:
    return PatternStore(tmp_path)


@pytest.fixture
def client(
    store: PatternStore, transports: dict[str, FakeLampArrayTransport]
) -> Iterator[TestClient]:
    keyboard, kb_transport = make_fake_zone("05af:667a:0", "Keyboard", lamp_count=4, kind=1)
    ring, ring_transport = make_fake_zone("0d62:a20a:1", "InfiniteRing", lamp_count=2, kind=7)
    transports.update({"kb": kb_transport, "ring": ring_transport})
    app = create_app(zones=[keyboard, ring], store=store, fps=100)
    with TestClient(app) as client:
        yield client


def test_devices_expose_layout_and_key_bindings(client: TestClient) -> None:
    devices = client.get("/api/devices").json()

    assert [d["id"] for d in devices] == ["05af:667a:0", "0d62:a20a:1"]
    keyboard = devices[0]
    assert keyboard["name"] == "Keyboard"
    assert keyboard["kind"] == "keyboard"
    assert keyboard["lamp_count"] == 4
    assert keyboard["lamps"][1] == {"id": 1, "x": pytest.approx(1000 / 340000), "y": 0.0, "key": 0}


def test_pattern_crud(client: TestClient) -> None:
    created = client.post("/api/patterns", json=SOLID_RED)
    assert created.status_code == 201
    pattern = created.json()
    assert pattern["name"] == "Red" and pattern["id"]

    assert [p["id"] for p in client.get("/api/patterns").json()] == [pattern["id"]]

    updated = client.put(f"/api/patterns/{pattern['id']}", json={**SOLID_RED, "name": "Crimson"})
    assert updated.status_code == 200 and updated.json()["name"] == "Crimson"

    assert client.delete(f"/api/patterns/{pattern['id']}").status_code == 204
    assert client.get(f"/api/patterns/{pattern['id']}").status_code == 404


def test_invalid_pattern_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/patterns", json={"name": "x", "layers": [{"effect": {"type": "nope"}}]}
    )

    assert response.status_code == 422


def test_apply_pattern_drives_hardware_and_reports_state(
    client: TestClient, transports: dict[str, FakeLampArrayTransport]
) -> None:
    pattern_id = client.post("/api/patterns", json=SOLID_RED).json()["id"]

    assert client.post("/api/playback/apply", json={"pattern_id": pattern_id}).status_code == 200

    state = client.get("/api/playback").json()
    assert state == {"pattern_id": pattern_id, "preview": False}
    assert transports["kb"].sent[0] == b"\x70\x00"
    assert transports["ring"].sent[0] == b"\x70\x00"


def test_apply_unknown_pattern_is_404(client: TestClient) -> None:
    assert client.post("/api/playback/apply", json={"pattern_id": "missing"}).status_code == 404


def test_preview_plays_an_unsaved_pattern(client: TestClient) -> None:
    assert client.post("/api/playback/preview", json=SOLID_RED).status_code == 200

    assert client.get("/api/playback").json() == {"pattern_id": None, "preview": True}


def test_stop_releases_hardware(
    client: TestClient, transports: dict[str, FakeLampArrayTransport]
) -> None:
    client.post("/api/playback/preview", json=SOLID_RED)

    assert client.post("/api/playback/stop").status_code == 200

    assert client.get("/api/playback").json() == {"pattern_id": None, "preview": False}
    assert transports["kb"].sent[-1] == b"\x70\x01"


def test_deleting_the_active_pattern_stops_playback(client: TestClient) -> None:
    pattern_id = client.post("/api/patterns", json=SOLID_RED).json()["id"]
    client.post("/api/playback/apply", json={"pattern_id": pattern_id})

    client.delete(f"/api/patterns/{pattern_id}")

    assert client.get("/api/playback").json()["pattern_id"] is None


def test_active_pattern_is_restored_on_startup(
    store: PatternStore, transports: dict[str, FakeLampArrayTransport]
) -> None:
    pattern = store.create(PatternBody.model_validate(SOLID_RED))
    store.set_active_pattern_id(pattern.id)
    zone, transport = make_fake_zone()

    with TestClient(create_app(zones=[zone], store=store, fps=100)) as client:
        assert client.get("/api/playback").json()["pattern_id"] == pattern.id
        assert transport.sent[0] == b"\x70\x00"


def test_frames_are_streamed_over_websocket(client: TestClient) -> None:
    client.post("/api/playback/preview", json=SOLID_RED)

    with client.websocket_connect("/api/ws/frames") as ws:
        frame = ws.receive_json()

    assert frame["05af:667a:0"] == [[255, 0, 0]] * 4
    assert frame["0d62:a20a:1"] == [[255, 0, 0]] * 2
