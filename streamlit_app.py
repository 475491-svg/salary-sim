import streamlit as st
import pandas as pd

# כותרת האפליקציה
st.title("🚀 סימולטור תקציב קידום - מסך הערכת עובדים")

# שלב א': הגדרות
st.sidebar.header("הגדרות סימולציה")
rating_method = st.sidebar.radio("בחר שיטת דירוג:", ["סולם 1-5", "אחוזים (0-100)"])
upload_file = st.sidebar.file_uploader("העלה קובץ אקסל של העובדים", type=["xlsx", "csv"])

# רשימת המדדים שביקשת
options = ["עמידה ביעדי מחלקה", "חדשנות", "נוכחות מלאה", "ראש גדול", "השלמת יעדים אישיים", "הערכת מנהל", "אחר"]
selected_metrics = st.multiselect("בחר מדדי איכות להערכה:", options, default=options[:5])

# קביעת משקולות
weights = {}
st.subheader("קביעת משקל לכל מדד (חייב להשלים ל-100%)")
cols = st.columns(len(selected_metrics))
for i, metric in enumerate(selected_metrics):
    weights[metric] = cols[i].number_input(f"משקל {metric}", min_value=0, max_value=100, value=100//len(selected_metrics))

total_weight = sum(weights.values())
if total_weight != 100:
    st.error(f"שימי לב: סך המשקולות הוא {total_weight}%. עליך להגיע ל-100% כדי להמשיך.")
else:
    st.success("משקולות תקינים!")

# שלב ב': הזנת נתונים
if upload_file:
    df = pd.read_excel(upload_file)
else:
    # נתוני ברירת מחדל (למשל מנוחה מה-106)
    data = {
        "שם עובד": ["מנוחה רחל סבן"],
        "שכר בסיס": [111972] # נתון מטופס 106 שנת 2024 [cite: 72]
    }
    df = pd.DataFrame(data)

st.subheader("טבלת הערכת עובדים")
for metric in selected_metrics:
    df[metric] = 0.0

# טבלה אינטראקטיבית שניתן לערוך בדפדפן
edited_df = st.data_editor(df, num_rows="dynamic")

# חישוב הציון המשוקלל
def calculate_score(row):
    score = 0
    for metric, weight in weights.items():
        score += (row[metric] * (weight / 100))
    return score

if st.button("חשב ציון איכות משוקלל"):
    edited_df["ציון סופי"] = edited_df.apply(calculate_score, axis=1)
    st.write("תוצאות ההערכה:")
    st.dataframe(edited_df[["שם עובד", "שכר בסיס", "ציון סופי"]])
    st.session_state['df_final'] = edited_df
    st.info("הנתונים נשמרו. עברי למסך השני (בקרוב...)")
