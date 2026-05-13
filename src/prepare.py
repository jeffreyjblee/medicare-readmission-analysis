import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def load_beneficiary() -> pd.DataFrame:
    """Load and clean all 5 beneficiary samples."""
    print("Loading beneficiary data...")

    files = [
        "DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv",
        "DE1_0_2008_Beneficiary_Summary_File_Sample_2.csv",
        "DE1_0_2008_Beneficiary_Summary_File_Sample_3.csv",
        "DE1_0_2008_Beneficiary_Summary_File_Sample_4.csv",
        "DE1_0_2008_Beneficiary_Summary_File_Sample_5.csv",
    ]

    frames = []
    for f in files:
        df = pd.read_csv(RAW_DIR / f, dtype=str)
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    print(f"  Loaded {len(df):,} beneficiaries from 5 samples")

    # Fix dates
    df["BENE_BIRTH_DT"] = pd.to_datetime(df["BENE_BIRTH_DT"],
                                          format="%Y%m%d", errors="coerce")
    df["BENE_DEATH_DT"] = pd.to_datetime(df["BENE_DEATH_DT"],
                                          format="%Y%m%d", errors="coerce")

    # Derive age as of 2008
    ref = pd.Timestamp("2008-01-01")
    df["AGE"] = ((ref - df["BENE_BIRTH_DT"]).dt.days / 365).fillna(0).astype(int)

    # Decode sex and race
    df["SEX"] = df["BENE_SEX_IDENT_CD"].map({"1": "Male", "2": "Female"}).fillna("Unknown")
    df["RACE"] = df["BENE_RACE_CD"].map({
        "1": "White", "2": "Black", "3": "Other",
        "4": "Asian", "5": "Hispanic", "6": "Native American"
    }).fillna("Unknown")

    # Chronic conditions — 1=yes, 2=no
    cc_map = {
        "SP_ALZHDMTA": "CC_ALZHEIMERS",
        "SP_CHF":      "CC_HEART_FAILURE",
        "SP_CHRNKIDN": "CC_KIDNEY_DISEASE",
        "SP_CNCR":     "CC_CANCER",
        "SP_COPD":     "CC_COPD",
        "SP_DEPRESSN": "CC_DEPRESSION",
        "SP_DIABETES": "CC_DIABETES",
        "SP_ISCHMCHT": "CC_ISCHEMIC_HEART",
        "SP_OSTEOPRS": "CC_OSTEOPOROSIS",
        "SP_RA_OA":    "CC_ARTHRITIS",
        "SP_STRKETIA": "CC_STROKE",
    }
    for raw_col, clean_col in cc_map.items():
        if raw_col in df.columns:
            df[clean_col] = df[raw_col].map({"1": 1, "2": 0}).fillna(0).astype(int)

    cc_cols = list(cc_map.values())
    df["CC_TOTAL"] = df[cc_cols].sum(axis=1)
    df["IS_DECEASED"] = df["BENE_DEATH_DT"].notna().astype(int)

    # Rename and select
    df = df.rename(columns={"DESYNPUF_ID": "PATIENT_ID"})
    keep = ["PATIENT_ID", "AGE", "SEX", "RACE", "IS_DECEASED", "CC_TOTAL"] + cc_cols
    return df[keep]


def load_inpatient() -> pd.DataFrame:
    """Load and clean inpatient claims from all 5 samples."""
    print("Loading inpatient claims...")

    files = [
        "DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv",
        "DE1_0_2008_to_2010_Inpatient_Claims_Sample_2.csv",
        "DE1_0_2008_to_2010_Inpatient_Claims_Sample_3.csv",
        "DE1_0_2008_to_2010_Inpatient_Claims_Sample_4.csv",
        "DE1_0_2008_to_2010_Inpatient_Claims_Sample_5.csv",
    ]

    frames = []
    for f in files:
        path = RAW_DIR / f
        if path.exists():
            df = pd.read_csv(path, dtype=str)
            frames.append(df)
        else:
            print(f"  WARNING: {f} not found — skipping")

    df = pd.concat(frames, ignore_index=True)
    print(f"  Loaded {len(df):,} inpatient claims")

    # Fix dates and payment
    for col in ["CLM_FROM_DT", "CLM_THRU_DT"]:
        df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")

    df["CLM_PMT_AMT"] = pd.to_numeric(df["CLM_PMT_AMT"],
                                       errors="coerce").fillna(0).clip(lower=0)
    df["LENGTH_OF_STAY"] = (df["CLM_THRU_DT"] - df["CLM_FROM_DT"]).dt.days

    df = df.rename(columns={
        "DESYNPUF_ID": "PATIENT_ID",
        "CLM_PMT_AMT": "PAYMENT_AMOUNT"
    })

    return df[["PATIENT_ID", "CLM_FROM_DT", "CLM_THRU_DT",
               "PAYMENT_AMOUNT", "LENGTH_OF_STAY"]].copy()


def build_analysis_dataset() -> pd.DataFrame:
    """
    Join beneficiary demographics to inpatient utilization.
    Creates the final analysis-ready dataset with readmission
    labels and cost features.
    """
    print("\nBuilding analysis dataset...")

    bene = load_beneficiary()
    inpatient = load_inpatient()

    # Aggregate inpatient claims per patient
    claims_agg = inpatient.groupby("PATIENT_ID").agg(
        inpatient_visits=("PAYMENT_AMOUNT", "count"),
        total_inpatient_cost=("PAYMENT_AMOUNT", "sum"),
        avg_length_of_stay=("LENGTH_OF_STAY", "mean"),
        max_length_of_stay=("LENGTH_OF_STAY", "max")
    ).reset_index()

    # Readmission label — more than one admission
    claims_agg["READMITTED"] = (claims_agg["inpatient_visits"] > 1).astype(int)

    # High cost label — top 25% of inpatient spenders
    threshold = claims_agg["total_inpatient_cost"].quantile(0.75)
    claims_agg["HIGH_COST"] = (claims_agg["total_inpatient_cost"] >= threshold).astype(int)

    # Join to beneficiary — only patients with at least one admission
    df = bene.merge(claims_agg, on="PATIENT_ID", how="inner")

    print(f"  Final dataset: {len(df):,} patients with inpatient history")
    print(f"  Readmitted: {df['READMITTED'].sum():,} ({df['READMITTED'].mean()*100:.1f}%)")
    print(f"  High cost:  {df['HIGH_COST'].sum():,} ({df['HIGH_COST'].mean()*100:.1f}%)")

    return df


def run():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_analysis_dataset()
    out = PROCESSED_DIR / "analysis_dataset.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved to {out}")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    run()