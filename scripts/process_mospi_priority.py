"""Build commit-safe MoSPI aggregates for the NEET microsimulation.

Reads local unit CSVs from data/external/mospi/ (gitignored) and writes
small weighted summary tables under data/processed/mospi/.

Does not redistribute microdata.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "mospi"


def wmean(x: np.ndarray, w: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not m.any():
        return float("nan")
    return float(np.average(x[m], weights=w[m]))


def wquantiles(x: np.ndarray, w: np.ndarray, qs=(0.1, 0.25, 0.5, 0.75, 0.9, 0.95)) -> dict[str, float]:
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not m.any():
        return {f"p{int(q * 100)}": float("nan") for q in qs}
    xv = x[m]
    wv = w[m]
    order = np.argsort(xv)
    xv, wv = xv[order], wv[order]
    cw = np.cumsum(wv)
    cw = cw / cw[-1]
    out: dict[str, float] = {}
    for q in qs:
        out[f"p{int(q * 100)}"] = float(xv[min(np.searchsorted(cw, q, side="left"), len(xv) - 1)])
    return out


def wgeom_sd(x: np.ndarray, w: np.ndarray) -> float:
    """Geometric SD = exp(weighted SD of log earnings)."""
    m = np.isfinite(x) & (x > 0) & np.isfinite(w) & (w > 0)
    if m.sum() < 5:
        return float("nan")
    lx = np.log(x[m])
    ww = w[m]
    mu = np.average(lx, weights=ww)
    var = np.average((lx - mu) ** 2, weights=ww)
    return float(np.exp(np.sqrt(max(var, 0.0))))


def earn_summary(earn: np.ndarray, w: np.ndarray) -> dict:
    m = np.isfinite(earn) & (earn > 0) & np.isfinite(w) & (w > 0)
    if not m.any():
        return {"n": 0}
    return {
        "n": int(m.sum()),
        "monthly_mean_weighted": wmean(earn[m], w[m]),
        "geometric_sd": wgeom_sd(earn[m], w[m]),
        **wquantiles(earn[m], w[m]),
    }


def zip_member(zpath: Path, substr: str) -> str:
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if substr in n and n.lower().endswith(".csv"):
                return n
    raise FileNotFoundError(f"{substr} in {zpath}")


def process_plfs_2025() -> pd.DataFrame:
    zpath = ROOT / "data/external/mospi/plfs/2025/raw/Data_in_CSV.zip"
    member = zip_member(zpath, "cperv12025.csv")
    usecols = ["age", "gedu_lvl", "tedu_lvl", "pas", "ocu_pas", "ern_reg", "ern_self", "mult"]
    buckets: dict[str, list[pd.DataFrame]] = {
        "medicine_nco_221": [],
        "nursing_nco_222": [],
        "health_nco_22x": [],
        "engineering_nco_21x": [],
        "non_professional_graduate": [],
        "no_college": [],
        "all_positive_earners": [],
    }
    youth_grad_lf_w = 0.0
    youth_grad_unemp_w = 0.0

    with zipfile.ZipFile(zpath) as z:
        for chunk in pd.read_csv(z.open(member), usecols=usecols, chunksize=250_000, low_memory=False):
            age = pd.to_numeric(chunk["age"], errors="coerce")
            gedu = pd.to_numeric(chunk["gedu_lvl"], errors="coerce")
            pas = pd.to_numeric(chunk["pas"], errors="coerce")
            ocu = pd.to_numeric(chunk["ocu_pas"], errors="coerce")
            w = pd.to_numeric(chunk["mult"], errors="coerce")
            earn = pd.to_numeric(chunk["ern_reg"], errors="coerce").fillna(0) + pd.to_numeric(
                chunk["ern_self"], errors="coerce"
            ).fillna(0)
            positive = earn > 0

            youth_grad = age.between(15, 29) & (gedu >= 11)
            in_lf = pas.isin([11, 12, 21, 31, 41, 42, 51, 61, 62, 71, 72, 81, 82])
            unemp = pas.isin([81, 82])
            youth_grad_lf_w += float(w[youth_grad & in_lf].sum())
            youth_grad_unemp_w += float(w[youth_grad & in_lf & unemp].sum())

            def take(mask: pd.Series) -> pd.DataFrame:
                m = mask & positive & w.notna() & (w > 0)
                return pd.DataFrame({"earn": earn[m].to_numpy(), "w": w[m].to_numpy()})

            buckets["medicine_nco_221"].append(take(ocu == 221))
            buckets["nursing_nco_222"].append(take(ocu == 222))
            buckets["health_nco_22x"].append(take((ocu // 10) == 22))
            buckets["engineering_nco_21x"].append(take((ocu // 10) == 21))
            # Graduate+ not in eng/health professional NCO families
            buckets["non_professional_graduate"].append(
                take((gedu >= 11) & ~((ocu // 10).isin([21, 22])))
            )
            buckets["no_college"].append(take((gedu < 11) & age.between(18, 59)))
            buckets["all_positive_earners"].append(take(positive))

    rows = []
    for field, parts in buckets.items():
        frame = pd.concat([p for p in parts if len(p)], ignore_index=True) if any(len(p) for p in parts) else pd.DataFrame()
        if frame.empty:
            summary = {"n": 0}
            earn = np.array([])
            ww = np.array([])
        else:
            earn = frame["earn"].to_numpy(dtype=float)
            ww = frame["w"].to_numpy(dtype=float)
            summary = earn_summary(earn, ww)
        rows.append(
            {
                "field": field,
                "source_wave": "plfs_2025",
                "occupation_definition": {
                    "medicine_nco_221": "NCO-2015 221 (medical doctors)",
                    "nursing_nco_222": "NCO-2015 222 (nursing/midwifery professionals)",
                    "health_nco_22x": "NCO-2015 22x health professionals",
                    "engineering_nco_21x": "NCO-2015 21x science/engineering professionals",
                    "non_professional_graduate": "gedu>=11 and NCO not 21x/22x; positive earners",
                    "no_college": "gedu<11, age 18-59; positive earners",
                    "all_positive_earners": "any positive ern_reg+ern_self",
                }[field],
                "n_unweighted": summary.get("n", 0),
                "monthly_median": summary.get("p50"),
                "monthly_mean_weighted": summary.get("monthly_mean_weighted"),
                "geometric_sd": summary.get("geometric_sd"),
                "p10": summary.get("p10"),
                "p25": summary.get("p25"),
                "p75": summary.get("p75"),
                "p90": summary.get("p90"),
                "p95": summary.get("p95"),
                "unit": "INR/month",
                "notes": "Weighted with PLFS mult; CWS regular+self-employed earnings among positive earners",
            }
        )

    unemp_path = OUT / "plfs_youth_grad_unemployment.csv"
    pd.DataFrame(
        [
            {
                "measure": "youth_graduate_unemployment_usual_status",
                "source_wave": "plfs_2025",
                "age_band": "15-29",
                "education": "gedu_lvl>=11",
                "estimate": (youth_grad_unemp_w / youth_grad_lf_w) if youth_grad_lf_w else np.nan,
                "estimate_type": "weighted_rate",
                "denominator": "in labor force (usual status)",
                "notes": "pas in {81,82} / LF statuses; not field-specific",
            }
        ]
    ).to_csv(unemp_path, index=False)

    return pd.DataFrame(rows)


def process_plfs_2023_24() -> pd.DataFrame:
    zpath = ROOT / "data/external/mospi/plfs/2023-24/raw/CSV_data_PLFS_2023_2024.zip"
    member = zip_member(zpath, "perv1.csv")
    usecols = [
        "b4q6_perv1",  # age
        "b4q8_perv1",  # gedu
        "b5pt1q6_perv1",  # ocu
        "b6q9_perv1",  # ern_reg
        "b6q10_perv1",  # ern_self
        "mult_perv1",
    ]
    buckets: dict[str, list[pd.DataFrame]] = {
        "medicine_nco_221": [],
        "nursing_nco_222": [],
        "engineering_nco_21x": [],
        "non_professional_graduate": [],
        "no_college": [],
    }
    with zipfile.ZipFile(zpath) as z:
        for chunk in pd.read_csv(z.open(member), usecols=usecols, chunksize=200_000, low_memory=False):
            age = pd.to_numeric(chunk["b4q6_perv1"], errors="coerce")
            gedu = pd.to_numeric(chunk["b4q8_perv1"], errors="coerce")
            ocu = pd.to_numeric(chunk["b5pt1q6_perv1"], errors="coerce")
            w = pd.to_numeric(chunk["mult_perv1"], errors="coerce")
            earn = pd.to_numeric(chunk["b6q9_perv1"], errors="coerce").fillna(0) + pd.to_numeric(
                chunk["b6q10_perv1"], errors="coerce"
            ).fillna(0)
            positive = earn > 0

            def take(mask: pd.Series) -> pd.DataFrame:
                m = mask & positive & w.notna() & (w > 0)
                return pd.DataFrame({"earn": earn[m].to_numpy(), "w": w[m].to_numpy()})

            buckets["medicine_nco_221"].append(take(ocu == 221))
            buckets["nursing_nco_222"].append(take(ocu == 222))
            buckets["engineering_nco_21x"].append(take((ocu // 10) == 21))
            buckets["non_professional_graduate"].append(
                take((gedu >= 11) & ~((ocu // 10).isin([21, 22])))
            )
            buckets["no_college"].append(take((gedu < 11) & age.between(18, 59)))

    rows = []
    for field, parts in buckets.items():
        frame = pd.concat([p for p in parts if len(p)], ignore_index=True) if any(len(p) for p in parts) else pd.DataFrame()
        if frame.empty:
            summary = {"n": 0}
        else:
            summary = earn_summary(frame["earn"].to_numpy(float), frame["w"].to_numpy(float))
        rows.append(
            {
                "field": field,
                "source_wave": "plfs_2023_24",
                "occupation_definition": field,
                "n_unweighted": summary.get("n", 0),
                "monthly_median": summary.get("p50"),
                "monthly_mean_weighted": summary.get("monthly_mean_weighted"),
                "geometric_sd": summary.get("geometric_sd"),
                "p10": summary.get("p10"),
                "p25": summary.get("p25"),
                "p75": summary.get("p75"),
                "p90": summary.get("p90"),
                "p95": summary.get("p95"),
                "unit": "INR/month",
                "notes": "Visit-1; weighted with mult_perv1; keep separate from PLFS 2025 revamp",
            }
        )
    return pd.DataFrame(rows)


def process_cmse() -> tuple[pd.DataFrame, pd.DataFrame]:
    zpath = ROOT / "data/external/mospi/cmse/2025/raw/Data in CSV.zip"
    with zipfile.ZipFile(zpath) as z:
        per = pd.read_csv(z.open("CMSE80PER25.csv"), low_memory=False)
        hh = pd.read_csv(z.open("CMSE80HH25.csv"), low_memory=False)

    keys = ["fsu_serial_no", "second_stage_stratum_no", "sample_hhld_no"]
    # Person file already has sector; pull HH covariates only.
    m = per.merge(
        hh[keys + ["social_group", "usual_monthly_consumption_expenditure"]],
        on=keys,
        how="left",
    )
    lvl = pd.to_numeric(m["enrolment_level"], errors="coerce")
    enrolled = m["currently_enrolled_school"].eq(1)
    hs = enrolled & lvl.isin([10, 11, 12])
    coach = m["received_private_coaching"].eq(1)
    w = pd.to_numeric(m["mult"], errors="coerce")
    coach_exp = pd.to_numeric(m["private_coaching_exp_total"], errors="coerce")
    school_exp = pd.to_numeric(m["school_exp_total"], errors="coerce")
    cons = pd.to_numeric(m["usual_monthly_consumption_expenditure"], errors="coerce")

    # Consumption terciles among Class X–XII persons (weighted household usual monthly cons.)
    cons_hs = cons[hs].to_numpy(dtype=float)
    w_hs = w[hs].to_numpy(dtype=float)
    cuts = wquantiles(cons_hs, w_hs, qs=(0.333, 0.667))
    lo, hi = cuts["p33"], cuts["p66"]

    def tercile(v: float) -> str:
        if not np.isfinite(v):
            return "unknown"
        if v <= lo:
            return "low"
        if v <= hi:
            return "mid"
        return "high"

    m = m.copy()
    m["consumption_tercile"] = [tercile(float(v)) if pd.notna(v) else "unknown" for v in cons]
    m["enrolment_band"] = np.where(hs, "class_x_xii", np.where(enrolled, "other_enrolled", "not_enrolled"))

    strata_rows = []
    for (sector, sg, terc), g in m[hs].groupby(["sector", "social_group", "consumption_tercile"], dropna=False):
        ww = pd.to_numeric(g["mult"], errors="coerce")
        cc = g["received_private_coaching"].eq(1)
        den = float(ww.sum())
        if den <= 0:
            continue
        rate = float(ww[cc].sum() / den)
        exp = pd.to_numeric(g.loc[cc, "private_coaching_exp_total"], errors="coerce")
        ew = ww[cc]
        exp_s = earn_summary(exp.to_numpy(dtype=float), ew.to_numpy(dtype=float)) if cc.any() else {"n": 0}
        strata_rows.append(
            {
                "sector": int(sector) if pd.notna(sector) else None,
                "sector_label": {1: "rural", 2: "urban"}.get(int(sector) if pd.notna(sector) else -1, "unknown"),
                "social_group": int(sg) if pd.notna(sg) else None,
                "consumption_tercile": terc,
                "enrolment_band": "class_x_xii",
                "n_unweighted": int(len(g)),
                "n_coached_unweighted": int(cc.sum()),
                "coaching_rate_weighted": rate,
                "coaching_exp_p50": exp_s.get("p50"),
                "coaching_exp_p90": exp_s.get("p90"),
                "coaching_exp_mean_weighted": exp_s.get("monthly_mean_weighted"),
                "notes": "CMSE 2025; school Class X-XII; not NEET-specific",
            }
        )

    # Simpler sector × band margins for priors
    margin_rows = []
    for sector_label, sector_code in [("rural", 1), ("urban", 2), ("all", None)]:
        for band, mask in [
            ("all_enrolled", enrolled),
            ("class_x_xii", hs),
            ("class_xii", enrolled & lvl.eq(12)),
        ]:
            if sector_code is None:
                gmask = mask
            else:
                gmask = mask & m["sector"].eq(sector_code)
            ww = w[gmask]
            cc = coach[gmask]
            den = float(ww.sum())
            if den <= 0:
                continue
            exp = coach_exp[gmask & coach]
            ew = w[gmask & coach]
            exp_s = earn_summary(exp.to_numpy(dtype=float), ew.to_numpy(dtype=float)) if len(exp) else {"n": 0}
            sch = school_exp[gmask]
            sch_s = earn_summary(sch.to_numpy(dtype=float), ww.to_numpy(dtype=float))
            margin_rows.append(
                {
                    "sector_label": sector_label,
                    "enrolment_band": band,
                    "n_unweighted": int(gmask.sum()),
                    "n_coached_unweighted": int((gmask & coach).sum()),
                    "coaching_rate_weighted": float(ww[cc].sum() / den),
                    "coaching_exp_p25": exp_s.get("p25"),
                    "coaching_exp_p50": exp_s.get("p50"),
                    "coaching_exp_p75": exp_s.get("p75"),
                    "coaching_exp_p90": exp_s.get("p90"),
                    "coaching_exp_mean_weighted": exp_s.get("monthly_mean_weighted"),
                    "school_exp_p50": sch_s.get("p50"),
                    "notes": "CMSE 2025 weighted with mult; academic-year INR",
                }
            )

    return pd.DataFrame(margin_rows), pd.DataFrame(strata_rows)


def process_hces() -> pd.DataFrame:
    zpath = ROOT / "data/external/mospi/hces/2023-24/raw/HCES_Data_2023-24_Csv.zip"
    member = zip_member(zpath, "LEVEL - 15")
    with zipfile.ZipFile(zpath) as z:
        l15 = pd.read_csv(
            z.open(member),
            usecols=[
                "FSU_Serial_No",
                "Second_Stage_Stratum_No",
                "Sample_Household_No",
                "Sector",
                "State",
                "MONTHLY_CONSUMPTION_EXP",
                "HOUSEHOLD_SIZE",
                "MULTIPLIER",
            ],
            low_memory=False,
        )
    sub = l15[l15["MONTHLY_CONSUMPTION_EXP"].notna()].drop_duplicates(
        ["FSU_Serial_No", "Second_Stage_Stratum_No", "Sample_Household_No"]
    )
    mce = pd.to_numeric(sub["MONTHLY_CONSUMPTION_EXP"], errors="coerce")
    hsz = pd.to_numeric(sub["HOUSEHOLD_SIZE"], errors="coerce")
    w = pd.to_numeric(sub["MULTIPLIER"], errors="coerce")
    mpce = (mce / hsz.replace(0, np.nan)).to_numpy(dtype=float)
    ww = w.to_numpy(dtype=float)
    rows = []
    for label, mask in [
        ("all", np.ones(len(sub), dtype=bool)),
        ("rural", (sub["Sector"] == 1).to_numpy()),
        ("urban", (sub["Sector"] == 2).to_numpy()),
    ]:
        s = earn_summary(mpce[mask], ww[mask])
        # reuse earn_summary field names but this is MPCE not earnings
        rows.append(
            {
                "sector_label": label,
                "n_households": s.get("n", 0),
                "mpce_p10": s.get("p10"),
                "mpce_p25": s.get("p25"),
                "mpce_p50": s.get("p50"),
                "mpce_p75": s.get("p75"),
                "mpce_p90": s.get("p90"),
                "mpce_p95": s.get("p95"),
                "mpce_mean_weighted": s.get("monthly_mean_weighted"),
                "unit": "INR/person/month",
                "definition": "MONTHLY_CONSUMPTION_EXP / HOUSEHOLD_SIZE on Level 15 (proxy; confirm vs official MPCE)",
                "source_wave": "hces_2023_24",
            }
        )
    return pd.DataFrame(rows)


def process_aidis() -> pd.DataFrame:
    zpath = ROOT / "data/external/mospi/aidis/2019/raw/CSV_DI_77.zip"
    with zipfile.ZipFile(zpath) as z:
        debt_name = [n for n in z.namelist() if "Visit1_Level_14" in n][0]
        hh_name = [n for n in z.namelist() if "Visit1  Level - 01" in n][0]
        debt = pd.read_csv(z.open(debt_name), low_memory=False)
        hh = pd.read_csv(z.open(hh_name), usecols=["HHID", "Sector", "MLT"], low_memory=False)

    sub = debt[~debt["b12q1"].isin([99])].copy()
    sub["amt"] = pd.to_numeric(sub["b12q14"], errors="coerce")
    g = sub.groupby("HHID", as_index=False).agg(debt=("amt", "sum"))
    g = g.merge(hh, on="HHID", how="right")
    g["debt"] = g["debt"].fillna(0)
    w = pd.to_numeric(g["MLT"], errors="coerce").to_numpy(dtype=float)
    debt_v = g["debt"].to_numpy(dtype=float)
    indebted = debt_v > 0
    rows = []
    for label, mask in [
        ("all_hh", np.ones(len(g), dtype=bool)),
        ("indebted_hh", indebted),
        ("rural_indebted", indebted & (g["Sector"] == 1).to_numpy()),
        ("urban_indebted", indebted & (g["Sector"] == 2).to_numpy()),
    ]:
        s = earn_summary(debt_v[mask], w[mask]) if mask.any() else {"n": 0}
        rows.append(
            {
                "population": label,
                "n_households": int(mask.sum()),
                "share_of_all_hh": float(mask.sum() / len(g)) if len(g) else np.nan,
                "debt_p25": s.get("p25"),
                "debt_p50": s.get("p50"),
                "debt_p75": s.get("p75"),
                "debt_p90": s.get("p90"),
                "debt_p95": s.get("p95"),
                "debt_mean_weighted": s.get("monthly_mean_weighted"),
                "unit": "INR outstanding (2019)",
                "definition": "Sum of Visit1 Block12 b12q14 excluding item code 99",
                "notes": "Upper-bound indebtedness incidence until purpose filters applied; inflate to NEET-year INR",
            }
        )
    return pd.DataFrame(rows)


def build_model_wage_anchors(plfs: pd.DataFrame) -> pd.DataFrame:
    """Map PLFS occupation buckets onto privilege/bayes field keys."""
    pref = plfs[plfs["source_wave"] == "plfs_2025"].set_index("field")
    mapping = {
        "medicine": "medicine_nco_221",
        "engineering": "engineering_nco_21x",
        "nursing": "nursing_nco_222",
        "non_professional_graduate": "non_professional_graduate",
        "no_college": "no_college",
    }
    rows = []
    for model_field, src in mapping.items():
        if src not in pref.index:
            continue
        r = pref.loc[src]
        rows.append(
            {
                "field": model_field,
                "source_wave": "plfs_2025",
                "source_field": src,
                "monthly_median_inr": r["monthly_median"],
                "monthly_mean_weighted_inr": r["monthly_mean_weighted"],
                "geometric_sd": r["geometric_sd"],
                "n_unweighted": r["n_unweighted"],
                "p25": r["p25"],
                "p75": r["p75"],
                "p90": r["p90"],
                "preferred_for_model": True,
                "notes": "Prefer median+geometric_sd for lognormal career paths; means for validation only",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    print("PLFS 2025...")
    plfs25 = process_plfs_2025()
    print("PLFS 2023-24...")
    plfs2324 = process_plfs_2023_24()
    plfs = pd.concat([plfs25, plfs2324], ignore_index=True)
    plfs.to_csv(out / "plfs_earnings_by_occupation.csv", index=False)
    anchors = build_model_wage_anchors(plfs)
    anchors.to_csv(out / "plfs_wage_anchors.csv", index=False)

    print("CMSE...")
    margins, strata = process_cmse()
    margins.to_csv(out / "cmse_coaching_priors.csv", index=False)
    strata.to_csv(out / "cmse_coaching_by_stratum.csv", index=False)

    print("HCES...")
    hces = process_hces()
    hces.to_csv(out / "hces_mpce_percentiles.csv", index=False)

    print("AIDIS...")
    aidis = process_aidis()
    aidis.to_csv(out / "aidis_debt_percentiles.csv", index=False)

    manifest = {
        "output_dir": str(out.relative_to(ROOT)).replace("\\", "/"),
        "files": sorted(p.name for p in out.glob("*.csv")),
        "redistribution": "aggregates only; unit microdata remain local/gitignored",
        "model_hooks": {
            "wages": "plfs_wage_anchors.csv -> evidence.load_wage_anchors / privilege careers",
            "coaching": "cmse_coaching_priors.csv + cmse_coaching_by_stratum.csv",
            "resources": "hces_mpce_percentiles.csv",
            "financing": "aidis_debt_percentiles.csv",
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Wrote", out)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
