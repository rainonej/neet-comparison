"""Build commit-safe Delhi education and coaching aggregates.

Raw MoSPI unit files remain under data/external/mospi and are never
redistributed. Outputs are weighted aggregate tables only. CMSE coaching is
school tutoring broadly, not NEET-specific coaching.
"""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "delhi"
DELHI_STATE_CODE = 7
MIN_CELL_N = 30
MEDIUM_LABELS = {1: "hindi", 2: "english"}
SCHOOL_TYPE_LABELS = {
    1: "government",
    2: "govt_aided_private",
    3: "private_unaided_recognised",
    4: "private_unaided_unrecognised",
    5: "others",
}


def nss_state_code(value: object) -> int | None:
    """Recover the two-digit state code from an NSS-region value.

    Delhi region codes such as 071/072 may be parsed from CSV as 71/72 or
    71.0, so normalize to three digits before taking the first two.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", maxsplit=1)[0]
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return int(digits.zfill(3)[:2])


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    x = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors="coerce").to_numpy(dtype=float)
    good = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not good.any():
        return float("nan")
    return float(np.average(x[good], weights=w[good]))


def weighted_share(mask: pd.Series | np.ndarray, weights: pd.Series | np.ndarray) -> float:
    m = np.asarray(mask, dtype=bool)
    w = np.asarray(weights, dtype=float)
    good = np.isfinite(w) & (w > 0)
    if not good.any():
        return float("nan")
    return float(w[good & m].sum() / w[good].sum())


def weighted_quantiles(
    values: pd.Series | np.ndarray,
    weights: pd.Series | np.ndarray,
    quantiles: tuple[float, ...] = (0.25, 0.5, 0.75, 0.9),
) -> dict[str, float]:
    x = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    good = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not good.any():
        return {f"p{int(q * 100)}": float("nan") for q in quantiles}
    x, w = x[good], w[good]
    order = np.argsort(x)
    x, w = x[order], w[order]
    cumulative = np.cumsum(w) / w.sum()
    return {
        f"p{int(q * 100)}": float(x[min(np.searchsorted(cumulative, q), len(x) - 1)])
        for q in quantiles
    }


def weighted_quintile(values: pd.Series, weights: pd.Series) -> pd.Series:
    cuts = weighted_quantiles(values, weights, quantiles=(0.2, 0.4, 0.6, 0.8))
    boundaries = np.array([cuts["p20"], cuts["p40"], cuts["p60"], cuts["p80"]])
    numeric = pd.to_numeric(values, errors="coerce")
    out = pd.Series(pd.NA, index=values.index, dtype="Int64")
    finite = numeric.notna() & np.isfinite(numeric)
    out.loc[finite] = np.searchsorted(boundaries, numeric.loc[finite], side="left") + 1
    return out


def zip_member(zpath: Path, contains: str) -> str:
    with zipfile.ZipFile(zpath) as archive:
        for name in archive.namelist():
            if contains.lower() in name.lower() and name.lower().endswith(".csv"):
                return name
    raise FileNotFoundError(f"Could not find CSV containing {contains!r} in {zpath}")


def process_cmse(zpath: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Produce Delhi coaching margins, resource quintiles, and school-type cells."""
    with zipfile.ZipFile(zpath) as archive:
        per = pd.read_csv(archive.open("CMSE80PER25.csv"), low_memory=False)
        hh = pd.read_csv(archive.open("CMSE80HH25.csv"), low_memory=False)

    if "nss_region" not in per:
        raise KeyError("CMSE person file is missing nss_region")
    per = per.loc[per["nss_region"].map(nss_state_code).eq(DELHI_STATE_CODE)].copy()
    if per.empty:
        raise ValueError("No NCT Delhi records found in CMSE person file")

    keys = ["fsu_serial_no", "second_stage_stratum_no", "sample_hhld_no"]
    hh_cols = keys + ["social_group", "usual_monthly_consumption_expenditure"]
    merged = per.merge(hh[hh_cols], on=keys, how="left", validate="many_to_one")

    level = pd.to_numeric(merged["enrolment_level"], errors="coerce")
    enrolled = merged["currently_enrolled_school"].eq(1)
    consumption = pd.to_numeric(
        merged["usual_monthly_consumption_expenditure"], errors="coerce"
    )
    bands = {
        "all_enrolled": enrolled,
        "class_x_xii": enrolled & level.isin([10, 11, 12]),
        "class_xii": enrolled & level.eq(12),
    }

    margin_rows: list[dict[str, object]] = []
    for band, mask in bands.items():
        g = merged.loc[mask].copy()
        if len(g) < MIN_CELL_N:
            continue
        gw = pd.to_numeric(g["mult"], errors="coerce")
        gc = g["received_private_coaching"].eq(1)
        exp = pd.to_numeric(g.loc[gc, "private_coaching_exp_total"], errors="coerce")
        exp_w = pd.to_numeric(g.loc[gc, "mult"], errors="coerce")
        exp_q = weighted_quantiles(exp, exp_w)
        cons_q = weighted_quantiles(
            pd.to_numeric(g["usual_monthly_consumption_expenditure"], errors="coerce"), gw
        )
        margin_rows.append(
            {
                "geography": "NCT Delhi",
                "enrolment_band": band,
                "n_unweighted": int(len(g)),
                "n_coached_unweighted": int(gc.sum()),
                "coaching_rate_weighted": weighted_share(gc, gw),
                "coaching_exp_p25_among_coached": exp_q["p25"],
                "coaching_exp_p50_among_coached": exp_q["p50"],
                "coaching_exp_p75_among_coached": exp_q["p75"],
                "coaching_exp_p90_among_coached": exp_q["p90"],
                "coaching_exp_mean_among_coached": weighted_mean(exp, exp_w),
                "usual_monthly_household_consumption_p50": cons_q["p50"],
                "source_wave": "cmse_2025",
                "notes": "Weighted with mult; coaching is not NEET-specific; expenditure is per academic year",
            }
        )

    target = bands["class_x_xii"] & consumption.notna() & (consumption > 0)
    target_frame = merged.loc[target].copy()
    target_frame["consumption_quintile"] = weighted_quintile(
        pd.to_numeric(target_frame["usual_monthly_consumption_expenditure"], errors="coerce"),
        pd.to_numeric(target_frame["mult"], errors="coerce"),
    )
    resource_rows: list[dict[str, object]] = []
    for quintile, g in target_frame.groupby("consumption_quintile", dropna=True):
        if len(g) < MIN_CELL_N:
            continue
        gw = pd.to_numeric(g["mult"], errors="coerce")
        gc = g["received_private_coaching"].eq(1)
        exp = pd.to_numeric(g.loc[gc, "private_coaching_exp_total"], errors="coerce")
        exp_w = pd.to_numeric(g.loc[gc, "mult"], errors="coerce")
        cons = pd.to_numeric(
            g.loc[gc, "usual_monthly_consumption_expenditure"], errors="coerce"
        )
        burden = exp / (12.0 * cons)
        resource_rows.append(
            {
                "geography": "NCT Delhi",
                "enrolment_band": "class_x_xii",
                "consumption_quintile_within_delhi": int(quintile),
                "n_unweighted": int(len(g)),
                "n_coached_unweighted": int(gc.sum()),
                "coaching_rate_weighted": weighted_share(gc, gw),
                "usual_monthly_household_consumption_p50": weighted_quantiles(
                    pd.to_numeric(g["usual_monthly_consumption_expenditure"], errors="coerce"),
                    gw,
                    quantiles=(0.5,),
                )["p50"],
                "coaching_exp_p50_among_coached": weighted_quantiles(
                    exp, exp_w, quantiles=(0.5,)
                )["p50"],
                "coaching_exp_mean_among_coached": weighted_mean(exp, exp_w),
                "coaching_burden_p50_among_coached": weighted_quantiles(
                    burden, exp_w, quantiles=(0.5,)
                )["p50"],
                "source_wave": "cmse_2025",
                "notes": "Delhi-specific quintiles; burden=annual coaching/(12x monthly household consumption)",
            }
        )

    school_rows: list[dict[str, object]] = []
    for school_type, g in merged.loc[bands["class_x_xii"]].groupby(
        "school_type", dropna=False
    ):
        if len(g) < MIN_CELL_N:
            continue
        st = int(school_type) if pd.notna(school_type) else None
        gw = pd.to_numeric(g["mult"], errors="coerce")
        gc = g["received_private_coaching"].eq(1)
        exp = pd.to_numeric(g.loc[gc, "private_coaching_exp_total"], errors="coerce")
        exp_w = pd.to_numeric(g.loc[gc, "mult"], errors="coerce")
        exp_q = weighted_quantiles(exp, exp_w, quantiles=(0.5, 0.9))
        school_rows.append(
            {
                "geography": "NCT Delhi",
                "enrolment_band": "class_x_xii",
                "school_type": st,
                "school_type_label": SCHOOL_TYPE_LABELS.get(st or -1, "unknown"),
                "n_unweighted": int(len(g)),
                "n_coached_unweighted": int(gc.sum()),
                "coaching_rate_weighted": weighted_share(gc, gw),
                "coaching_exp_p50_among_coached": exp_q["p50"],
                "coaching_exp_p90_among_coached": exp_q["p90"],
                "source_wave": "cmse_2025",
                "notes": "Class X-XII school tutoring; not NEET-specific",
            }
        )

    return pd.DataFrame(margin_rows), pd.DataFrame(resource_rows), pd.DataFrame(school_rows)


def process_nss_education(zpath: Path) -> pd.DataFrame:
    """Estimate historical Delhi medium-of-instruction x private-coaching margins."""
    member = zip_member(zpath, "Block-5")
    with zipfile.ZipFile(zpath) as archive:
        frame = pd.read_csv(
            archive.open(member),
            usecols=[
                "State",
                "Sector",
                "Age",
                "Medium_instruction",
                "Enrol_basic_course",
                "Institution_type",
                "Taking_pvt_coaching",
                "MULT_Combined",
            ],
            low_memory=False,
        )

    state = pd.to_numeric(frame["State"], errors="coerce")
    level = pd.to_numeric(frame["Enrol_basic_course"], errors="coerce")
    delhi = frame.loc[state.eq(DELHI_STATE_CODE) & level.isin([10, 11])].copy()
    if delhi.empty:
        raise ValueError("No Delhi secondary/higher-secondary records found in NSS Education")

    rows: list[dict[str, object]] = []
    for medium, g in delhi.groupby("Medium_instruction", dropna=True):
        if len(g) < MIN_CELL_N:
            continue
        code = int(medium)
        gw = pd.to_numeric(g["MULT_Combined"], errors="coerce")
        gc = g["Taking_pvt_coaching"].eq(1)
        rows.append(
            {
                "geography": "NCT Delhi",
                "population": "secondary_higher_secondary_attending",
                "medium_code": code,
                "medium_label": MEDIUM_LABELS.get(code, f"code_{code}"),
                "n_unweighted": int(len(g)),
                "n_coached_unweighted": int(gc.sum()),
                "weighted_population_mass": float(gw.sum()),
                "coaching_rate_weighted": weighted_share(gc, gw),
                "source_wave": "nss_education_2017_18",
                "notes": "Historical school medium/coaching joint; not NEET language or coaching",
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result["student_share_weighted"] = (
            result["weighted_population_mass"] / result["weighted_population_mass"].sum()
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cmse",
        type=Path,
        default=ROOT / "data/external/mospi/cmse/2025/raw/Data in CSV.zip",
    )
    parser.add_argument(
        "--nss-education",
        type=Path,
        default=ROOT / "data/external/mospi/nss_education/2017-18/raw/Data_in_CSV.zip",
    )
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    missing = [path for path in (args.cmse, args.nss_education) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing restricted/local archives: " + ", ".join(str(path) for path in missing)
        )

    args.out.mkdir(parents=True, exist_ok=True)
    margins, resources, school_types = process_cmse(args.cmse)
    medium = process_nss_education(args.nss_education)
    margins.to_csv(args.out / "delhi_cmse_coaching_by_band.csv", index=False)
    resources.to_csv(
        args.out / "delhi_cmse_coaching_by_consumption_quintile.csv", index=False
    )
    school_types.to_csv(args.out / "delhi_cmse_coaching_by_school_type.csv", index=False)
    medium.to_csv(args.out / "delhi_nss75_medium_coaching.csv", index=False)
    print(f"Wrote Delhi aggregates to {args.out}")


if __name__ == "__main__":
    main()
