"""Write attempt-continuation prior artifacts (sensitivity, not national estimates)."""

from __future__ import annotations

import argparse
from pathlib import Path

from neet_microsim.attempt_priors import write_attempt_prior_artifacts


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/bayesian"),
        help="Output directory",
    )
    p.add_argument(
        "--config",
        type=Path,
        default=Path("config/attempt_priors.yaml"),
        help="Prior config YAML",
    )
    args = p.parse_args()
    paths = write_attempt_prior_artifacts(out_dir=args.out, cfg_path=args.config)
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
