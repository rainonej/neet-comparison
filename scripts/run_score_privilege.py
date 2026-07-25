#!/usr/bin/env python3
"""Run the score → rank → seat privilege inequality story."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from neet_microsim.score_engine import load_score_config
from neet_microsim.score_privilege import run_score_privilege_pipeline

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO / "config" / "score_privilege_scenarios.yaml",
    )
    parser.add_argument("--processed", type=Path, default=REPO / "data" / "processed")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--draws", type=int, default=None)
    parser.add_argument("--coaching-profile", type=str, default=None)
    parser.add_argument(
        "--arms-race",
        nargs="*",
        default=None,
        help="Optional subset of arms-race scenario ids (default: all)",
    )
    args = parser.parse_args()

    paths = run_score_privilege_pipeline(
        config_path=args.config,
        processed=args.processed,
        output_dir=args.out,
        draws=args.draws,
        coaching_profile=args.coaching_profile,
        arms_race_ids=args.arms_race,
    )
    config = load_score_config(args.config)
    story = json.loads(paths["score_inequality_story"].read_text(encoding="utf-8"))
    decomp = story.get("decomposition_unilateral", {})
    print("Score-privilege artifacts:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    print(f"model_version: {config.get('model_version')}")
    print(f"coaching_profile: {story.get('coaching_profile')}")
    print(f"govt cutoff share: {story['capacity']['government_cutoff_percentile']:.4f}")
    print(f"any MBBS cutoff share: {story['capacity']['any_mbbs_cutoff_percentile']:.4f}")
    if decomp.get("full_ladder_ratio_top_over_low") is not None:
        print(f"unilateral access ladder ratio: {decomp['full_ladder_ratio_top_over_low']:.3f}")
        print(
            f"mean marks low->top: {decomp['mean_marks_low']:.1f} -> {decomp['mean_marks_top']:.1f}"
        )


if __name__ == "__main__":
    main()
