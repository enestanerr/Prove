from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
from hypothesis import settings

ROOT = Path(__file__).resolve().parent.parent
settings.register_profile("prove", deadline=None, max_examples=120)
settings.load_profile("prove")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """No test may touch the network. Source resolvers are tested against fixtures."""

    def refuse(*args, **kwargs):
        raise AssertionError("tests must not use the network")

    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def kestrel_doc() -> dict:
    from provecheck.ingest import ingest

    return ingest(ROOT / "examples" / "kestrel-q3" / "report.md")


@pytest.fixture(scope="session")
def kestrel_claims() -> dict:
    return json.loads(
        (ROOT / "examples" / "kestrel-q3" / "claims.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="session")
def reference_claims() -> dict:
    return json.loads((ROOT / "reference" / "claims.example.json").read_text(encoding="utf-8"))
