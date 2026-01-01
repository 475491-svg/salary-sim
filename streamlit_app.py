import streamlit as st
import pandas as pd

# -----------------------------
# הגדרות עמוד
# -----------------------------
st.set_page_config(
    page_title="מערכת ניהול שכר וביצועים",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# עיצוב CSS
# -----------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        direction: rtl;
        text-align: right;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    h1 {
        color: #0e1117;
        font-weight: 700;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        gap: 50px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 18px;
        font-weight: 600;
        color: #555;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #1f77b4 !important;
        border-bottom: 2px solid #1f77b4 !important;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #eee;
        box-shadow: 0 3px 6px rgba(0,0,0,0.04);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# פונקציות עזר
# -----------------------------
def get_scale_range(scale_label: str):
    if scale_label == "סולם 1-5":
        return 1, 5
    elif scale_label == "סולם 1-10":
        return 1, 10
    else:
        return 1, 100   # אחוזים 1-100

def normalize_weights(weights: dict):
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: v / total for k, v in weights.items()}

def calculate_weighted_score(row, metrics, norm_weights, min_scale, max_scale):
    score = 0.0
    for m in metrics:
        raw = row.get(m, 0)
        # לוודא שהציון בגבולות הסולם
        raw = max(min(raw, max_scale), min_scale)
        # נורמליזציה ל-0–1
        normalized = (raw - min_scale) / (max_scale - min_scale)
        score += normalized * norm_weights[m]
    return score

# -----------------------------
# כותרת
# -----------------------------
st.title("💼 מערכת סימולציה אינטליגנטית: תקציב קידום")
st.markdown(
    "<p style='text-align: center; color: #666;'>"
    "ניהול ביצועים ותגמול מבוסס נתונים לצוות עובדים"
    "</p>",
    unsafe_allow_html=True
)
st.divider()

# -----------------------------
# טאבים
# -----------------------------
tab1, tab2 = st.tabs(["📊 הערכת מדדי איכות", "📈 סימולציית קידום ותקציב"])

# --------------------------------
# טאב 1 – מודל + נתוני ביצועים
# --------------------------------
with tab1:
    col_config, col_main = st.columns([1, 2.5], gap="large")

    # -------- הגדרות מודל --------
    with col_config:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("⚙️ הגדרות מודל")

        grading_style = st.select_slider(
            "רמת רזולוציית דירוג",
            options=["סולם 1-5", "סולם 1-10", "אחוזים 1-100"],
            value="סולם 1-5"
        )
        min_scale, max_scale = get_scale_range(grading_style)
        st.caption(f"כל ציון צריך להיות בין {min_scale} ל-{max_scale}.")

        metrics_pool = [
            "עמידה ביעדי מחלקה",
            "חדשנות",
            "נוכחות מלאה",
            "ראש גדול",
            "השלמת יעדים אישיים",
            "הערכת מנהל"
        ]
        selected_metrics = st.multiselect(
            "בחירת מדדים פעילים",
            metrics_pool,
            default=metrics_pool[:4]
        )

        st.write("---")
        st.write("**משקולות המדדים (סה\"כ מומלץ ~100%):**")
        weights = {}
        default_weight = 100 // max(len(selected_metrics), 1) if selected_metrics else 0
        for m in selected_metrics:
            weights[m] = st.number_input(
                f"משקל {m} (%)",
                min_value=0,
                max_value=100,
                value=default_weight,
                step=5
            )

        total_weight = sum(weights.values())
        norm_weights = normalize_weights(weights)

        if selected_metrics:
            if 80 <= total_weight <= 120:
                st.success(f"סך המשקולות {total_weight}%. בפועל ננרמל אוטומטית ל-100%.")
            else:
                st.warning(
                    f"סך המשקולות כרגע {total_weight}%. "
                    f"החישוב יתבצע עם נרמול, אבל כדאי לכוון ל-100%."
                )
        else:
            st.info("בחרי לפחות מדד אחד כדי להגדיר מודל.")

        st.markdown("</div>", unsafe_allow_html=True)

    # -------- נתוני עובדים --------
    with col_main:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📋 הזנת נתוני ביצועים לעובדים")

        # סכמת עמודות בסיס
        base_cols = {
            "שם העובד": "",
            "ת.ז": "",
            "שכר בסיס שנתי": 0.0,
        }
        metrics_cols = {m: 0.0 for m in selected_metrics}
        all_cols = {**base_cols, **metrics_cols}

        # אתחול / עדכון טבלת העובדים
        if "employees_df" not in st.session_state:
            st.session_state["employees_df"] = pd.DataFrame([all_cols])
        else:
            df_existing = st.session_state["employees_df"].copy()
            # הוספת עמודות חסרות
            for col, default_val in all_cols.items():
                if col not in df_existing.columns:
                    df_existing[col] = default_val
            # הסרת מדדים שכבר לא נבחרו
            for col in df_existing.columns:
                if col not in all_cols:
                    df_existing.drop(columns=[col], inplace=True)
            st.session_state["employees_df"] = df_existing

        edited_df = st.data_editor(
            st.session_state["employees_df"],
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True
        )
        st.session_state["employees_df"] = edited_df

        if st.button("חשב ציון איכות ושלח לסימולציה", use_container_width=True):
            df = edited_df.copy()

            if df["שם העובד"].replace("", pd.NA).isna().all():
                st.error("יש למלא לפחות עובד אחד עם שם.")
            elif not selected_metrics:
                st.error("יש לבחור לפחות מדד אחד.")
            else:
                df["ציון משוקלל"] = df.apply(
                    lambda row: calculate_weighted_score(
                        row, selected_metrics, norm_weights, min_scale, max_scale
                    ),
                    axis=1
                )
                st.session_state["processed_data"] = df
                st.success("הנתונים עובדו ונשמרו לסימולציה.")
                st.balloons()

        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# טאב 2 – תקציב וקידום
# -----------------------------
with tab2:
    if "processed_data" not in st.session_state:
        st.info("אנא בצעי הערכת עובדים בטאב הראשון כדי לראות את סימולציית התקציב.")
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("💰 ניהול תקציב וקידום שכר")

        df = st.session_state["processed_data"].copy()

        c1, c2, c3 = st.columns(3)
        with c1:
            total_budget = st.number_input(
                "תקציב קידום מחלקתי (₪)",
                value=20000,
                min_value=0,
                step=1000
            )
        with c2:
            st.metric("מספר עובדים", len(df))
        with c3:
            avg_salary = df["שכר בסיס שנתי"].mean() if len(df) else 0
            st.metric("שכר בסיס ממוצע", f"₪{avg_salary:,.0f}")

        # חישוב העלאה יחסית לפי ציון
        if "ציון משוקלל" not in df.columns:
            st.error("לא נמצא 'ציון משוקלל'. חזרי לטאב הראשון וחישבי שוב.")
        else:
            sum_scores = df["ציון משוקלל"].sum()
            if sum_scores > 0:
                df["העלאה מוצעת (₪)"] = (df["ציון משוקלל"] / sum_scores) * total_budget
            else:
                df["העלאה מוצעת (₪)"] = 0.0

            df["שכר חדש"] = df["שכר בסיס שנתי"] + df["העלאה מוצעת (₪)"]
            df["אחוז העלאה"] = df["העלאה מוצעת (₪)"] / df["שכר בסיס שנתי"] * 100

            st.dataframe(
                df[
                    [
                        "שם העובד",
                        "שכר בסיס שנתי",
                        "ציון משוקלל",
                        "העלאה מוצעת (₪)",
                        "שכר חדש",
                        "אחוז העלאה",
                    ]
                ].style.format(
                    {
                        "שכר בסיס שנתי": "₪{:,.0f}",
                        "העלאה מוצעת (₪)": "₪{:,.0f}",
                        "שכר חדש": "₪{:,.0f}",
                        "אחוז העלאה": "{:.1f}%",
                        "ציון משוקלל": "{:.3f}",
                    }
                ),
                use_container_width=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
