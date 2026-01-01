import streamlit as st
import pandas as pd

# הגדרות עמוד ופריסה מלאה
st.set_page_config(page_title="מערכת ניהול שכר וביצועים", layout="wide", initial_sidebar_state="collapsed")

# עיצוב CSS ברמה גבוהה - מראה מודרני ונקי
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e1e4e8; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    h1 { color: #0e1117; font-family: 'Inter', sans-serif; font-weight: 700; text-align: center; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 50px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { font-size: 18px; font-weight: 600; color: #555; border-bottom: 2px solid transparent; }
    .stTabs [aria-selected="true"] { color: #1f77b4 !important; border-bottom: 2px solid #1f77b4 !important; }
    .card { background-color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# כותרת האפליקציה
st.title("💼 מערכת סימולציה אינטליגנטית: תקציב קידום")
st.markdown("<p style='text-align: center; color: #666;'>ניהול ביצועים ותגמול מבוסס נתונים</p>", unsafe_allow_html=True)
st.divider()

# יצירת הטאבים (מסכים)
tab1, tab2 = st.tabs(["📊 הערכת מדדי איכות", "📈 סימולציית קידום ותקציב"])

# --- טאב 1: הערכת עובדים ---
with tab1:
    col_config, col_main = st.columns([1, 2.5], gap="large")
    
    with col_config:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("⚙️ הגדרות מודל")
        grading_style = st.select_slider("רמת רזולוציית דירוג", options=["סולם 1-5", "סולם 1-10", "אחוזים 1-100"])
        
        metrics_pool = ["עמידה ביעדי מחלקה", "חדשנות", "נוכחות מלאה", "ראש גדול", "השלמת יעדים אישיים", "הערכת מנהל"]
        selected = st.multiselect("בחירת מדדים פעילים", metrics_pool, default=metrics_pool[:4])
        
        st.write("---")
        st.write("**משקולות המדדים (סה\"כ 100%):**")
        weights = {}
        for m in selected:
            weights[m] = st.number_input(f"משקל {m} (%)", 0, 100, 100 // len(selected))
        
        if sum(weights.values()) != 100:
            st.error(f"שגיאה: סך המשקולות עומד על {sum(weights.values())}%")
        else:
            st.success("מודל המשקולות מאוזן")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_main:
        st.subheader("📋 הזנת נתוני ביצועים")
        
        # נתוני מנוחה רחל סבן שחולצו מהמסמכים
        data = {
            "שם העובד": ["מנוחה רחל סבן"],
            "ת.ז": ["313511024"], # [cite: 8, 32, 67, 88, 109, 219, 240, 264]
            "שכר בסיס שנתי": [111972], # [cite: 72]
            "הפקדות קופ\"ג": [10333], # [cite: 94]
            "מעסיק": ["משרד החינוך"] # [cite: 71, 92]
        }
        
        df = pd.DataFrame(data)
        for m in selected:
            df[m] = 0.0 # אתחול ציונים
            
        edited_df = st.data_editor(df, use_container_width=True, hide_index=True)
        
        if st.button("חשב ציון איכות ושלח לסימולציה"):
            # לוגיקת חישוב
            def calculate(row):
                return sum(row[m] * (weights[m]/100) for m in selected)
            
            edited_df['ציון משוקלל'] = edited_df.apply(calculate, axis=1)
            st.session_state['processed_data'] = edited_df
            st.toast("הנתונים עובדו בהצלחה", icon="✅")
            st.balloons()

# --- טאב 2: תקציב ---
with tab2:
    if 'processed_data' not in st.session_state:
        st.info("אנא בצעי הערכת עובדים בטאב הראשון כדי לראות את סימולציית התקציב.")
    else:
        st.subheader("💰 ניהול תקציב וקידום שכר")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            total_budget = st.number_input("תקציב קידום מחלקתי (₪)", value=20000)
        with c2:
            st.metric("מספר עובדים", len(st.session_state['processed_data']))
        with c3:
            st.metric("שכר בסיס ממוצע", f"₪{st.session_state['processed_data']['שכר בסיס שנתי'].mean():,.0f}")

        final_df = st.session_state['processed_data'].copy()
        
        # חישוב העלאה יחסית לפי ציון
        sum_scores = final_df['ציון משוקלל'].sum()
        if sum_scores > 0:
            final_df['העלאה מוצעת (₪)'] = (final_df['ציון משוקלל'] / sum_scores) * total_budget
        else:
            final_df['העלאה מוצעת (₪)'] = 0
            
        final_df['שכר חדש'] = final_df['שכר בסיס שנתי'] + final_df['העלאה מוצעת (₪)']
        final_df['אחוז העלאה'] = (final_df['העלאה מוצעת (₪)'] / final_df['שכר בסיס שנתי']) * 100
        
        st.dataframe(final_df[["שם העובד", "שכר בסיס שנתי", "ציון משוקלל", "העלאה מוצעת (₪)", "שכר חדש", "אחוז העלאה"]].style.format({
            "שכר בסיס שנתי": "₪{:,.0f}",
            "העלאה מוצעת (₪)": "₪{:,.0f}",
            "שכר חדש": "₪{:,.0f}",
            "אחוז העלאה": "{:.1f}%"
        }), use_container_width=True)
