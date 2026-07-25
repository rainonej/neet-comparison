"""Preliminary schema inspection and stats for acquired open datasets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("data/processed/prelim_analysis")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    report: dict = {}

    marks = pd.read_csv(
        "data/external/neet-2024-center-marks.csv",
        header=None,
        names=["centre_id", "serial_number", "marks"],
        dtype={"centre_id": "int32", "serial_number": "int32", "marks": "int16"},
    )
    report["neet"] = {
        "rows": int(len(marks)),
        "centres": int(marks.centre_id.nunique()),
        "min": int(marks.marks.min()),
        "max": int(marks.marks.max()),
        "mean": float(marks.marks.mean()),
        "std": float(marks.marks.std()),
        "median": float(marks.marks.median()),
        "p10": float(marks.marks.quantile(0.10)),
        "p25": float(marks.marks.quantile(0.25)),
        "p75": float(marks.marks.quantile(0.75)),
        "p90": float(marks.marks.quantile(0.90)),
        "p95": float(marks.marks.quantile(0.95)),
        "p99": float(marks.marks.quantile(0.99)),
        "neg": int((marks.marks < 0).sum()),
        "zero": int((marks.marks == 0).sum()),
        "ge_650": int((marks.marks >= 650).sum()),
        "ge_600": int((marks.marks >= 600).sum()),
        "ge_500": int((marks.marks >= 500).sum()),
        "ge_400": int((marks.marks >= 400).sum()),
        "ge_200": int((marks.marks >= 200).sum()),
        "eq_720": int((marks.marks == 720).sum()),
    }
    bins = [-180, 0, 100, 200, 300, 400, 500, 600, 650, 700, 721]
    labels = [
        "<0",
        "0-99",
        "100-199",
        "200-299",
        "300-399",
        "400-499",
        "500-599",
        "600-649",
        "650-699",
        "700-720",
    ]
    band = pd.cut(marks.marks, bins=bins, labels=labels, right=False, include_lowest=True)
    hist = band.value_counts(sort=False)
    report["neet_hist"] = [{"band": str(i), "n": int(v), "share": float(v / len(marks))} for i, v in hist.items()]

    centre = marks.groupby("centre_id")["marks"].agg(["count", "mean", "median", "std", "max"]).reset_index()
    report["neet_centres"] = {
        "mean_of_means": float(centre["mean"].mean()),
        "median_of_medians": float(centre["median"].median()),
        "centres_mean_ge_400": int((centre["mean"] >= 400).sum()),
        "centres_mean_ge_500": int((centre["mean"] >= 500).sum()),
        "smallest_lt_50": int((centre["count"] < 50).sum()),
        "largest_centre_n": int(centre["count"].max()),
        "median_centre_n": float(centre["count"].median()),
    }
    big = centre[centre["count"] >= 100].copy()
    report["neet_top_centres"] = (
        big.nlargest(8, "mean")[["centre_id", "count", "mean", "median", "max"]].round(1).to_dict(orient="records")
    )
    report["neet_bottom_centres"] = (
        big.nsmallest(8, "mean")[["centre_id", "count", "mean", "median", "max"]].round(1).to_dict(orient="records")
    )

    nmc = pd.read_csv("data/raw/nmc_colleges.csv")
    report["nmc_schema"] = {c: str(nmc[c].dtype) for c in nmc.columns}
    report["nmc_n"] = int(len(nmc))
    seats = pd.to_numeric(nmc["ugApproved"], errors="coerce")
    # Scrape stores labels in stateName / managementupdate; numeric state/management are null.
    mgmt_col = "managementupdate" if "managementupdate" in nmc.columns else "management"
    state_col = "stateName" if "stateName" in nmc.columns else "state"
    report["nmc_seats"] = {
        "total": float(np.nansum(seats)),
        "mean": float(np.nanmean(seats)),
        "median": float(np.nanmedian(seats)),
        "min": float(np.nanmin(seats)),
        "max": float(np.nanmax(seats)),
        "missing": int(seats.isna().sum()),
    }
    nmc = nmc.assign(
        _seats=seats,
        _mgmt=nmc[mgmt_col].astype(str).str.strip(),
        _state=nmc[state_col].astype(str).str.strip(),
    )
    by_mgmt = (
        nmc.groupby("_mgmt", dropna=False)
        .agg(colleges=("_mgmt", "size"), seats=("_seats", "sum"))
        .sort_values("seats", ascending=False)
    )
    report["nmc_by_mgmt"] = [
        {"management": str(i), "colleges": int(r.colleges), "seats": float(r.seats)} for i, r in by_mgmt.iterrows()
    ]
    by_state = (
        nmc.groupby("_state")
        .agg(colleges=("_state", "size"), seats=("_seats", "sum"))
        .sort_values("seats", ascending=False)
    )
    report["nmc_by_state"] = [
        {"state": str(i), "colleges": int(r.colleges), "seats": float(r.seats)} for i, r in by_state.head(15).iterrows()
    ]
    report["nmc_states_n"] = int(nmc["_state"].nunique())

    def classify(m: object) -> str:
        text = str(m).lower()
        if any(k in text for k in ("govt", "government", "state government", "central", "aiims")):
            return "government_like"
        if any(k in text for k in ("trust", "society", "private", "deemed", "corp", "company")):
            return "private_like"
        return "other"

    nmc["_own"] = nmc["_mgmt"].map(classify)
    own = nmc.groupby("_own").agg(colleges=("_own", "size"), seats=("_seats", "sum"))
    report["nmc_ownership"] = [
        {"type": str(i), "colleges": int(r.colleges), "seats": float(r.seats)} for i, r in own.iterrows()
    ]

    osf = pd.read_csv("data/external/osf/tnh4x/raw/Data_for_analysis.csv")
    report["osf_schema"] = {c: str(osf[c].dtype) for c in osf.columns}
    report["osf_n"] = int(len(osf))
    report["osf_demo"] = {
        "age_mean": float(osf["Age"].mean()),
        "age_sd": float(osf["Age"].std()),
        "age_min": float(osf["Age"].min()),
        "age_max": float(osf["Age"].max()),
        "gender_counts": {str(k): int(v) for k, v in osf["Gender"].value_counts(dropna=False).items()},
        "ses_counts": {
            str(k): int(v)
            for k, v in osf["SES (5= highest and 1= Lowest)"].value_counts(dropna=False).sort_index().items()
        },
    }
    for col in ["ESS", "PPE", "GMS", "DSHI"]:
        s = pd.to_numeric(osf[col], errors="coerce")
        report[f"osf_{col}"] = {
            "mean": float(s.mean()),
            "sd": float(s.std()),
            "min": float(s.min()),
            "max": float(s.max()),
            "missing": int(s.isna().sum()),
        }
    corr_cols = ["Age", "SES (5= highest and 1= Lowest)", "ESS", "PPE", "GMS", "DSHI"]
    cmat = osf[corr_cols].apply(pd.to_numeric, errors="coerce").corr()
    report["osf_corr"] = {
        str(r): {str(c): float(cmat.loc[r, c]) for c in cmat.columns} for r in cmat.index
    }
    tmp = osf.assign(
        SES=pd.to_numeric(osf["SES (5= highest and 1= Lowest)"], errors="coerce"),
        DSHI=pd.to_numeric(osf["DSHI"], errors="coerce"),
        PPE=pd.to_numeric(osf["PPE"], errors="coerce"),
        ESS=pd.to_numeric(osf["ESS"], errors="coerce"),
    )
    report["osf_by_ses"] = (
        tmp.groupby("SES")
        .agg(
            n=("DSHI", "count"),
            dshi_mean=("DSHI", "mean"),
            ppe_mean=("PPE", "mean"),
            ess_mean=("ESS", "mean"),
        )
        .reset_index()
        .round(2)
        .to_dict(orient="records")
    )

    mcc = pd.read_csv("data/raw/mcc_2024/2024/archive_index.csv")
    report["mcc_n"] = int(len(mcc))
    report["mcc_titles"] = mcc["title"].astype(str).tolist()

    klinks = pd.read_csv("data/external/kerala_cee/raw/discovered_links.csv")
    report["kerala_links_n"] = int(len(klinks))
    report["kerala_links"] = klinks.to_dict(orient="records")

    try:
        pub = pd.read_csv("data/processed/published_estimates.csv")
        report["published"] = pub.to_dict(orient="records")
    except Exception as exc:  # noqa: BLE001
        report["published_error"] = str(exc)

    nmc_total = report["nmc_seats"]["total"]
    neet_n = report["neet"]["rows"]
    report["scarcity"] = {
        "nmc_ug_seats_sum": nmc_total,
        "neet_2024_mark_rows": neet_n,
        "candidates_per_nmc_seat": float(neet_n / nmc_total) if nmc_total else None,
        "share_ge_650": float(report["neet"]["ge_650"] / neet_n),
        "share_ge_600": float(report["neet"]["ge_600"] / neet_n),
        "share_ge_500": float(report["neet"]["ge_500"] / neet_n),
    }

    (OUT / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["neet", "nmc_seats", "scarcity", "osf_demo", "nmc_ownership"]}, indent=2))
    print("wrote", OUT / "summary.json")


if __name__ == "__main__":
    main()
