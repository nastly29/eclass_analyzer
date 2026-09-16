import pandas as pd
import difflib

def get_added_classes(cc15: pd.DataFrame, cc16: pd.DataFrame) -> pd.DataFrame:
    ids_15 = set(cc15["ClassID"])
    ids_16 = set(cc16["ClassID"])

    added_df = cc16[cc16["ClassID"].isin(ids_16 - ids_15)].copy()

    cols = ["IrdiCC", "ClassID", "CodedName", "PreferredName"]
    avail_cols = [c for c in cols if c in added_df.columns]

    result_df = added_df[avail_cols].copy()
    result_df["Статус"] = "Додано в оновленій версії"

    return result_df


def get_exact_word_diff(old_text: str, new_text: str) -> str:
    if old_text == new_text:
        return "Без істотних змін"

    old_words = str(old_text).split()
    new_words = str(new_text).split()

    matcher = difflib.SequenceMatcher(None, old_words, new_words)
    changes = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            old_part = " ".join(old_words[i1:i2])
            new_part = " ".join(new_words[j1:j2])
            changes.append(f"Замінено: '{old_part}' -> '{new_part}'")
        elif tag == "delete":
            deleted_part = " ".join(old_words[i1:i2])
            changes.append(f"Вилучено: '{deleted_part}'")
        elif tag == "insert":
            added_part = " ".join(new_words[j1:j2])
            changes.append(f"Додано: '{added_part}'")

    return " | ".join(changes) if changes else "Без істотних змін"


def analyze_internal_changes(data: dict) -> pd.DataFrame:
    cc15, cc16 = data["cc15"], data["cc16"]
    cc_pr15, cc_pr16 = data["cc_pr15"], data["cc_pr16"]
    pr15, pr16 = data["pr15"], data["pr16"]

    common_class_ids = set(cc15["ClassID"]).intersection(set(cc16["ClassID"]))

    cc15_map = cc15.set_index("ClassID")
    cc16_map = cc16.set_index("ClassID")
    pr15_names = pr15.set_index("PropID")["PreferredName"].to_dict()
    pr16_names = pr16.set_index("PropID")["PreferredName"].to_dict()
    pr15_grouped = cc_pr15.groupby("ClassID")["PropID"].apply(set).to_dict()
    pr16_grouped = cc_pr16.groupby("ClassID")["PropID"].apply(set).to_dict()

    internal_changes = []

    for class_id in common_class_ids:
        class_name = cc16_map.loc[class_id, "PreferredName"]
        full_irdi = cc16_map.loc[class_id, "IrdiCC"]

        coded_name = (
            cc16_map.loc[class_id, "CodedName"]
            if "CodedName" in cc16_map.columns
            else ""
        )

        def15 = str(cc15_map.loc[class_id, "Definition"])
        def16 = str(cc16_map.loc[class_id, "Definition"])
        if def15 != def16:
            word_diff = get_exact_word_diff(def15, def16)
            internal_changes.append(
                {
                    "ClassID": class_id,
                    "CodedName": coded_name,
                    "IrdiCC": full_irdi,
                    "Назва класу": class_name,
                    "Змінено": "Definition класу",
                    "Що змінено": word_diff,
                }
            )

        props15 = pr15_grouped.get(class_id, set())
        props16 = pr16_grouped.get(class_id, set())

        for prop_id in props16 - props15:
            prop_name = pr16_names.get(prop_id, "Невідома назва")
            internal_changes.append(
                {
                    "ClassID": class_id,
                    "CodedName": coded_name,
                    "IrdiCC": full_irdi,
                    "Назва класу": class_name,
                    "Змінено": "Property (Властивість)",
                    "Що змінено": f"Додано властивість: {prop_id} ({prop_name})",
                }
            )

        for prop_id in props15 - props16:
            prop_name = pr15_names.get(prop_id, "Невідома назва")
            internal_changes.append(
                {
                    "ClassID": class_id,
                    "CodedName": coded_name,
                    "IrdiCC": full_irdi,
                    "Назва класу": class_name,
                    "Змінено": "Property (Властивість)",
                    "Що змінено": f"Вилучено властивість: {prop_id} ({prop_name})",
                }
            )

    return pd.DataFrame(internal_changes)