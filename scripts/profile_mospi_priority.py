"""Cursory schema + NEET-relevant profiling of MoSPI priority CSVs (streamed from zip)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "mospi_profile"
OUT.mkdir(parents=True, exist_ok=True)


def wmean(x: pd.Series, w: pd.Series) -> float:
    m = x.notna() & w.notna() & (w > 0)
    if not m.any():
        return float("nan")
    return float(np.average(x[m].astype(float), weights=w[m].astype(float)))


def wquantiles(x: pd.Series, w: pd.Series, qs=(0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99)) -> dict:
    m = x.notna() & w.notna() & (w > 0)
    if not m.any():
        return {f"p{int(q*100)}": None for q in qs}
    xv = x[m].astype(float).to_numpy()
    wv = w[m].astype(float).to_numpy()
    order = np.argsort(xv)
    xv, wv = xv[order], wv[order]
    cw = np.cumsum(wv)
    cw = cw / cw[-1]
    out = {}
    for q in qs:
        out[f"p{int(q*100)}"] = float(xv[np.searchsorted(cw, q, side="left").clip(0, len(xv) - 1)])
    return out


def miss_rate(s: pd.Series) -> float:
    return float(s.isna().mean())


def zip_read_csv(zpath: Path, member: str, usecols=None, dtype=None, chunksize=None, nrows=None):
    # Keep ZipFile alive for chunked readers by attaching it to the iterator/dataframe.
    zf = zipfile.ZipFile(zpath)
    f = zf.open(member)
    result = pd.read_csv(
        f, usecols=usecols, dtype=dtype, low_memory=False, chunksize=chunksize, nrows=nrows
    )
    if chunksize is not None:
        result._mospi_zip = zf  # noqa: SLF001 — prevent GC while iterating
    else:
        zf.close()
    return result


def find_member(zpath: Path, substr: str) -> str:
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if substr in n and n.lower().endswith(".csv"):
                return n
    raise FileNotFoundError(substr)


def profile_cmse() -> dict:
    zpath = ROOT / "data/external/mospi/cmse/2025/raw/Data in CSV.zip"
    per = zip_read_csv(zpath, "CMSE80PER25.csv")
    hh = zip_read_csv(zpath, "CMSE80HH25.csv")
    st = zip_read_csv(zpath, "CMSE80PERST25.csv")

    # enrolled students
    enrolled = per["currently_enrolled_school"].eq(1)
    coaching = per["received_private_coaching"].eq(1)
    # Class X–XII (codes 10–12)
    lvl = pd.to_numeric(per["enrolment_level"], errors="coerce")
    hs = enrolled & lvl.isin([10, 11, 12])
    hs_coach = hs & coaching

    w = pd.to_numeric(per["mult"], errors="coerce")
    coach_exp = pd.to_numeric(per["private_coaching_exp_total"], errors="coerce")
    school_exp = pd.to_numeric(per["school_exp_total"], errors="coerce")

    def share(mask_num, mask_den):
        den_w = w[mask_den].sum()
        if den_w <= 0:
            return None
        return float(w[mask_num & mask_den].sum() / den_w)

    # unweighted + weighted coaching rates
    out = {
        "files": {
            "person": {"rows": int(len(per)), "cols": int(per.shape[1])},
            "household": {"rows": int(len(hh)), "cols": int(hh.shape[1])},
            "erstwhile_students": {"rows": int(len(st)), "cols": int(st.shape[1])},
        },
        "person_columns": list(per.columns),
        "missingness_person_key": {
            c: miss_rate(per[c])
            for c in [
                "currently_enrolled_school",
                "enrolment_level",
                "school_type",
                "received_private_coaching",
                "private_coaching_exp_total",
                "school_exp_total",
                "mult",
            ]
        },
        "assumptions": [
            "CMSE covers school education (Class I–XII / diploma up to HS), not college or exam-dropper cohorts.",
            "Private coaching is asked only for currently enrolled school students (and separately for erstwhile/hostel students).",
            "Does not identify NEET-specific coaching; Class XI–XII science coaching is the closest proxy.",
            "Expenditure is for current academic year; use survey weight 'mult'.",
        ],
        "stats": {
            "n_persons": int(len(per)),
            "n_hh": int(len(hh)),
            "n_erstwhile": int(len(st)),
            "enrolled_share_unweighted": float(enrolled.mean()),
            "coaching_among_enrolled_unweighted": float(coaching[enrolled].mean()) if enrolled.any() else None,
            "coaching_among_enrolled_weighted": share(coaching, enrolled),
            "coaching_among_class_xii_weighted": share(coaching & lvl.eq(12), enrolled & lvl.eq(12)),
            "coaching_among_class_x_xii_weighted": share(hs_coach, hs),
            "enrolment_level_counts_unweighted": lvl.value_counts(dropna=False).head(20).to_dict(),
            "class_x_xii_n_unweighted": int(hs.sum()),
            "class_x_xii_coached_n": int(hs_coach.sum()),
            "coaching_exp_among_coached_class_x_xii": {
                "n": int((hs_coach & coach_exp.notna()).sum()),
                **wquantiles(coach_exp[hs_coach], w[hs_coach]),
                "mean_weighted": wmean(coach_exp[hs_coach], w[hs_coach]),
            },
            "school_exp_among_enrolled_class_x_xii": {
                "n": int((hs & school_exp.notna()).sum()),
                **wquantiles(school_exp[hs], w[hs]),
                "mean_weighted": wmean(school_exp[hs], w[hs]),
            },
            "erstwhile_coaching_exp": {
                "n": int(st["private_coaching_expenditure"].notna().sum()),
                **wquantiles(
                    pd.to_numeric(st["private_coaching_expenditure"], errors="coerce"),
                    pd.to_numeric(st["mult"], errors="coerce"),
                ),
            },
            "hh_usual_monthly_consumption": {
                "n": int(hh["usual_monthly_consumption_expenditure"].notna().sum()),
                **wquantiles(
                    pd.to_numeric(hh["usual_monthly_consumption_expenditure"], errors="coerce"),
                    pd.to_numeric(hh["mult"], errors="coerce"),
                ),
            },
            "sector_hh_counts": hh["sector"].value_counts().to_dict(),
            "social_group_hh_counts": hh["social_group"].value_counts().to_dict(),
        },
        "neet_utility": {
            "role": "coaching participation + spend priors among school students (esp. Class X–XII)",
            "strength": "high for tutoring prevalence/cost; low for NEET-specific or repeater coaching",
            "join_keys": "state/sector/social_group/consumption band for synthetic joints with HCES",
        },
    }
    return out


def _plfs2025_chunk_stats(zpath: Path) -> dict:
    member = find_member(zpath, "cperv12025.csv")
    usecols = [
        "sec",
        "st",
        "sex",
        "age",
        "gedu_lvl",
        "tedu_lvl",
        "curr_att",
        "trg",
        "pas",
        "ocu_pas",
        "ind_pas",
        "acws",
        "ocu_cws",
        "ern_reg",
        "ern_self",
        "mult",
        "sg",
        "relg",
    ]
    # sg/relg are on household file; person may not have them — probe first
    with zipfile.ZipFile(zpath) as z:
        header = pd.read_csv(z.open(member), nrows=0)
    cols = [c for c in usecols if c in header.columns]
    # NCO 3-digit: health professionals often 22x; medical doctors ~221; nurses ~222; engineers ~21x
    # Also technical education codes: engineering/technology vs medicine (from PLFS manuals)
    n = 0
    miss = {c: 0 for c in cols}
    tech_counts: dict[str, int] = {}
    pas_counts: dict[str, int] = {}
    ocu_counts: dict[str, int] = {}
    field_buckets = {
        "medicine_tedu": 0,
        "engineering_tedu": 0,
        "other_tech": 0,
        "nco_health_22": 0,
        "nco_doctor_221": 0,
        "nco_nurse_222": 0,
        "nco_engineer_21": 0,
        "graduate_plus": 0,
        "unemployed_usual": 0,
        "in_lf_usual": 0,
        "age_15_29": 0,
        "age_15_29_graduate": 0,
        "age_15_29_graduate_unemployed": 0,
    }
    # earnings collectors
    earn_reg = []
    earn_self = []
    earn_w = []
    earn_ocu = []
    earn_tedu = []

    for chunk in zip_read_csv(zpath, member, usecols=cols, chunksize=200_000):
        n += len(chunk)
        for c in cols:
            miss[c] += int(chunk[c].isna().sum())
        tedu = pd.to_numeric(chunk.get("tedu_lvl"), errors="coerce")
        gedu = pd.to_numeric(chunk.get("gedu_lvl"), errors="coerce")
        age = pd.to_numeric(chunk.get("age"), errors="coerce")
        pas = pd.to_numeric(chunk.get("pas"), errors="coerce")
        ocu = pd.to_numeric(chunk.get("ocu_pas"), errors="coerce")
        w = pd.to_numeric(chunk.get("mult"), errors="coerce")
        ern_reg = pd.to_numeric(chunk.get("ern_reg"), errors="coerce")
        ern_self = pd.to_numeric(chunk.get("ern_self"), errors="coerce")

        # PLFS technical education: common codes include
        # 03 engineering/technology, 04 medicine, etc. (confirm via layout codes; keep raw counts)
        for k, v in tedu.value_counts(dropna=False).items():
            tech_counts[str(k)] = tech_counts.get(str(k), 0) + int(v)
        for k, v in pas.value_counts(dropna=False).head(30).items():
            pas_counts[str(k)] = pas_counts.get(str(k), 0) + int(v)

        # Approximate field buckets — MoSPI tech edu codes typically:
        # 01: no technical; 02: technical degree in agriculture; 03: eng/tech; 04: medicine;
        # 05: crafts; 06: other; diplomas parallel. Keep both exact counts and these labels.
        field_buckets["medicine_tedu"] += int(tedu.isin([4, 14]).sum())  # degree/diploma medicine-ish
        field_buckets["engineering_tedu"] += int(tedu.isin([3, 13]).sum())
        other_tech_mask = tedu.notna() & ~tedu.isin([1, 3, 4, 13, 14]) & (tedu > 1)
        field_buckets["other_tech"] += int(other_tech_mask.sum())

        field_buckets["nco_health_22"] += int(((ocu // 10) == 22).sum())
        field_buckets["nco_doctor_221"] += int((ocu == 221).sum())
        field_buckets["nco_nurse_222"] += int((ocu == 222).sum())
        field_buckets["nco_engineer_21"] += int(((ocu // 10) == 21).sum())

        grad = gedu >= 12  # graduate and above typical PLFS coding starts ~12/13; verify
        # PLFS general education: 01 not literate ... 12 graduate, 13 PG+
        # In recent PLFS: 10 diploma, 11 graduate, 12 PG — codes vary by year. Store raw later.
        age1529 = age.between(15, 29)
        field_buckets["age_15_29"] += int(age1529.sum())
        field_buckets["age_15_29_graduate"] += int((age1529 & (gedu >= 11)).sum())

        # usual status: 11-51 employed-ish, 81 unemployed seeking, 91-97 not in LF
        in_lf = pas.isin([11, 12, 21, 31, 41, 42, 51, 61, 62, 71, 72, 81, 82])
        unemp = pas.isin([81, 82])
        field_buckets["in_lf_usual"] += int(in_lf.sum())
        field_buckets["unemployed_usual"] += int(unemp.sum())
        field_buckets["age_15_29_graduate_unemployed"] += int((age1529 & (gedu >= 11) & unemp).sum())

        # top occupations among earners
        has_earn = ern_reg.fillna(0) + ern_self.fillna(0)
        m = has_earn > 0
        if m.any():
            earn_reg.append(ern_reg[m])
            earn_self.append(ern_self[m])
            earn_w.append(w[m])
            earn_ocu.append(ocu[m])
            earn_tedu.append(tedu[m])
            for k, v in ocu[m].value_counts().head(20).items():
                ocu_counts[str(int(k)) if pd.notna(k) else "nan"] = ocu_counts.get(
                    str(int(k)) if pd.notna(k) else "nan", 0
                ) + int(v)

    miss_rate_map = {c: miss[c] / n for c in cols}

    # Field earnings by NCO family
    ern_reg_s = pd.concat(earn_reg, ignore_index=True) if earn_reg else pd.Series(dtype=float)
    ern_self_s = pd.concat(earn_self, ignore_index=True) if earn_self else pd.Series(dtype=float)
    w_s = pd.concat(earn_w, ignore_index=True) if earn_w else pd.Series(dtype=float)
    ocu_s = pd.concat(earn_ocu, ignore_index=True) if earn_ocu else pd.Series(dtype=float)
    total_earn = ern_reg_s.fillna(0) + ern_self_s.fillna(0)

    def earn_for(mask):
        if not mask.any():
            return {"n": 0}
        return {
            "n": int(mask.sum()),
            "monthly_earn_reg_self_sum": {
                **wquantiles(total_earn[mask], w_s[mask]),
                "mean_weighted": wmean(total_earn[mask], w_s[mask]),
            },
        }

    field_earn = {
        "nco_doctor_221": earn_for(ocu_s == 221),
        "nco_nurse_222": earn_for(ocu_s == 222),
        "nco_health_22x": earn_for((ocu_s // 10) == 22),
        "nco_engineer_21x": earn_for((ocu_s // 10) == 21),
        "all_positive_earners": earn_for(total_earn > 0),
    }

    hh_member = find_member(zpath, "chhv12025.csv")
    hh_cols = ["sec", "st", "hh_size", "hhtype", "relg", "sg", "hce_tot", "inc_tot", "mult"]
    with zipfile.ZipFile(zpath) as z:
        hh_header = list(pd.read_csv(z.open(hh_member), nrows=0).columns)
    hh = zip_read_csv(zpath, hh_member, usecols=[c for c in hh_cols if c in hh_header])
    return {
        "person_rows": n,
        "person_cols_used": cols,
        "missingness": miss_rate_map,
        "tedu_lvl_value_counts_unweighted": dict(sorted(tech_counts.items(), key=lambda kv: -kv[1])[:40]),
        "pas_top_unweighted": dict(sorted(pas_counts.items(), key=lambda kv: -kv[1])[:25]),
        "field_buckets_unweighted": field_buckets,
        "field_earnings_among_positive_earners": field_earn,
        "hh_rows": int(len(hh)),
        "hh_hce_tot": {
            **wquantiles(pd.to_numeric(hh["hce_tot"], errors="coerce"), pd.to_numeric(hh["mult"], errors="coerce")),
            "mean_weighted": wmean(pd.to_numeric(hh["hce_tot"], errors="coerce"), pd.to_numeric(hh["mult"], errors="coerce")),
        },
        "hh_inc_tot": {
            **wquantiles(pd.to_numeric(hh["inc_tot"], errors="coerce"), pd.to_numeric(hh["mult"], errors="coerce")),
            "mean_weighted": wmean(pd.to_numeric(hh["inc_tot"], errors="coerce"), pd.to_numeric(hh["mult"], errors="coerce")),
            "missing_share": miss_rate(hh["inc_tot"]),
        },
        "assumptions": [
            "PLFS 2025 is the revamped calendar-year design; do not pool naively with 2023-24.",
            "Usual principal activity status (pas) and CWS earnings (ern_reg/ern_self) are the main labor outcomes.",
            "NCO-2015 3-digit used for occupation families; rare occupations need pooling.",
            "Technical education codes need codebook confirmation before labeling medicine vs engineering.",
            "Weights: use 'mult' (subsample multiplier); apply NSC/NSS rules from estimation note for official estimates.",
        ],
    }


def profile_plfs_2023_24() -> dict:
    zpath = ROOT / "data/external/mospi/plfs/2023-24/raw/CSV_data_PLFS_2023_2024.zip"
    member = find_member(zpath, "perv1.csv")
    with zipfile.ZipFile(zpath) as z:
        header = list(pd.read_csv(z.open(member), nrows=0).columns)

    # Map questionnaire cols from observed header
    # b4q8=gedu, b4q9=tedu, b4q5=age, b4q4=sex, b5pt1q3=pas, b5pt1q6=ocu, earnings near end
    candidates = {
        "state": next(c for c in header if c.startswith("state_")),
        "sex": "b4q5_perv1" if "b4q5_perv1" in header else None,
        "age": "b4q6_perv1" if "b4q6_perv1" in header else None,
        "gedu": "b4q8_perv1" if "b4q8_perv1" in header else None,
        "tedu": "b4q9_perv1" if "b4q9_perv1" in header else None,
        "pas": "b5pt1q3_perv1" if "b5pt1q3_perv1" in header else None,
        "ocu": "b5pt1q6_perv1" if "b5pt1q6_perv1" in header else None,
        "ind": "b5pt1q5_perv1" if "b5pt1q5_perv1" in header else None,
        "mult": "mult_perv1" if "mult_perv1" in header else next(c for c in header if c.startswith("mult")),
    }
    # CWS earnings: b6q9 = regular salaried/wage; b6q10 = self-employed (layout Field_Name ern_reg/ern_self)
    tail = header[-15:]
    candidates["ern_reg"] = "b6q9_perv1" if "b6q9_perv1" in header else None
    candidates["ern_self"] = "b6q10_perv1" if "b6q10_perv1" in header else None
    candidates["acws"] = "b6q5_perv1" if "b6q5_perv1" in header else None
    usecols = [c for c in candidates.values() if c]
    usecols = list(dict.fromkeys(usecols))
    ern_cols = [c for c in (candidates.get("ern_reg"), candidates.get("ern_self")) if c]

    n = 0
    miss = {c: 0 for c in usecols}
    tedu_counts: dict[str, int] = {}
    gedu_counts: dict[str, int] = {}
    buckets = {
        "medicine_tedu_3_4_13_14": 0,
        "engineering_tedu_3_13": 0,
        "nco_221": 0,
        "nco_222": 0,
        "nco_22x": 0,
        "nco_21x": 0,
        "age_15_29": 0,
        "age_15_29_gedu_ge_11": 0,
        "unemp_81_82": 0,
        "in_lf": 0,
    }
    ocu_col = candidates.get("ocu")
    age_col = candidates.get("age")
    gedu_col = candidates.get("gedu")
    tedu_col = candidates.get("tedu")
    pas_col = candidates.get("pas")
    mult_col = candidates.get("mult")

    earn_frames = []

    for chunk in zip_read_csv(zpath, member, usecols=usecols, chunksize=200_000):
        n += len(chunk)
        for c in usecols:
            miss[c] += int(chunk[c].isna().sum())
        if tedu_col:
            for k, v in chunk[tedu_col].value_counts(dropna=False).items():
                tedu_counts[str(k)] = tedu_counts.get(str(k), 0) + int(v)
        if gedu_col:
            for k, v in chunk[gedu_col].value_counts(dropna=False).items():
                gedu_counts[str(k)] = gedu_counts.get(str(k), 0) + int(v)
        age = pd.to_numeric(chunk[age_col], errors="coerce") if age_col else pd.Series(np.nan, index=chunk.index)
        gedu = pd.to_numeric(chunk[gedu_col], errors="coerce") if gedu_col else pd.Series(np.nan, index=chunk.index)
        tedu = pd.to_numeric(chunk[tedu_col], errors="coerce") if tedu_col else pd.Series(np.nan, index=chunk.index)
        pas = pd.to_numeric(chunk[pas_col], errors="coerce") if pas_col else pd.Series(np.nan, index=chunk.index)
        ocu = pd.to_numeric(chunk[ocu_col], errors="coerce") if ocu_col else pd.Series(np.nan, index=chunk.index)
        w = pd.to_numeric(chunk[mult_col], errors="coerce") if mult_col else pd.Series(np.nan, index=chunk.index)

        buckets["medicine_tedu_3_4_13_14"] += int(tedu.isin([4, 14]).sum())
        buckets["engineering_tedu_3_13"] += int(tedu.isin([3, 13]).sum())
        buckets["nco_221"] += int((ocu == 221).sum())
        buckets["nco_222"] += int((ocu == 222).sum())
        buckets["nco_22x"] += int(((ocu // 10) == 22).sum())
        buckets["nco_21x"] += int(((ocu // 10) == 21).sum())
        a = age.between(15, 29)
        buckets["age_15_29"] += int(a.sum())
        buckets["age_15_29_gedu_ge_11"] += int((a & (gedu >= 11)).sum())
        buckets["unemp_81_82"] += int(pas.isin([81, 82]).sum())
        buckets["in_lf"] += int(pas.isin([11, 12, 21, 31, 41, 42, 51, 61, 62, 71, 72, 81, 82]).sum())

        if ern_cols:
            sub = chunk[[c for c in ern_cols if c in chunk.columns]].apply(pd.to_numeric, errors="coerce")
            total = sub.fillna(0).sum(axis=1)
            m = total > 0
            if m.any():
                earn_frames.append(
                    pd.DataFrame(
                        {
                            "earn": total[m],
                            "w": w[m],
                            "ocu": ocu[m],
                            "tedu": tedu[m],
                        }
                    )
                )

    earn = pd.concat(earn_frames, ignore_index=True) if earn_frames else pd.DataFrame()

    def earn_for(mask):
        if earn.empty or not mask.any():
            return {"n": 0}
        return {
            "n": int(mask.sum()),
            **wquantiles(earn.loc[mask, "earn"], earn.loc[mask, "w"]),
            "mean_weighted": wmean(earn.loc[mask, "earn"], earn.loc[mask, "w"]),
        }

    return {
        "person_rows_visit1": n,
        "columns_total": len(header),
        "column_map_guess": candidates,
        "earnings_columns_detected": ern_cols,
        "sample_tail_columns": tail,
        "sample_head_columns": header[:20],
        "missingness": {c: miss[c] / n for c in usecols},
        "tedu_value_counts": dict(sorted(tedu_counts.items(), key=lambda kv: -kv[1])[:30]),
        "gedu_value_counts": dict(sorted(gedu_counts.items(), key=lambda kv: -kv[1])[:30]),
        "field_buckets_unweighted": buckets,
        "earnings_by_nco": {
            "doctor_221": earn_for(earn["ocu"] == 221) if not earn.empty else {"n": 0},
            "nurse_222": earn_for(earn["ocu"] == 222) if not earn.empty else {"n": 0},
            "health_22x": earn_for((earn["ocu"] // 10) == 22) if not earn.empty else {"n": 0},
            "engineer_21x": earn_for((earn["ocu"] // 10) == 21) if not earn.empty else {"n": 0},
            "all_positive": earn_for(earn["earn"] > 0) if not earn.empty else {"n": 0},
        },
        "files_in_zip": [
            "hhv1.csv",
            "hhrv.csv",
            "perv1.csv",
            "perrv.csv",
        ],
        "assumptions": [
            "Visit-1 person file (perv1) is the primary annual cross-section; perrv is revisit.",
            "CSV headers are questionnaire codes (b4q*, b5pt1q*), not layout Field_Name aliases.",
            "Keep separate from PLFS 2025 revamp for any pooled modeling.",
        ],
    }


def profile_hces() -> dict:
    zpath = ROOT / "data/external/mospi/hces/2023-24/raw/HCES_Data_2023-24_Csv.zip"
    lvl01 = find_member(zpath, "LEVEL - 01")
    lvl02 = find_member(zpath, "LEVEL - 02")
    lvl03 = find_member(zpath, "LEVEL - 03.csv")
    lvl13 = find_member(zpath, "Level - 13")
    lvl15 = find_member(zpath, "LEVEL - 15")

    # household identity / weights
    hh = zip_read_csv(zpath, lvl01)
    char = zip_read_csv(zpath, lvl03)
    # person demographics
    # stream level 02 for education counts only
    edu_counts: dict[str, int] = {}
    n_persons = 0
    age_1529 = 0
    for chunk in zip_read_csv(
        zpath,
        lvl02,
        usecols=["Age", "Gender", "Education_Level", "Multiplier"],
        chunksize=300_000,
    ):
        n_persons += len(chunk)
        age = pd.to_numeric(chunk["Age"], errors="coerce")
        age_1529 += int(age.between(15, 29).sum())
        for k, v in chunk["Education_Level"].value_counts(dropna=False).items():
            edu_counts[str(k)] = edu_counts.get(str(k), 0) + int(v)

    # Level 15 has MONTHLY_CONSUMPTION_EXP + HOUSEHOLD_SIZE — best MPCE proxy without full item aggregation
    l15 = zip_read_csv(
        zpath,
        lvl15,
        usecols=["Sector", "State", "MONTHLY_CONSUMPTION_EXP", "HOUSEHOLD_SIZE", "MULTIPLIER", "SECTION", "VISIT"],
    )
    # Level 13 = durables (Section 14): TOTAL_EXPENDITURE by ITEM_CODE
    item_freq: dict[str, int] = {}
    n_l13 = 0
    durable_tot = []
    for chunk in zip_read_csv(
        zpath,
        lvl13,
        usecols=["ITEM_CODE", "TOTAL_EXPENDITURE", "MULTIPLIER"],
        chunksize=400_000,
    ):
        n_l13 += len(chunk)
        for k, v in chunk["ITEM_CODE"].value_counts(dropna=False).items():
            item_freq[str(k)] = item_freq.get(str(k), 0) + int(v)
        # household total durable spend rows where item is a subtotal if present; else keep raw
        val = pd.to_numeric(chunk["TOTAL_EXPENDITURE"], errors="coerce")
        w13 = pd.to_numeric(chunk["MULTIPLIER"], errors="coerce")
        m = val.notna() & (val > 0)
        if m.any():
            durable_tot.append(pd.DataFrame({"v": val[m], "w": w13[m]}))
    top_items = dict(sorted(item_freq.items(), key=lambda kv: -kv[1])[:40])
    durable_df = pd.concat(durable_tot, ignore_index=True) if durable_tot else pd.DataFrame()

    mce = pd.to_numeric(l15["MONTHLY_CONSUMPTION_EXP"], errors="coerce")
    hsz = pd.to_numeric(l15["HOUSEHOLD_SIZE"], errors="coerce")
    w = pd.to_numeric(l15["MULTIPLIER"], errors="coerce")
    mpce = mce / hsz.replace(0, np.nan)

    # social group from level 03
    sg = char["Social_Group_of_HH_Head"]
    rel = char["Religion_of_HH_Head"]

    return {
        "files": {
            "levels": 15,
            "lvl01_hh_rows": int(len(hh)),
            "lvl02_person_rows": n_persons,
            "lvl03_hh_char_rows": int(len(char)),
            "lvl13_item_rows": n_l13,
            "lvl15_rows": int(len(l15)),
        },
        "key_schemas": {
            "lvl01": list(hh.columns),
            "lvl03": list(char.columns),
            "lvl15": list(l15.columns),
        },
        "missingness": {
            "lvl15_MONTHLY_CONSUMPTION_EXP": miss_rate(l15["MONTHLY_CONSUMPTION_EXP"]),
            "lvl15_HOUSEHOLD_SIZE": miss_rate(l15["HOUSEHOLD_SIZE"]),
            "lvl03_Social_Group": miss_rate(char["Social_Group_of_HH_Head"]),
            "lvl03_NCO": miss_rate(char["NCO_2015_Code"]),
        },
        "stats": {
            "persons_age_15_29_unweighted": age_1529,
            "education_level_person_counts": dict(sorted(edu_counts.items(), key=lambda kv: -kv[1])[:25]),
            "hh_sector_counts": hh["Sector"].value_counts().to_dict(),
            "social_group_counts": sg.value_counts(dropna=False).to_dict(),
            "religion_counts": rel.value_counts(dropna=False).to_dict(),
            "monthly_consumption_exp_hh": {
                **wquantiles(mce, w),
                "mean_weighted": wmean(mce, w),
            },
            "mpce_proxy_mce_over_hhsize": {
                **wquantiles(mpce, w),
                "mean_weighted": wmean(mpce, w),
            },
            "lvl13_top_item_codes": top_items,
            "lvl13_positive_expenditure_rows": {
                **(
                    {
                        **wquantiles(durable_df["v"], durable_df["w"]),
                        "mean_weighted": wmean(durable_df["v"], durable_df["w"]),
                        "n": int(len(durable_df)),
                    }
                    if not durable_df.empty
                    else {"n": 0}
                )
            },
        },
        "assumptions": [
            "HCES measures consumption, not income or wealth.",
            "MONTHLY_CONSUMPTION_EXP on Level 15 is a household summary field; confirm against official MPCE construction before publication.",
            "Item-level files (Levels 05–13) are long-form; education/tuition items need item-code mapping from schedule.",
            "Use Multiplier with subsample/estimation procedure from MoSPI note.",
        ],
        "neet_utility": {
            "role": "household resource rank / affordability / coaching burden denominator",
            "strength": "critical for synthetic household generator",
        },
    }


def profile_aidis() -> dict:
    zpath = ROOT / "data/external/mospi/aidis/2019/raw/CSV_DI_77.zip"
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]

    def get(substr: str) -> str:
        for n in names:
            if substr in n:
                return n
        raise FileNotFoundError(substr)

    hh = zip_read_csv(zpath, get("Visit1  Level - 01"))
    dem = zip_read_csv(zpath, get("Visit1  Level - 02"))
    char = zip_read_csv(zpath, get("Visit1  Level - 03"))
    debt = zip_read_csv(zpath, get("Visit1_Level_14_Block_12.csv"))
    # financial assets
    fin = zip_read_csv(zpath, get("Level - 12 (Block 11a)"))

    # Block 12 debt: b12q1 item/loan serial, amounts in later q fields — inspect non-null rates
    debt_num = debt[[c for c in debt.columns if c.startswith("b12")]].apply(pd.to_numeric, errors="coerce")
    w = pd.to_numeric(debt["MLT"], errors="coerce")

    # Outstanding amount often one of the later columns; take row-wise max of positive numeric fields as rough debt size
    debt_amt_candidates = [c for c in debt_num.columns if debt_num[c].gt(0).mean() > 0.01]
    # Prefer columns with larger typical magnitudes (loan amounts vs codes)
    col_scores = {
        c: float(debt_num[c].quantile(0.9)) for c in debt_amt_candidates
    }
    likely_amt_cols = sorted(col_scores, key=col_scores.get, reverse=True)[:5]

    # Household-level: any debt record
    n_hh = hh["HHID"].nunique()
    hh_with_debt = debt["HHID"].nunique()

    # Aggregate rough outstanding using best candidate column
    best = likely_amt_cols[0] if likely_amt_cols else None
    debt_stats = {}
    if best:
        amt = debt_num[best]
        # household sum
        g = debt.groupby("HHID")[best].sum(min_count=1)
        # attach weight from first debt row
        ww = debt.groupby("HHID")["MLT"].first()
        debt_stats = {
            "amount_column_guess": best,
            "amount_column_candidates": likely_amt_cols,
            "loan_rows": int(len(debt)),
            "hh_with_any_debt_row": int(hh_with_debt),
            "share_hh_with_debt_row_unweighted": hh_with_debt / n_hh if n_hh else None,
            "hh_total_debt_guess": {
                **wquantiles(g, ww),
                "mean_weighted": wmean(g, ww),
            },
        }

    fin_num = fin[[c for c in fin.columns if c.startswith("b11") or c.startswith("b1")]].apply(
        pd.to_numeric, errors="coerce"
    )
    fin_cols = sorted(
        ((c, float(fin_num[c].quantile(0.9))) for c in fin_num.columns if fin_num[c].gt(0).mean() > 0.01),
        key=lambda kv: -kv[1],
    )[:8]

    # demographics age for NEET-relevant household presence
    # b3q5 often age in AIDIS block 3
    age = pd.to_numeric(dem.get("b3q5"), errors="coerce")
    return {
        "files_n": len(names),
        "file_list_short": [Path(n).name[:90] for n in names],
        "hh_rows_visit1": int(len(hh)),
        "unique_hh": int(n_hh),
        "person_rows": int(len(dem)),
        "persons_age_15_29": int(age.between(15, 29).sum()) if age is not None else None,
        "missingness_hh": {
            "MLT": miss_rate(hh["MLT"]),
            "Sector": miss_rate(hh["Sector"]),
            "State": miss_rate(hh["State"]),
        },
        "debt": debt_stats,
        "financial_asset_column_candidates": [c for c, _ in fin_cols],
        "char_columns": list(char.columns),
        "debt_columns": list(debt.columns),
        "assumptions": [
            "AIDIS 2019 is a household balance-sheet cross-section (Visit 1 assets/debt; Visit 2 transactions).",
            "Not linked to NEET candidates; use for wealth/debt percentiles and catastrophic financing priors.",
            "Block 12 variable labels are codes (b12q*); map via schedule before interpreting purpose/source.",
            "Values are as-of survey date in 2019 INR; inflate carefully to NEET-year rupees.",
        ],
        "neet_utility": {
            "role": "private-seat / coaching financing capacity, debt burden, asset percentiles",
            "strength": "high for wealth/debt margins; no education-outcome link",
        },
    }


def main():
    print("Profiling CMSE...")
    cmse = profile_cmse()
    (OUT / "cmse_2025.json").write_text(json.dumps(cmse, indent=2), encoding="utf-8")
    print("  done", cmse["files"])

    print("Profiling PLFS 2025 (chunked)...")
    plfs25 = _plfs2025_chunk_stats(ROOT / "data/external/mospi/plfs/2025/raw/Data_in_CSV.zip")
    (OUT / "plfs_2025.json").write_text(json.dumps(plfs25, indent=2), encoding="utf-8")
    print("  persons", plfs25["person_rows"])

    print("Profiling PLFS 2023-24 (chunked)...")
    plfs2324 = profile_plfs_2023_24()
    (OUT / "plfs_2023_24.json").write_text(json.dumps(plfs2324, indent=2), encoding="utf-8")
    print("  persons", plfs2324["person_rows_visit1"])

    print("Profiling HCES (selected levels)...")
    hces = profile_hces()
    (OUT / "hces_2023_24.json").write_text(json.dumps(hces, indent=2), encoding="utf-8")
    print("  hh", hces["files"]["lvl01_hh_rows"])

    print("Profiling AIDIS...")
    aidis = profile_aidis()
    (OUT / "aidis_2019.json").write_text(json.dumps(aidis, indent=2), encoding="utf-8")
    print("  hh", aidis["unique_hh"])

    summary = {
        "cmse": {
            "rows": cmse["files"],
            "coaching_class_x_xii_weighted": cmse["stats"]["coaching_among_class_x_xii_weighted"],
            "coaching_exp_p50": cmse["stats"]["coaching_exp_among_coached_class_x_xii"].get("p50"),
        },
        "plfs_2025": {
            "person_rows": plfs25["person_rows"],
            "buckets": plfs25["field_buckets_unweighted"],
            "doctor_earn_n": plfs25["field_earnings_among_positive_earners"]["nco_doctor_221"].get("n"),
        },
        "plfs_2023_24": {
            "person_rows": plfs2324["person_rows_visit1"],
            "buckets": plfs2324["field_buckets_unweighted"],
        },
        "hces": {
            "hh": hces["files"]["lvl01_hh_rows"],
            "mpce_p50": hces["stats"]["mpce_proxy_mce_over_hhsize"].get("p50"),
        },
        "aidis": {
            "hh": aidis["unique_hh"],
            "debt_share_hh": aidis["debt"].get("share_hh_with_debt_row_unweighted"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
