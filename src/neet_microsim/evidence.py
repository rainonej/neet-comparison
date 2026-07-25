"""Load citation-ready processed evidence used by the Bayesian model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = REPO_ROOT / "data" / "processed"


@dataclass(frozen=True)
class NationalExamCounts:
    appeared_excluding_ufm: int
    qualified: int
    nmc_mbbs_seats: int
    source_appeared: str
    source_qualified: str
    source_seats: str


@dataclass(frozen=True)
class MediumPeriodCounts:
    period: str
    english_applicants: int
    tamil_applicants: int
    english_government_allotments: int
    tamil_government_allotments: int


@dataclass(frozen=True)
class EmploymentBenchmark:
    id: str
    measure: str
    estimate: float
    suggested_prior_ess: float
    age_band: str
    source: str
    notes: str


@dataclass(frozen=True)
class WageAnchor:
    estimate_id: str
    monthly_inr: float
    source: str
    geometric_sd: float = 1.75
    # "median" for PLFS microdata medians; "mean" for World Bank published means.
    statistic: str = "mean"

    def annual_median_inr(self) -> float:
        """Annual earnings median for lognormal career paths (INR)."""
        monthly_median = (
            self.monthly_inr if self.statistic == "median" else self.monthly_inr / 1.15
        )
        return float(monthly_median * 12.0)


@dataclass(frozen=True)
class CoachingCohortOutcome:
    evidence_id: str
    program: str
    cohort_year: str
    outcome: str
    successes: int
    trials: int
    observed_rate: float
    selection_into_program: str
    evidence_role: str


@dataclass(frozen=True)
class AiqCourseCounts:
    mbbs: int
    bds: int
    nursing: int
    other: int
    total: int


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required evidence file missing: {path}")
    return path


def load_published_estimates(processed: Path | None = None) -> pd.DataFrame:
    root = PROCESSED if processed is None else processed
    return pd.read_csv(_require(root / "published_estimates.csv"))


def load_national_exam_counts(processed: Path | None = None) -> NationalExamCounts:
    estimates = load_published_estimates(processed)
    by_id = estimates.set_index("estimate_id")["value"].astype(float)

    def _get(estimate_id: str) -> tuple[int, str]:
        row = estimates.loc[estimates["estimate_id"] == estimate_id].iloc[0]
        return int(round(float(row["value"]))), str(row["source"])

    appeared, appeared_source = _get("neet_2024_appeared_including_ufm")
    # Prefer the reconstruction-reconciled appeared-excluding-UFM count for denominators.
    if "neet_2024_candidate_rows" in by_id.index:
        appeared, appeared_source = _get("neet_2024_candidate_rows")
    qualified, qualified_source = _get("neet_2024_qualified")
    seats, seats_source = _get("nmc_mbbs_seats_current_page")
    return NationalExamCounts(
        appeared_excluding_ufm=appeared,
        qualified=qualified,
        nmc_mbbs_seats=seats,
        source_appeared=appeared_source,
        source_qualified=qualified_source,
        source_seats=seats_source,
    )


def load_medium_aggregate_rates(processed: Path | None = None) -> list[MediumPeriodCounts]:
    root = PROCESSED if processed is None else processed
    frame = pd.read_csv(_require(root / "tamil_nadu_medium_aggregate_rates.csv"))
    rows: list[MediumPeriodCounts] = []
    for record in frame.to_dict("records"):
        rows.append(
            MediumPeriodCounts(
                period=str(record["period"]),
                english_applicants=int(record["english_applicants"]),
                tamil_applicants=int(record["tamil_applicants"]),
                english_government_allotments=int(record["english_government_allotments"]),
                tamil_government_allotments=int(record["tamil_government_allotments"]),
            )
        )
    return rows


def load_medium_year_rates(processed: Path | None = None) -> pd.DataFrame:
    root = PROCESSED if processed is None else processed
    return pd.read_csv(_require(root / "tamil_nadu_medium_admission_rates.csv"))


def load_employment_benchmarks(processed: Path | None = None) -> list[EmploymentBenchmark]:
    root = PROCESSED if processed is None else processed
    frame = pd.read_csv(_require(root / "employment_benchmarks.csv"))
    return [
        EmploymentBenchmark(
            id=str(row["id"]),
            measure=str(row["measure"]),
            estimate=float(row["estimate"]),
            suggested_prior_ess=float(row["suggested_prior_ess"]),
            age_band=str(row["age_band"]),
            source=str(row["source"]),
            notes=str(row["notes"]),
        )
        for row in frame.to_dict("records")
        if float(row["suggested_prior_ess"]) > 0
    ]


def load_wage_anchors(processed: Path | None = None) -> dict[str, WageAnchor]:
    """Load medicine/engineering/nursing wage anchors.

    Prefers MoSPI PLFS 2025 medians + geometric SDs from
    ``data/processed/mospi/plfs_wage_anchors.csv`` when present; falls back to
    World Bank published means in ``published_estimates.csv``.
    """

    root = PROCESSED if processed is None else processed
    plfs_path = root / "mospi" / "plfs_wage_anchors.csv"
    anchors: dict[str, WageAnchor] = {}
    if plfs_path.exists():
        frame = pd.read_csv(plfs_path)
        preferred = frame
        if "preferred_for_model" in frame.columns:
            preferred = frame[frame["preferred_for_model"].astype(bool)]
        if "source_wave" in preferred.columns:
            wave = preferred[preferred["source_wave"].astype(str) == "plfs_2025"]
            if not wave.empty:
                preferred = wave
        for row in preferred.to_dict("records"):
            field = str(row["field"])
            if field not in {"medicine", "engineering", "nursing"}:
                continue
            geom = float(row.get("geometric_sd", 1.75) or 1.75)
            if not (geom > 1.0):
                geom = 1.75
            anchors[field] = WageAnchor(
                estimate_id=f"plfs_2025_{field}_monthly_median",
                monthly_inr=float(row["monthly_median_inr"]),
                source=(
                    f"MoSPI PLFS 2025 unit file; NCO bucket {row.get('source_field', field)}; "
                    f"n={int(row.get('n_unweighted', 0))}"
                ),
                geometric_sd=geom,
                statistic="median",
            )
        if {"medicine", "engineering", "nursing"} <= anchors.keys():
            return anchors

    estimates = load_published_estimates(processed)
    wanted = {
        "world_bank_physician_monthly_wage": "medicine",
        "world_bank_engineer_monthly_wage": "engineering",
        "world_bank_professional_nurse_monthly_wage": "nursing",
    }
    for estimate_id, key in wanted.items():
        if key in anchors:
            continue
        row = estimates.loc[estimates["estimate_id"] == estimate_id].iloc[0]
        anchors[key] = WageAnchor(
            estimate_id=estimate_id,
            monthly_inr=float(row["value"]),
            source=str(row["source"]),
            geometric_sd=1.75,
            statistic="mean",
        )
    return anchors


def load_plfs_extended_wage_anchors(processed: Path | None = None) -> dict[str, WageAnchor]:
    """Optional extended fields (non_professional_graduate, no_college) from PLFS aggregates."""

    root = PROCESSED if processed is None else processed
    path = root / "mospi" / "plfs_wage_anchors.csv"
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if "source_wave" in frame.columns:
        frame = frame[frame["source_wave"].astype(str) == "plfs_2025"]
    out: dict[str, WageAnchor] = {}
    for row in frame.to_dict("records"):
        field = str(row["field"])
        if field not in {"non_professional_graduate", "no_college"}:
            continue
        geom = float(row.get("geometric_sd", 1.75) or 1.75)
        if not (geom > 1.0):
            geom = 1.75
        out[field] = WageAnchor(
            estimate_id=f"plfs_2025_{field}_monthly_median",
            monthly_inr=float(row["monthly_median_inr"]),
            source=f"MoSPI PLFS 2025; {row.get('source_field', field)}; n={int(row.get('n_unweighted', 0))}",
            geometric_sd=geom,
            statistic="median",
        )
    return out


def load_cmse_coaching_priors(processed: Path | None = None) -> pd.DataFrame:
    """CMSE 2025 weighted coaching participation/spend margins (school frame)."""

    root = PROCESSED if processed is None else processed
    path = root / "mospi" / "cmse_coaching_priors.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_coaching_rate_summary(processed: Path | None = None) -> list[CoachingCohortOutcome]:
    root = PROCESSED if processed is None else processed
    frame = pd.read_csv(_require(root / "coaching_outcome_rate_summary.csv"))
    return [
        CoachingCohortOutcome(
            evidence_id=str(row["evidence_id"]),
            program=str(row["program"]),
            cohort_year=str(row["cohort_year"]),
            outcome=str(row["outcome"]),
            successes=int(row["successes"]),
            trials=int(row["trials"]),
            observed_rate=float(row["observed_rate"]),
            selection_into_program=str(row["selection_into_program"]),
            evidence_role=str(row["evidence_role"]),
        )
        for row in frame.to_dict("records")
    ]


def load_aiq_course_counts(processed: Path | None = None) -> AiqCourseCounts:
    """Count MCC 2024 tidy allotment rows by course family.

    These are AIQ/deemed/central counselling allotment events, not national seat outcomes.
    """

    root = PROCESSED if processed is None else processed
    path = root / "mcc_2024" / "mcc_2024_allotments.csv"
    if not path.exists():
        return AiqCourseCounts(mbbs=0, bds=0, nursing=0, other=0, total=0)
    frame = pd.read_csv(path, usecols=["course"])
    courses = frame["course"].astype(str).str.upper()
    mbbs = int(courses.eq("MBBS").sum())
    bds = int(courses.eq("BDS").sum())
    nursing = int(courses.str.contains("NURS", na=False).sum())
    total = int(len(courses))
    other = total - mbbs - bds - nursing
    return AiqCourseCounts(mbbs=mbbs, bds=bds, nursing=nursing, other=other, total=total)
