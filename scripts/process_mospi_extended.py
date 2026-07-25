"""Build additional commit-safe MoSPI aggregates from newly available unit files.

Extends the priority pass with:
- NSS Education 2017-18 coaching / medium / prep-for-higher joints
- PLFS 2025 field-specific employment gates (technical education)
- CMSE Class X-XII coaching by school type
- Block-7 not-attending prep intensity (aspirant/dropper proxy)

Unit microdata stay gitignored under data/external/mospi/.
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

# Medium-of-instruction codes for NSS 75 Sch 25.2 (ICSSR data dictionary):
# Hindi=01, English=02. Other codes follow the schedule language list — keep numeric
# codes in outputs; only highlight hindi/english until full codebook is wired.
MEDIUM_LABELS = {
    1: "hindi",
    2: "english",
}

SG_LABELS = {1: "ST", 2: "SC", 3: "OBC", 9: "Others"}
SECTOR_LABELS = {1: "rural", 2: "urban"}
SCHOOL_TYPE_LABELS = {
    1: "government",
    2: "govt_aided_private",
    3: "private_unaided_recognised",
    4: "private_unaided_unrecognised",
    5: "others",
}


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


def wshare(mask: np.ndarray, w: np.ndarray) -> float:
    m = np.asarray(mask, dtype=bool)
    ww = np.asarray(w, dtype=float)
    good = np.isfinite(ww) & (ww > 0)
    if not (good & m).any():
        return float("nan")
    return float(ww[good & m].sum() / ww[good].sum())


def zip_member(zpath: Path, substr: str) -> str:
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if substr in n and n.lower().endswith(".csv"):
                return n
    raise FileNotFoundError(f"{substr} in {zpath}")


def process_nss_education() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Coaching / medium / prep aggregates from NSS 75 Education (2017-18)."""

    zpath = ROOT / "data/external/mospi/nss_education/2017-18/raw/Data_in_CSV.zip"
    with zipfile.ZipFile(zpath) as z:
        b5n = zip_member(zpath, "Block-5")
        b6n = next(n for n in z.namelist() if "Block 6" in n and n.lower().endswith(".csv"))
        b2n = next(n for n in z.namelist() if "household characteristics" in n and n.lower().endswith(".csv"))
        b7n = next(n for n in z.namelist() if "Block 7" in n and n.lower().endswith(".csv"))

        b5 = pd.read_csv(
            z.open(b5n),
            usecols=[
                "HHID",
                "Sector",
                "State",
                "Age",
                "Medium_instruction",
                "Enrol_basic_course",
                "Institution_type",
                "Taking_pvt_coaching",
                "MULT_Combined",
            ],
            low_memory=False,
        )
        b6 = pd.read_csv(
            z.open(b6n),
            usecols=[
                "HHID",
                "Per_serialno",
                "Private_coaching_amt",
                "Exp_prep_higher_studies_amt",
                "Course_fee_amt",
                "Total_expenditure_amt",
                "MULT_Combined",
            ],
            low_memory=False,
        )
        b2 = pd.read_csv(
            z.open(b2n),
            usecols=["HHID", "Social_group", "Religion"],
            low_memory=False,
        )
        b7 = pd.read_csv(
            z.open(b7n),
            usecols=[
                "Sector",
                "Age",
                "Preparing_higher_last365days",
                "Exp_preparation_amt",
                "MULT_Combined",
            ],
            low_memory=False,
        )

    # Secondary / higher secondary currently attending (codes 10, 11 in this file).
    hs = b5["Enrol_basic_course"].isin([10, 11]).to_numpy()
    coach = b5["Taking_pvt_coaching"].eq(1).to_numpy()
    w = pd.to_numeric(b5["MULT_Combined"], errors="coerce").to_numpy(dtype=float)
    medium = pd.to_numeric(b5["Medium_instruction"], errors="coerce")
    sector = pd.to_numeric(b5["Sector"], errors="coerce")
    inst = pd.to_numeric(b5["Institution_type"], errors="coerce")

    m = b5.loc[hs].merge(b2, on="HHID", how="left")
    sg = pd.to_numeric(m["Social_group"], errors="coerce")
    mw = pd.to_numeric(m["MULT_Combined"], errors="coerce").to_numpy(dtype=float)
    mc = m["Taking_pvt_coaching"].eq(1).to_numpy()

    joint_rows: list[dict] = []

    def add_row(dims: dict, mask: np.ndarray, weights: np.ndarray, coach_mask: np.ndarray) -> None:
        n = int(mask.sum())
        if n < 30:
            return
        ww = weights[mask]
        cc = coach_mask[mask]
        joint_rows.append(
            {
                **dims,
                "n_unweighted": n,
                "n_coached_unweighted": int(cc.sum()),
                "coaching_rate_weighted": wshare(cc, ww),
                "population": "secondary_higher_secondary_attending",
                "source_wave": "nss_education_2017_18",
                "notes": "Enrol_basic_course in {10,11}; Taking_pvt_coaching==1; weight MULT_Combined",
            }
        )

    add_row(
        {"stratum_type": "all", "sector": "all", "social_group": "all", "medium_code": "all", "institution_type": "all"},
        np.ones(len(m), dtype=bool),
        mw,
        mc,
    )
    for code, label in SECTOR_LABELS.items():
        add_row(
            {
                "stratum_type": "sector",
                "sector": label,
                "social_group": "all",
                "medium_code": "all",
                "institution_type": "all",
            },
            pd.to_numeric(m["Sector"], errors="coerce").eq(code).to_numpy(),
            mw,
            mc,
        )
    for code, label in SG_LABELS.items():
        add_row(
            {
                "stratum_type": "social_group",
                "sector": "all",
                "social_group": label,
                "medium_code": "all",
                "institution_type": "all",
            },
            sg.eq(code).to_numpy(),
            mw,
            mc,
        )
    for code, label in SECTOR_LABELS.items():
        for sg_code, sg_label in SG_LABELS.items():
            add_row(
                {
                    "stratum_type": "sector_x_social_group",
                    "sector": label,
                    "social_group": sg_label,
                    "medium_code": "all",
                    "institution_type": "all",
                },
                pd.to_numeric(m["Sector"], errors="coerce").eq(code).to_numpy() & sg.eq(sg_code).to_numpy(),
                mw,
                mc,
            )

    # Medium margins (keep numeric code; attach hindi/english labels when known).
    med_all = pd.to_numeric(m["Medium_instruction"], errors="coerce")
    for code, g in m.groupby(med_all, dropna=True):
        code_i = int(code)
        ww = pd.to_numeric(g["MULT_Combined"], errors="coerce").to_numpy(dtype=float)
        cc = g["Taking_pvt_coaching"].eq(1).to_numpy()
        if len(g) < 30:
            continue
        joint_rows.append(
            {
                "stratum_type": "medium",
                "sector": "all",
                "social_group": "all",
                "medium_code": code_i,
                "medium_label": MEDIUM_LABELS.get(code_i, f"code_{code_i}"),
                "institution_type": "all",
                "n_unweighted": int(len(g)),
                "n_coached_unweighted": int(cc.sum()),
                "coaching_rate_weighted": wshare(cc, ww),
                "population": "secondary_higher_secondary_attending",
                "source_wave": "nss_education_2017_18",
                "notes": "Enrol_basic_course in {10,11}; medium labels hindi=1 english=2 per NSS75 dict",
            }
        )

    for code, label in {1: "govt_like", 2: "local_body_or_aided", 3: "private", 4: "other"}.items():
        add_row(
            {
                "stratum_type": "institution_type",
                "sector": "all",
                "social_group": "all",
                "medium_code": "all",
                "institution_type": label,
            },
            pd.to_numeric(m["Institution_type"], errors="coerce").eq(code).to_numpy(),
            mw,
            mc,
        )

    joints = pd.DataFrame(joint_rows)

    # Expenditure among coached HS (merge B6 on HHID — person join imperfect; use HHID+rough filter).
    # Block 6 is person-level with Per_serialno; Block 5 lacks person serial in our usecols.
    # Use B6 positives among ages 14-20 as prep/coaching spend priors.
    age6 = None
    # Fall back: coaching amount distribution among positive Private_coaching_amt rows.
    pc = pd.to_numeric(b6["Private_coaching_amt"], errors="coerce").to_numpy(dtype=float)
    prep = pd.to_numeric(b6["Exp_prep_higher_studies_amt"], errors="coerce").to_numpy(dtype=float)
    w6 = pd.to_numeric(b6["MULT_Combined"], errors="coerce").to_numpy(dtype=float)
    spend_rows = []
    for name, arr in [("private_coaching_amt", pc), ("exp_prep_higher_studies_amt", prep)]:
        pos = np.isfinite(arr) & (arr > 0) & np.isfinite(w6) & (w6 > 0)
        qs = wquantiles(arr[pos], w6[pos]) if pos.any() else {}
        spend_rows.append(
            {
                "measure": name,
                "population": "currently_attending_with_positive_amount",
                "n_positive_unweighted": int(pos.sum()),
                "share_rows_positive_unweighted": float(np.mean(np.isfinite(arr) & (arr > 0))),
                **{f"{k}": v for k, v in qs.items()},
                "mean_weighted": wmean(arr[pos], w6[pos]) if pos.any() else float("nan"),
                "unit": "INR_academic_year_2017_18",
                "source_wave": "nss_education_2017_18",
                "notes": "Not NEET-specific; prep_higher_studies is closest entrance-prep proxy",
            }
        )
    spend = pd.DataFrame(spend_rows)

    # Block 7: not currently attending, preparing for higher studies (dropper/aspirant proxy).
    age7 = pd.to_numeric(b7["Age"], errors="coerce")
    youth = age7.between(15, 25).to_numpy()
    preparing = b7["Preparing_higher_last365days"].eq(1).to_numpy()
    w7 = pd.to_numeric(b7["MULT_Combined"], errors="coerce").to_numpy(dtype=float)
    exp7 = pd.to_numeric(b7["Exp_preparation_amt"], errors="coerce").to_numpy(dtype=float)
    sector7 = pd.to_numeric(b7["Sector"], errors="coerce")

    aspirant_rows = [
        {
            "stratum_type": "all",
            "sector": "all",
            "age_band": "15_25_not_attending",
            "n_unweighted": int(youth.sum()),
            "preparing_rate_weighted": wshare(preparing[youth], w7[youth]),
            "prep_exp_p50_among_preparing": wquantiles(
                exp7[youth & preparing & (exp7 > 0)],
                w7[youth & preparing & (exp7 > 0)],
            ).get("p50"),
            "prep_exp_p90_among_preparing": wquantiles(
                exp7[youth & preparing & (exp7 > 0)],
                w7[youth & preparing & (exp7 > 0)],
            ).get("p90"),
            "source_wave": "nss_education_2017_18",
            "notes": "Block 7 not-attending; Preparing_higher_last365days; aspirant/dropper proxy",
        }
    ]
    for code, label in SECTOR_LABELS.items():
        mask = youth & sector7.eq(code).to_numpy()
        aspirant_rows.append(
            {
                "stratum_type": "sector",
                "sector": label,
                "age_band": "15_25_not_attending",
                "n_unweighted": int(mask.sum()),
                "preparing_rate_weighted": wshare(preparing[mask], w7[mask]),
                "prep_exp_p50_among_preparing": wquantiles(
                    exp7[mask & preparing & (exp7 > 0)],
                    w7[mask & preparing & (exp7 > 0)],
                ).get("p50"),
                "prep_exp_p90_among_preparing": wquantiles(
                    exp7[mask & preparing & (exp7 > 0)],
                    w7[mask & preparing & (exp7 > 0)],
                ).get("p90"),
                "source_wave": "nss_education_2017_18",
                "notes": "Block 7 not-attending; Preparing_higher_last365days; aspirant/dropper proxy",
            }
        )
    aspirants = pd.DataFrame(aspirant_rows)
    return joints, spend, aspirants


def process_plfs_field_employment() -> pd.DataFrame:
    """Field-specific LFP / employment / unemployment for ages 22-35."""

    zpath = ROOT / "data/external/mospi/plfs/2025/raw/Data_in_CSV.zip"
    member = zip_member(zpath, "cperv12025")
    with zipfile.ZipFile(zpath) as z:
        df = pd.read_csv(
            z.open(member),
            usecols=["age", "sex", "sec", "gedu_lvl", "tedu_lvl", "pas", "ocu_pas", "ern_reg", "ern_self", "mult"],
            low_memory=False,
        )

    age = pd.to_numeric(df["age"], errors="coerce")
    tedu = pd.to_numeric(df["tedu_lvl"], errors="coerce")
    gedu = pd.to_numeric(df["gedu_lvl"], errors="coerce")
    pas = pd.to_numeric(df["pas"], errors="coerce")
    ocu = pd.to_numeric(df["ocu_pas"], errors="coerce")
    w = pd.to_numeric(df["mult"], errors="coerce")
    earn = pd.to_numeric(df["ern_reg"], errors="coerce").fillna(0) + pd.to_numeric(
        df["ern_self"], errors="coerce"
    ).fillna(0)
    sex = pd.to_numeric(df["sex"], errors="coerce")
    sec = pd.to_numeric(df["sec"], errors="coerce")

    in_lf = pas.isin([11, 12, 21, 31, 41, 51, 61, 62, 71, 72, 81, 82])
    employed = pas.isin([11, 12, 21, 31, 41, 51, 61, 62, 71, 72])
    unemployed = pas.isin([81, 82])
    youth = age.between(22, 35)

    fields = {
        "medicine_technical_education": tedu.isin([4, 14]),
        "engineering_technical_education": tedu.isin([3, 13]),
        "graduate_plus_general": gedu >= 11,
        "doctor_nco_221": ocu.eq(221),
        "nurse_nco_222": ocu.eq(222),
        "engineer_nco_21x": ocu.between(210, 219),
        "no_college": (gedu < 11) & age.between(22, 35),
    }

    rows = []
    for field, mask in fields.items():
        for sex_label, sex_mask in [("all", pd.Series(True, index=df.index)), ("male", sex.eq(1)), ("female", sex.eq(2))]:
            for sec_label, sec_mask in [
                ("all", pd.Series(True, index=df.index)),
                ("rural", sec.eq(1)),
                ("urban", sec.eq(2)),
            ]:
                if sex_label != "all" and sec_label != "all":
                    continue  # keep table manageable
                sub = (youth & mask & sex_mask & sec_mask).to_numpy()
                n = int(sub.sum())
                if n < 50:
                    continue
                ww = w.to_numpy(dtype=float)
                lf = in_lf.to_numpy()
                emp = employed.to_numpy()
                unemp = unemployed.to_numpy()
                ey = earn.to_numpy(dtype=float)
                rows.append(
                    {
                        "field": field,
                        "age_band": "22_35",
                        "sex": sex_label,
                        "sector": sec_label,
                        "n_unweighted": n,
                        "lfp_weighted": wshare(lf[sub], ww[sub]),
                        "employment_given_lf_weighted": wshare(emp[sub & lf], ww[sub & lf]),
                        "unemployment_given_lf_weighted": wshare(unemp[sub & lf], ww[sub & lf]),
                        "zero_earnings_share_weighted": wshare(ey[sub] <= 0, ww[sub]),
                        "monthly_earn_p50_if_positive": wquantiles(ey[sub & (ey > 0)], ww[sub & (ey > 0)]).get("p50"),
                        "monthly_earn_p90_if_positive": wquantiles(ey[sub & (ey > 0)], ww[sub & (ey > 0)]).get("p90"),
                        "source_wave": "plfs_2025",
                        "notes": "Usual status PAS; tedu codes 3/13 eng, 4/14 medicine provisional; NCO employed by definition",
                    }
                )
    return pd.DataFrame(rows)


def process_cmse_school_type() -> pd.DataFrame:
    zpath = ROOT / "data/external/mospi/cmse/2025/raw/Data in CSV.zip"
    with zipfile.ZipFile(zpath) as z:
        per = pd.read_csv(z.open("CMSE80PER25.csv"), low_memory=False)
        hh = pd.read_csv(z.open("CMSE80HH25.csv"), low_memory=False)
    keys = ["fsu_serial_no", "second_stage_stratum_no", "sample_hhld_no"]
    m = per.merge(hh[keys + ["social_group"]], on=keys, how="left")
    lvl = pd.to_numeric(m["enrolment_level"], errors="coerce")
    hs = m["currently_enrolled_school"].eq(1) & lvl.isin([10, 11, 12])
    rows = []
    for (stype, sector, sg), g in m.loc[hs].groupby(["school_type", "sector", "social_group"], dropna=False):
        ww = pd.to_numeric(g["mult"], errors="coerce").to_numpy(dtype=float)
        cc = g["received_private_coaching"].eq(1).to_numpy()
        if len(g) < 30:
            continue
        exp = pd.to_numeric(g.loc[g["received_private_coaching"].eq(1), "private_coaching_exp_total"], errors="coerce")
        ew = pd.to_numeric(g.loc[g["received_private_coaching"].eq(1), "mult"], errors="coerce")
        qs = wquantiles(exp.to_numpy(dtype=float), ew.to_numpy(dtype=float)) if len(exp) else {}
        st = int(stype) if pd.notna(stype) else None
        rows.append(
            {
                "school_type": st,
                "school_type_label": SCHOOL_TYPE_LABELS.get(st or -1, "unknown"),
                "sector": SECTOR_LABELS.get(int(sector) if pd.notna(sector) else -1, "unknown"),
                "social_group": SG_LABELS.get(int(sg) if pd.notna(sg) else -1, "unknown"),
                "n_unweighted": int(len(g)),
                "coaching_rate_weighted": wshare(cc, ww),
                "coaching_exp_p50": qs.get("p50"),
                "coaching_exp_p90": qs.get("p90"),
                "source_wave": "cmse_2025",
                "notes": "Class X-XII school tutoring; not NEET-specific",
            }
        )
    # also school-type only margins
    for stype, g in m.loc[hs].groupby("school_type", dropna=False):
        ww = pd.to_numeric(g["mult"], errors="coerce").to_numpy(dtype=float)
        cc = g["received_private_coaching"].eq(1).to_numpy()
        st = int(stype) if pd.notna(stype) else None
        rows.append(
            {
                "school_type": st,
                "school_type_label": SCHOOL_TYPE_LABELS.get(st or -1, "unknown"),
                "sector": "all",
                "social_group": "all",
                "n_unweighted": int(len(g)),
                "coaching_rate_weighted": wshare(cc, ww),
                "coaching_exp_p50": None,
                "coaching_exp_p90": None,
                "source_wave": "cmse_2025",
                "notes": "Class X-XII school tutoring; not NEET-specific",
            }
        )
    return pd.DataFrame(rows)


def write_tus_status(out: Path) -> Path:
    """Document that TUS arrived as Nesstar, not CSV."""

    rows = []
    for wave, rel in [
        ("2024", "data/external/mospi/tus/2024/raw/TUS2024.zip"),
        ("2019", "data/external/mospi/tus/2019/raw/Unit level data of TUS 2019.zip"),
    ]:
        zpath = ROOT / rel
        status = "missing"
        detail = ""
        if zpath.exists():
            with zipfile.ZipFile(zpath) as z:
                names = z.namelist()
                nes = [n for n in names if n.lower().endswith(".nesstar")]
                csvs = [n for n in names if n.lower().endswith(".csv")]
                if nes and not csvs:
                    status = "nesstar_only_needs_conversion"
                    detail = f"entries={names}; magic=NESSTART proprietary"
                elif csvs:
                    status = "csv_available"
                    detail = f"csv_count={len(csvs)}"
                else:
                    status = "unknown_archive"
                    detail = f"entries={names}"
        rows.append(
            {
                "dataset": "tus",
                "wave": wave,
                "local_path": rel.replace("\\", "/"),
                "status": status,
                "detail": detail,
                "model_use": "study_time / unpaid_work opportunity-cost priors for prep arms race",
                "next_action": "Open in Nesstar Explorer or re-download CSV extract from MoSPI if offered",
            }
        )
    path = out / "tus_conversion_status.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    print("NSS Education 2017-18...")
    joints, spend, aspirants = process_nss_education()
    joints.to_csv(out / "nss_education_coaching_joints.csv", index=False)
    spend.to_csv(out / "nss_education_prep_spend.csv", index=False)
    aspirants.to_csv(out / "nss_education_aspirant_prep.csv", index=False)

    print("PLFS field employment...")
    emp = process_plfs_field_employment()
    emp.to_csv(out / "plfs_field_employment.csv", index=False)

    print("CMSE school type...")
    st = process_cmse_school_type()
    st.to_csv(out / "cmse_coaching_by_school_type.csv", index=False)

    print("TUS status...")
    tus_path = write_tus_status(out)

    # Update / merge manifest
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {"output_dir": str(out.relative_to(ROOT)).replace("\\", "/"), "files": [], "model_hooks": {}}
    manifest["files"] = sorted(p.name for p in out.glob("*.csv"))
    manifest["redistribution"] = "aggregates only; unit microdata remain local/gitignored"
    hooks = manifest.setdefault("model_hooks", {})
    hooks.update(
        {
            "coaching_joints_nss": "nss_education_coaching_joints.csv",
            "prep_spend_nss": "nss_education_prep_spend.csv + nss_education_aspirant_prep.csv",
            "field_employment": "plfs_field_employment.csv",
            "coaching_school_type": "cmse_coaching_by_school_type.csv",
            "tus_status": tus_path.name,
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Wrote", out)
    print(json.dumps({"files_added": [
        "nss_education_coaching_joints.csv",
        "nss_education_prep_spend.csv",
        "nss_education_aspirant_prep.csv",
        "plfs_field_employment.csv",
        "cmse_coaching_by_school_type.csv",
        "tus_conversion_status.csv",
    ]}, indent=2))


if __name__ == "__main__":
    main()
