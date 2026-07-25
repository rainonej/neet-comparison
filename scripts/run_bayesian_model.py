#!/usr/bin/env python3
"""Fit the Bayesian evidence model under all prior profiles and write artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from neet_microsim.model import fit_all_profiles, run_bayesian_pipeline, scarcity_log_odds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed",
        type=Path,
        default=None,
        help="Override data/processed root",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: data/processed/bayesian)",
    )
    parser.add_argument("--draws", type=int, default=40_000)
    args = parser.parse_args()

    paths = run_bayesian_pipeline(
        processed=args.processed,
        output_dir=args.out,
        draws=args.draws,
    )
    fits = fit_all_profiles(processed=args.processed)
    print("Bayesian model artifacts:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    print()
    for fit in fits:
        scarcity = scarcity_log_odds(fit)
        print(
            f"[{fit.profile}] qualify={fit.qualify_rate.mean:.4f} "
            f"capacity={fit.mbbs_capacity_rate.mean:.5f} "
            f"appeared/seat={scarcity['appeared_per_mbbs_seat']:.1f} "
            f"TN eng/tam ratio={fit.medium_rate_ratio_post:.2f} "
            f"coaching prior mean SD={fit.coaching_score_shift.mean:.2f}"
        )


if __name__ == "__main__":
    main()
