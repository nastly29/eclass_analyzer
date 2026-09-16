import pandas as pd

def generate_summary_report(
    df_added: pd.DataFrame,
    df_deleted: pd.DataFrame,
    df_internal: pd.DataFrame,
    total_15: int,
    total_16: int,
) -> pd.DataFrame:
    count_added = len(df_added)
    count_deleted = len(df_deleted)

    if not df_internal.empty:
        def_changes = len(
            df_internal[df_internal["Змінено"] == "Definition класу"]
        )

        what_changed = df_internal["Що змінено"].astype(str).str.lower()

        prop_added = len(
            df_internal[what_changed.str.startswith("додано властивість")]
        )
        prop_deleted = len(
            df_internal[what_changed.str.startswith("вилучено властивість")]
        )
        affected_classes = df_internal["ClassID"].nunique()
    else:
        def_changes = prop_added = prop_deleted = affected_classes = 0

    stats = [
        {"Метрика": "Всього класів у попередній версії", "Значення": total_15},
        {"Метрика": "Всього класів в оновленій версії", "Значення": total_16},
        {"Метрика": "Додано нових класів", "Значення": count_added},
        {"Метрика": "Вилучено класів", "Значення": count_deleted},
        {
            "Метрика": "Класів із внутрішніми змінами",
            "Значення": affected_classes,
        },
        {"Метрика": "— з них змінено Definition", "Значення": def_changes},
        {"Метрика": "— додано властивостей", "Значення": prop_added},
        {"Метрика": "— вилучено властивостей", "Значення": prop_deleted},
    ]

    return pd.DataFrame(stats)


def generate_segment_statistics(
    df_added: pd.DataFrame,
    df_deleted: pd.DataFrame,
    df_internal: pd.DataFrame,
) -> pd.DataFrame:
    def extract_segment(df, col_name="CodedName"):
        if df.empty or col_name not in df.columns:
            return pd.Series(dtype=str)
        return (
            df[col_name]
            .astype(str)
            .str.strip()
            .str.zfill(8)
            .str[:2]
            .replace("00", "Невизначено")
        )

    seg_added = (
        extract_segment(df_added, "CodedName")
        .value_counts()
        .rename("Додано нових класів")
    )

    seg_deleted = (
        extract_segment(df_deleted, "CodedName")
        .value_counts()
        .rename("Вилучено класів")
    )

    if not df_internal.empty:
        df_int_copy = df_internal.copy()
        df_int_copy["Segment"] = extract_segment(df_int_copy, "CodedName")

        what_changed = df_int_copy["Що змінено"].astype(str).str.lower()

        seg_affected_classes = (
            df_int_copy.groupby("Segment")["ClassID"]
            .nunique()
            .rename("Змінених класів")
        )

        seg_def_changes = (
            df_int_copy[df_int_copy["Змінено"] == "Definition класу"]
            .groupby("Segment")
            .size()
            .rename("Змін Definition")
        )

        seg_prop_added = (
            df_int_copy[what_changed.str.startswith("додано властивість")]
            .groupby("Segment")
            .size()
            .rename("Додано властивостей")
        )

        seg_prop_deleted = (
            df_int_copy[what_changed.str.startswith("вилучено властивість")]
            .groupby("Segment")
            .size()
            .rename("Вилучено властивостей")
        )
    else:
        seg_affected_classes = pd.Series(dtype=int, name="Змінених класів")
        seg_def_changes = pd.Series(dtype=int, name="Змін Definition")
        seg_prop_added = pd.Series(dtype=int, name="Додано властивостей")
        seg_prop_deleted = pd.Series(dtype=int, name="Вилучено властивостей")

    segment_df = pd.concat(
        [
            seg_added,
            seg_deleted,
            seg_affected_classes,
            seg_def_changes,
            seg_prop_added,
            seg_prop_deleted,
        ],
        axis=1,
    ).fillna(0)

    segment_df = segment_df.astype(int)
    segment_df.index.name = "Сегмент"
    segment_df.reset_index(inplace=True)

    segment_df["Всього подій"] = (
        segment_df["Додано нових класів"]
        + segment_df["Вилучено класів"]
        + segment_df["Змін Definition"]
        + segment_df["Додано властивостей"]
        + segment_df["Вилучено властивостей"]
    )

    return segment_df.sort_values(
        by="Всього подій", ascending=False
    ).reset_index(drop=True)