import streamlit as st
from data.data_loader import load_data_from_files
from services.class_diff_service import (analyze_internal_changes, get_added_classes,)
from services.class_mapper_service import get_deleted_classes_with_mapping
from services.metrics_service import (generate_segment_statistics, generate_summary_report,)
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard

st.set_page_config(
    page_title="ECLASS Diff & Mapping Tool",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Система порівняння та мапінгу ECLASS")
st.caption(
    "Аналіз структурних змін та автоматичне зіставлення вилучених класів між версіями."
)

btn_run, files_uploaded, top_k, similarity_threshold = render_sidebar()

if btn_run:
    status = st.status("Обробка та аналіз даних...", expanded=True)

    status.write("1/5 Нормалізація завантажених CSV-файлів...")
    data = load_data_from_files(files_uploaded)

    status.write("2/5 Визначення доданих класів...")
    added_df = get_added_classes(data["cc15"], data["cc16"])

    status.write("3/5 Визначення та мапінг вилучених класів...")
    progress_bar = status.progress(0, text="Обробка вилучених класів: 0%")

    def update_progress(current, total):
        pct = int((current / total) * 100)
        progress_bar.progress(
            current / total, text=f"Обробка вилучених класів: {pct}%"
        )

    deleted_mapping_df = get_deleted_classes_with_mapping(
        data, top_k=top_k, progress_callback=update_progress
    )

    progress_bar.empty()

    status.write("4/5 Аналіз внутрішніх змін у класах...")
    changes_df = analyze_internal_changes(data)

    status.write("5/5 Формування звітів та підсумкової статистики...")
    summary_df = generate_summary_report(
        added_df,
        deleted_mapping_df,
        changes_df,
        total_15=len(data["cc15"]),
        total_16=len(data["cc16"]),
    )
    segment_stats_df = generate_segment_statistics(
        added_df, deleted_mapping_df, changes_df
    )

    st.session_state["added_df"] = added_df
    st.session_state["deleted_mapping_df"] = deleted_mapping_df
    st.session_state["changes_df"] = changes_df
    st.session_state["summary_df"] = summary_df
    st.session_state["segment_stats_df"] = segment_stats_df
    st.session_state["analysis_done"] = True

    status.update(
        label="Аналіз успішно завершено!", state="complete", expanded=False
    )

    st.rerun()

if st.session_state.get("analysis_done"):
    render_dashboard(
        summary_df=st.session_state["summary_df"],
        segment_stats_df=st.session_state["segment_stats_df"],
        deleted_mapping_df=st.session_state["deleted_mapping_df"],
        added_df=st.session_state["added_df"],
        changes_df=st.session_state["changes_df"],
        similarity_threshold=similarity_threshold,
    )
else:
    st.info(
        "Завантажте необхідні датасети на бічній панелі для запуску аналізу."
    )