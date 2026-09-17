import pandas as pd

def clean_classes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ClassID"] = df["Identifier"].astype(str).str.strip()
    df["PreferredName"] = df["PreferredName"].astype(str).str.strip()
    df["Definition"] = df["Definition"].fillna("").astype(str).str.strip()
    df["CodedName"] = df["CodedName"].astype(str).str.strip()
    return df


def clean_relations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ClassID"] = df["IdCC"].astype(str).str.strip().str[:-3]
    df["PropID"] = df["IdPR"].astype(str).str.strip().str[:-3]
    return df


def clean_properties(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["PropID"] = df["Identifier"].astype(str).str.strip()
    df["PreferredName"] = df["PreferredName"].astype(str).str.strip()
    return df


def _read_csv(file_source) -> pd.DataFrame:
    if hasattr(file_source, "seek"):
        file_source.seek(0)
    return pd.read_csv(file_source, sep=None, engine="python")


def extract_available_segments(cc_df: pd.DataFrame) -> list:
    if cc_df is None or "CodedName" not in cc_df.columns:
        return []

    segments = (
        cc_df["CodedName"]
        .astype(str)
        .str.strip()
        .str.zfill(8)
        .str[:2]
        .unique()
    )

    valid_segments = sorted([s for s in segments if s and s != "00"])
    return valid_segments


def load_data_from_files(files: dict) -> dict:
    return {
        "cc15": clean_classes(_read_csv(files["cc_old"])),
        "cc16": clean_classes(_read_csv(files["cc_new"])),
        "cc_pr15": clean_relations(_read_csv(files["cc_pr_old"])),
        "cc_pr16": clean_relations(_read_csv(files["cc_pr_new"])),
        "pr15": clean_properties(_read_csv(files["pr_old"])),
        "pr16": clean_properties(_read_csv(files["pr_new"])),
    }