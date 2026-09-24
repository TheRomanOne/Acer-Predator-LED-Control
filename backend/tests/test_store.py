from pathlib import Path

import pytest

from led_studio.patterns.model import Color, Layer, PatternBody, Solid
from led_studio.storage.patterns import PatternNotFound, PatternStore


def body(name: str = "Red") -> PatternBody:
    return PatternBody(name=name, layers=[Layer(effect=Solid(color=Color(r=255, g=0, b=0)))])


def test_create_assigns_unique_ids_and_persists_to_disk(tmp_path: Path) -> None:
    store = PatternStore(tmp_path)

    first = store.create(body("A"))
    second = store.create(body("B"))

    assert first.id != second.id
    assert (tmp_path / "patterns" / f"{first.id}.json").exists()
    assert PatternStore(tmp_path).get(first.id) == first


def test_list_is_sorted_by_name(tmp_path: Path) -> None:
    store = PatternStore(tmp_path)
    store.create(body("Zebra"))
    store.create(body("apple"))

    assert [p.name for p in store.list()] == ["apple", "Zebra"]


def test_update_replaces_body_and_keeps_id(tmp_path: Path) -> None:
    store = PatternStore(tmp_path)
    created = store.create(body("Old"))

    updated = store.update(created.id, body("New"))

    assert updated.id == created.id
    assert store.get(created.id).name == "New"


def test_delete_removes_pattern(tmp_path: Path) -> None:
    store = PatternStore(tmp_path)
    created = store.create(body())

    store.delete(created.id)

    with pytest.raises(PatternNotFound):
        store.get(created.id)
    with pytest.raises(PatternNotFound):
        store.delete(created.id)


def test_corrupt_file_is_reported_with_its_path(tmp_path: Path) -> None:
    store = PatternStore(tmp_path)
    created = store.create(body())
    (tmp_path / "patterns" / f"{created.id}.json").write_text("{not json")

    with pytest.raises(ValueError, match=created.id):
        store.get(created.id)


def test_active_pattern_id_round_trips(tmp_path: Path) -> None:
    store = PatternStore(tmp_path)
    assert store.active_pattern_id() is None

    store.set_active_pattern_id("abc")
    assert PatternStore(tmp_path).active_pattern_id() == "abc"

    store.set_active_pattern_id(None)
    assert store.active_pattern_id() is None
