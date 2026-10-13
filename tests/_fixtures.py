"""Shared test helpers for Lucky.Engine tests."""

import json
import os
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name):
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)


def bridge_path(name="bridge_nodes_fixture.json"):
    return FIXTURES / name


def graph_path(name="graph_minimal.json"):
    return FIXTURES / name


def make_temp_dir(name="tmp"):
    root = Path(FIXTURES.resolve().parent) / "_tmp" / name
    root.mkdir(parents=True, exist_ok=True)
    return root
