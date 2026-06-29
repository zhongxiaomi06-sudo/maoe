from __future__ import annotations

from pathlib import Path

from maoe.bootstrap import BootstrapLoader

ROOT = Path(__file__).resolve().parent.parent


def test_loader_records_all_seven_core_files() -> None:
    context = BootstrapLoader(ROOT).load()
    paths = {item.path for item in context.loaded_context}
    assert len(paths) == 7
    assert ".maoe/manifest.yaml" in paths
    assert all(len(item.sha256) == 64 for item in context.loaded_context)
