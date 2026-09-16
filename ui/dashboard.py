import streamlit as st


def render_dashboard(
    summary_df,
    segment_stats_df,
    deleted_mapping_df,
    added_df,
    changes_df,
    similarity_threshold,
):
    st.markdown(
        """
        <style>
        [data-testid="stElementToolbar"] {
            opacity: 1 !important;
            visibility: visible !important;
            display: flex !important;
        }

        /* Стилі для виділених метричних карток */
        .metric-card {
            background-color: #1e222d;
            border: 1px solid #2e3440;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 12px;
        }
        .metric-title {
            font-size: 0.82rem;
            color: #a0aab8;
            margin-bottom: 4px;
            font-weight: 500;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            line-height: 1.2;
        }
        
        /* Колірні акценти */
        .val-neutral { color: #ffffff; }
        .val-added { color: #4caf50; }     /* Зелений */
        .val-deleted { color: #f44336; }   /* Червоний */
        .val-warning { color: #ff9800; }   /* Помаранчевий */
        .val-info { color: #2196f3; }      /* Блакитний */
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Загальна статистика оновлення")

    val_old = val_new = val_added = val_deleted = 0
    val_internal = val_def = val_prop_add = val_prop_del = val_prop_mod = 0

    if not summary_df.empty:
        stats_map = summary_df.set_index("Метрика")["Значення"].to_dict()

        val_old = next(
            (v for k, v in stats_map.items() if "попередн" in k.lower()), 0
        )
        val_new = next(
            (v for k, v in stats_map.items() if "оновлен" in k.lower()), 0
        )

        val_added = stats_map.get("Додано нових класів", 0)
        val_deleted = stats_map.get("Вилучено класів", 0)
        val_internal = stats_map.get("Класів із внутрішніми змінами", 0)

        val_def = stats_map.get("— з них змінено Definition", 0)
        val_prop_add = stats_map.get("— додано властивостей", 0)
        val_prop_del = stats_map.get("— вилучено властивостей", 0)
        val_prop_mod = stats_map.get("— змінено властивостей", 0)

    cols1 = st.columns(4)
    with cols1[0]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Всього у попередній версії</div><div class="metric-value val-neutral">{val_old:,}</div></div>',
            unsafe_allow_html=True,
        )
    with cols1[1]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Всього у новій версії</div><div class="metric-value val-neutral">{val_new:,}</div></div>',
            unsafe_allow_html=True,
        )
    with cols1[2]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Додано класів</div><div class="metric-value val-added">+{val_added:,}</div></div>',
            unsafe_allow_html=True,
        )
    with cols1[3]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Вилучено класів</div><div class="metric-value val-deleted">-{val_deleted:,}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.write("#### Деталізація внутрішніх змін класів")

    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.markdown(
            f"""
            <div class="metric-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
                <div class="metric-title">Класів із змінами</div>
                <div class="metric-value val-neutral">{val_internal:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Змін Definition</div>
                    <div class="metric-value val-info">{val_def:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Додано властивостей</div>
                    <div class="metric-value val-added">+{val_prop_add:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">Вилучено властивостей</div>
                    <div class="metric-value val-deleted">-{val_prop_del:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Статистика за сегментами",
            "Вилучені класи",
            "Додані класи",
            "Внутрішні зміни класів",
            "Завантажити CSV",
        ]
    )

    with tab1:
        st.write("### Статистика за сегментами")
        st.dataframe(segment_stats_df, use_container_width=True)

    with tab2:
        st.write("### Мапінг вилучених класів та їх потенційних замінників")

        sim_col = "Замінник #1 Схожість (%)"
        if sim_col in deleted_mapping_df.columns:
            low_confidence = deleted_mapping_df[
                deleted_mapping_df[sim_col] < similarity_threshold
            ]
            if not low_confidence.empty:
                st.warning(
                    f"Знайдено {len(low_confidence)} класів зі схожістю нижче {similarity_threshold}% (потребують ручної перевірки)."
                )

        st.dataframe(deleted_mapping_df, use_container_width=True)

    with tab3:
        st.write("### Нові класи в оновленій версії")
        st.dataframe(added_df, use_container_width=True)

    with tab4:
        st.write("### Зміни в Definition та властивостях")
        st.dataframe(changes_df, use_container_width=True)

    with tab5:
        st.write("### Експорт всіх готових CSV-звітів")

        st.download_button(
            "Завантажити 'Загальна підсумкова статистика'",
            data=summary_df.to_csv(sep=";", index=False).encode("utf-8-sig"),
            file_name="ECLASS_Summary_Statistics.csv",
            mime="text/csv",
        )

        st.download_button(
            "Завантажити 'Статистика за сегментами'",
            data=segment_stats_df.to_csv(sep=";", index=False).encode("utf-8-sig"),
            file_name="ECLASS_Segment_Statistics.csv",
            mime="text/csv",
        )

        st.download_button(
            "Завантажити 'Додані класи'",
            data=added_df.to_csv(sep=";", index=False).encode("utf-8-sig"),
            file_name="ECLASS_Added_Classes.csv",
            mime="text/csv",
        )

        st.download_button(
            "Завантажити 'Вилучені класи'",
            data=deleted_mapping_df.to_csv(sep=";", index=False).encode("utf-8-sig"),
            file_name="ECLASS_Deleted_Classes_Mapping.csv",
            mime="text/csv",
        )

        st.download_button(
            "Завантажити 'Внутрішні зміни класів'",
            data=changes_df.to_csv(sep=";", index=False).encode("utf-8-sig"),
            file_name="ECLASS_Internal_Changes.csv",
            mime="text/csv",
        )