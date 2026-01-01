import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# הגדרות כלליות
# -----------------------------
st.set_page_config(
    page_title="סימולציית הערכת עובדים ותקציב קידום",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# CSS – RTL + עיצוב נקי
# -----------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        direction: rtl;
        text-align: right;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    h1, h2, h3, h4 {
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        gap: 40px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 17px;
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
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 6px rgba(0,0,0,0.04);
    }
    .metric-card {
        background-color: white;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# כותרת
# -----------------------------
st.title("💼 סימולציה אינטליגנטית להערכת עובדים ותקציב קידום")
st.markdown(
    "<p style='text-align:center; color:#666;'>"
    "הקצאת תקציב קידום על בסיס מודל איכות, ספים ואסטרטגיות שונות"
    "</p>",
    unsafe_allow_html=True,
)
st.divider()

# -----------------------------
# פונקציות עזר
# -----------------------------
def get_scale_range(scale_label: str):
    if scale_label == "סולם 1-5":
        return 1, 5
    elif scale_label == "סולם 1-10":
        return 1, 10
    else:
        return 1, 100   # אחוזים 1–100

def normalize_weights(weights: dict):
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: v / total for k, v in weights.items()}

def calculate_weighted_score(row, metrics, norm_weights, min_scale, max_scale):
    """מחזיר ציון בין 0 ל-1 (ניקוד נורמליזציה)."""
    score = 0.0
    for m in metrics:
        raw = row.get(m, 0)
        raw = max(min(raw, max_scale), min_scale)  # קלמפ לסולם
        norm_val = (raw - min_scale) / (max_scale - min_scale) if max_scale > min_scale else 0
        score += norm_val * norm_weights[m]
    return score

def allocate_budget(df, total_budget, method, min_score_threshold=0.6, base_raise_pct=1.0):
    """
    מחלקת תקציב לפי אסטרטגיה:
    method:
        - 'פרופורציונלי לציון'
        - 'רק מעל סף איכות'
        - 'בסיס לכולם + תוספת למצטיינים'
    """
    df = df.copy()
    df["העלאה מוצעת (₪)"] = 0.0

    if total_budget <= 0 or df.empty:
        df["שכר חדש"] = df["שכר בסיס שנתי"]
        df["אחוז העלאה"] = 0.0
        return df

    scores = df["ציון משוקלל"].fillna(0)

    if method == "פרופורציונלי לציון":
        total_scores = scores.sum()
        if total_scores > 0:
            df["העלאה מוצעת (₪)"] = (scores / total_scores) * total_budget

    elif method == "רק מעל סף איכות":
        mask = scores >= min_score_threshold
        eligible_scores = scores[mask]
        total_scores = eligible_scores.sum()
        if total_scores > 0:
            df.loc[mask, "העלאה מוצעת (₪)"] = (
                eligible_scores / total_scores * total_budget
            )
        # מי שמתחת לסף – 0, כברירת מחדל

    elif method == "בסיס לכולם + תוספת למצטיינים":
        # שלב 1 – בסיס אחוזי לכולם
        base_raises = df["שכר בסיס שנתי"] * (base_raise_pct / 100.0)
        base_total = base_raises.sum()
        if base_total > total_budget:
            # אין תקציב אפילו לבסיס – נוריד פרופורציונלית
            factor = total_budget / base_total
            df["העלאה מוצעת (₪)"] = base_raises * factor
        else:
            df["העלאה מוצעת (₪)"] = base_raises
            remaining = total_budget - base_total
            # שלב 2 – מה שנשאר מחולק למצטיינים מעל סף
            mask = scores >= min_score_threshold
            extra_scores = scores[mask]
            total_extra_scores = extra_scores.sum()
            if remaining > 0 and total_extra_scores > 0:
                df.loc[mask, "העלאה מוצעת (₪)"] += (
                    extra_scores / total_extra_scores * remaining
                )

    # חישוב שכר חדש ואחוז העלאה
    df["שכר חדש"] = df["שכר בסיס שנתי"] + df["העלאה מוצעת (₪)"]
    df["אחוז העלאה"] = np.where(
