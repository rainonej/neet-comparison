"""Unit tests for Delhi state extraction helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "process_delhi_state", REPO / "scripts" / "process_delhi_state.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_nss_state_code_handles_lost_leading_zero() -> None:
    assert MODULE.nss_state_code("071") == 7
    assert MODULE.nss_state_code(71) == 7
    assert MODULE.nss_state_code(71.0) == 7
    assert MODULE.nss_state_code("072") == 7
    assert MODULE.nss_state_code("271") == 27
    assert MODULE.nss_state_code(None) is None


def test_weighted_summary_helpers() -> None:
    values = pd.Series([10.0, 20.0, 30.0])
    weights = pd.Series([1.0, 1.0, 2.0])
    assert MODULE.weighted_mean(values, weights) == pytest.approx(22.5)
    assert MODULE.weighted_share(np.array([False, True, True]), weights) == pytest.approx(0.75)
    quantiles = MODULE.weighted_quantiles(values, weights, quantiles=(0.5, 0.9))
    assert quantiles == {"p50": 20.0, "p90": 30.0}


def test_weighted_quintile_returns_ordered_bins() -> None:
    values = pd.Series([1, 2, 3, 4, 5], dtype=float)
    weights = pd.Series([1, 1, 1, 1, 1], dtype=float)
    bins = MODULE.weighted_quintile(values, weights)
    assert bins.tolist() == [1, 2, 3, 4, 5]
