import pandas as pd
#import torch
#from config import CACHE_FILE, MODEL_NAME
from config import MODEL_NAME
from sentence_transformers import SentenceTransformer, util

MODEL = SentenceTransformer(MODEL_NAME)

def _build_full_text_with_properties(
    cc_df: pd.DataFrame, cc_pr_df: pd.DataFrame, pr_df: pd.DataFrame
) -> pd.DataFrame:
    df = cc_df.copy()
    pr_names = pr_df.set_index("PropID")["PreferredName"].to_dict()

    cc_pr = cc_pr_df.copy()
    cc_pr["PropName"] = cc_pr["PropID"].map(pr_names).fillna("")

    class_props = (
        cc_pr.groupby("ClassID")["PropName"]
        .apply(lambda names: " ".join(names))
        .to_dict()
    )

    df["PropsText"] = df["ClassID"].map(class_props).fillna("")

    def make_rich_text(row):
        coded = str(row.get("CodedName", "")).strip().zfill(8)
        segment = coded[:2] if len(coded) >= 2 else ""

        name = str(row.get("PreferredName", "")).strip()
        definition = str(row.get("Definition", "")).strip()
        props = str(row.get("PropsText", "")).strip()

        parts = []
        if segment:
            parts.append(f"Segment code: {segment}.")
        parts.append(f"Class name: {name}.")
        if definition:
            parts.append(f"Definition: {definition}.")
        if props:
            parts.append(f"Properties: {props}.")

        return " ".join(parts)

    df["FullText"] = df.apply(make_rich_text, axis=1)
    return df


def get_deleted_classes_with_mapping(
    data: dict, top_k: int = 3, progress_callback=None
) -> pd.DataFrame:
    cc15, cc16 = data["cc15"], data["cc16"]
    cc_pr15, cc_pr16 = data["cc_pr15"], data["cc_pr16"]
    pr15, pr16 = data["pr15"], data["pr16"]

    ids_15 = set(cc15["ClassID"])
    ids_16 = set(cc16["ClassID"])

    deleted_ids = ids_15 - ids_16
    if not deleted_ids:
        return pd.DataFrame()

    cc16_rich = _build_full_text_with_properties(cc16, cc_pr16, pr16)
    cc15_rich = _build_full_text_with_properties(cc15, cc_pr15, pr15)
    deleted_df = cc15_rich[cc15_rich["ClassID"].isin(deleted_ids)].copy()

    if progress_callback:
        progress_callback(10, 100)

    #if CACHE_FILE.exists():
        #embeddings_16 = torch.load(CACHE_FILE)
    #else:
        #embeddings_16 = MODEL.encode(
            #cc16_rich["FullText"].tolist(),
            #convert_to_tensor=True,
            #batch_size=256,
            #show_progress_bar=False,
        #)
        #torch.save(embeddings_16, CACHE_FILE)
    embeddings_16 = MODEL.encode(
        cc16_rich["FullText"].tolist(),
        convert_to_tensor=True,
        batch_size=256,
        show_progress_bar=False,
    ) 
    
    if progress_callback:
        progress_callback(30, 100)

    embeddings_deleted = MODEL.encode(
        deleted_df["FullText"].tolist(),
        convert_to_tensor=True,
        batch_size=128,
        show_progress_bar=False,
    )

    if progress_callback:
        progress_callback(70, 100)

    search_results = util.semantic_search(
        embeddings_deleted, embeddings_16, top_k=top_k
    )

    if progress_callback:
        progress_callback(85, 100)

    results = []
    total_rows = len(deleted_df)

    for idx, (_, del_row) in enumerate(deleted_df.iterrows()):
        top_matches = search_results[idx]

        row_data = {
            "IrdiCC": del_row.get("IrdiCC", ""),
            "ClassID": del_row.get("ClassID", ""),
            "CodedName": del_row.get("CodedName", ""),
            "Назва класу": del_row.get("PreferredName", ""),
            "Статус": "Вилучено в оновленій версії",
        }

        for rank, match in enumerate(top_matches):
            match_idx = match["corpus_id"]
            match_score = match["score"]
            matched_class = cc16_rich.iloc[match_idx]

            row_data[f"Замінник #{rank+1} ID"] = matched_class.get(
                "ClassID", ""
            )
            row_data[f"Замінник #{rank+1} CodedName"] = (
                matched_class.get("CodedName", "")
            )
            row_data[f"Замінник #{rank+1} Назва"] = matched_class.get(
                "PreferredName", ""
            )
            row_data[f"Замінник #{rank+1} Схожість (%)"] = round(
                match_score * 100, 1
            )

        results.append(row_data)

        if progress_callback and total_rows > 0:
            current_pct = 85 + int((idx / total_rows) * 15)
            progress_callback(current_pct, 100)

    return pd.DataFrame(results)