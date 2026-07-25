#!/usr/bin/env python3
"""Run the privilege-compounding inequality story and write artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from neet_microsim.privilege import affordability_only_ratio, load_privilege_config, run_privilege_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--processed", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--draws", type=int, default=None)
    parser.add_argument(
        "--admission-profile",
        default=None,
        help="baseline_neutral_prep (default) or prep_sensitivity",
    )
    args = parser.parse_args()

    paths = run_privilege_pipeline(
        config_path=args.config,
        processed=args.processed,
        output_dir=args.out,
        draws=args.draws,
        admission_profile=args.admission_profile,
    )
    config = load_privilege_config(args.config)
    story = json.loads(paths["inequality_story"].read_text(encoding="utf-8"))
    decomp = story["decomposition"]

    print("Privilege inequality artifacts:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    print()
    print(f"admission_profile: {story['admission_profile']}")
    print(f"primary_metric: {story.get('primary_metric')}")
    print(f"affordability-only access ratio (can/cannot): {affordability_only_ratio(config):.3f}")
    print(
        "access ladder low -> top: "
        f"{decomp['p_accessible_low']:.4f} -> {decomp['p_accessible_top']:.4f} "
        f"(ratio {decomp['full_ladder_ratio_top_over_low']:.2f}x)"
    )
    print(
        "govt - no-seat mean annual (incl zeros): "
        f"INR {decomp['within_stratum_government_minus_noseat_annual_mean']:,.0f}"
    )
    print(
        "govt - no-seat mean annual if employed: "
        f"INR {decomp['within_stratum_government_minus_noseat_annual_mean_if_employed']:,.0f}"
    )
    print(
        "govt / no-seat median annual if employed: "
        f"INR {decomp['government_annual_median_if_employed_mid']:,.0f} / "
        f"{decomp['no_seat_annual_median_if_employed_mid']:,.0f}"
    )


if __name__ == "__main__":
    main()
