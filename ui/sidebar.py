import streamlit as st
import pandas as pd
from data.data_loader import extract_available_segments, _read_csv

def render_sidebar():
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                min-width: 350px;
                max-width: 350px;
            }
            
            [data-testid="stSidebar"][aria-expanded="false"] {
                margin-left: -350px !important;
                visibility: hidden !important;
            }

            [data-testid="stSidebarCollapsedControl"] {
                display: block !important;
                visibility: visible !important;
                z-index: 1000001 !important;
            }

            [data-testid="stFileUploaderDropzone"] {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            
            [data-testid="stFileUploaderDropzone"] > div {
                align-items: center;
                justify-content: center;
            }

            button[aria-label="Add files"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "reset_count" not in st.session_state:
        st.session_state.reset_count = 0

    reset_id = st.session_state.reset_count

    st.sidebar.header("1. Завантаження датасетів")

    with st.sidebar.expander("Попередня версія ECLASS", expanded=True):
        cc_old = st.file_uploader(
            "Класи (CC_en.csv)", type=["csv"], key=f"cc_old_{reset_id}"
        )
        cc_pr_old = st.file_uploader(
            "Зв'язки (CC_PR_en.csv)", type=["csv"], key=f"cc_pr_old_{reset_id}"
        )
        pr_old = st.file_uploader(
            "Властивості (PR_en.csv)", type=["csv"], key=f"pr_old_{reset_id}"
        )

    with st.sidebar.expander("Оновлена версія ECLASS", expanded=True):
        cc_new = st.file_uploader(
            "Класи (CC_en.csv)", type=["csv"], key=f"cc_new_{reset_id}"
        )
        cc_pr_new = st.file_uploader(
            "Зв'язки (CC_PR_en.csv)", type=["csv"], key=f"cc_pr_new_{reset_id}"
        )
        pr_new = st.file_uploader(
            "Властивості (PR_en.csv)", type=["csv"], key=f"pr_new_{reset_id}"
        )

    available_segments = []
    if cc_old is not None:
        try:
            temp_cc15 = _read_csv(cc_old)
            available_segments = extract_available_segments(temp_cc15)
        except Exception:
            available_segments = []

    st.sidebar.header("2. Налаштування аналізу")

    selected_segments = st.sidebar.multiselect(
        "Сегменти для мапінгу:",
        options=available_segments,
        default=[],
        placeholder="Обрати всі сегменти" if available_segments else "Завантажте класи (CC_en.csv)...",
        help="Оберіть конкретні сегменти для пошуку замінників. Якщо залишити порожнім, то мапінг буде виконано для ВСІХ сегментів."
    )

    top_k = st.sidebar.slider(
        "Кількість замінників (Top-K):", 
        1, 5, 3, 
        key=f"top_k_{reset_id}",
        help="Кількість потенційних замінників з нової версії для кожного вилученого класу."
    )

    similarity_threshold = st.sidebar.slider(
        "Поріг схожості для попередження (%):",
        50,
        90,
        75,
        key=f"sim_threshold_{reset_id}",
        help="Мінімальний % схожості. Нижчий результат буде позначено як такий, що потребує перевірки."
    )

    files_uploaded = {
        "cc_old": cc_old,
        "cc_pr_old": cc_pr_old,
        "pr_old": pr_old,
        "cc_new": cc_new,
        "cc_pr_new": cc_pr_new,
        "pr_new": pr_new,
    }

    all_ready = all(files_uploaded.values())

    col1, col2 = st.sidebar.columns([1, 1])

    with col1:
        btn_run = st.button(
            "Проаналізувати",
            type="primary",
            disabled=not all_ready,
            use_container_width=True,
        )

    with col2:
        btn_reset = st.button("Скинути", use_container_width=True)

    if btn_reset:
        st.session_state.reset_count += 1

        for key in list(st.session_state.keys()):
            if key != "reset_count":
                del st.session_state[key]

        st.rerun()

    if not all_ready:
        st.sidebar.info(
            "Завантажте всі 6 CSV-файлів (по 3 для кожної версії) для активації кнопки."
        )

    return btn_run, files_uploaded, top_k, similarity_threshold, selected_segments