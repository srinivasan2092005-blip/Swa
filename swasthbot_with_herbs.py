import sys
import streamlit as st
import pandas as pd
from collections import defaultdict

st.write("Python executable:", sys.executable)

# Safe import for plotly
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.warning("Plotly is not installed. Some graphs may not display.")
    px = None

# Safe import for speech recognition
try:
    import speech_recognition as sr
except ModuleNotFoundError:
    sr = None

EXCEL_PATH = "./odisha_diseases_39_with_updated_treatments.xlsx"

@st.cache
def load_disease_data(path):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        st.error(f"Excel file not found at path: {path}")
        st.stop()
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.stop()
    df.columns = [c.strip().lower() for c in df.columns]
    if 'name' not in df.columns:
        st.error(f"Excel must have a column called 'name'. Found: {list(df.columns)}")
        st.stop()
    df['name'] = df['name'].astype(str).str.lower()
    for col in ['medicines', 'herbal_remedies', 'red_flags', 'symptoms', 'care', 'transmission', 'prevention', 'treatment', 'refs', 'about']:
        if col not in df.columns:
            df[col] = ""
    return df

df = load_disease_data(EXCEL_PATH)

# Build symptom map
symptom_map = defaultdict(list)
all_symptoms = set()
for _, r in df.iterrows():
    raw = str(r.get("symptoms", ""))
    for s in [x.strip().lower() for x in raw.split(",") if x.strip()]:
        symptom_map[s].append(r['name'])
        all_symptoms.add(s)
all_symptoms = sorted(all_symptoms)

st.title("🩺 SwasthBot – Odisha Disease Info & Herbal + Medicine Info (SIH Version)")
st.caption("⚠ Informational only – Always consult a qualified clinician for diagnosis or treatment.")

# Voice input for Disease Search
st.markdown("### 🎤 Voice Input for Disease Search")
voice_query = ""
if sr is not None and st.button("🎙 Speak Disease Name"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak now")
        audio = r.listen(source)
    try:
        voice_query = r.recognize_google(audio)
        st.success(f"You said: {voice_query}")
    except Exception as e:
        st.error(f"Could not understand audio: {e}")

query = st.text_input("🔍 Search Disease by Name:", value=voice_query).strip().lower()
if query:
    matches = df[df['name'].str.contains(query, case=False, na=False)]
    if not matches.empty:
        row = matches.iloc[0]
        st.markdown(f"<h2>🦠 <span style='text-decoration: underline;'>{row['name'].upper()}</span></h2>", unsafe_allow_html=True)
        for field, emoji, style in [
            ("about", "ℹ", "info"), ("symptoms", "📝", "info"), ("red_flags", "🚨", "error"),
            ("care", "⛑", "warning"), ("transmission", "🔁", "info"), ("prevention", "🛡", "info"),
            ("treatment", "💊", "info"), ("medicines", "💊", "info"), ("herbal_remedies", "🌿", "success"),
        ]:
            if row.get(field):
                getattr(st, style)(f"{emoji} *{field.replace('_', ' ').title()}:* {row[field]}")
        if row.get("refs"):
            st.caption(f"📖 *References:* {row['refs']}")
    else:
        st.warning("❌ No disease found. Please check spelling.")

# Symptom Checker
st.markdown("### 🧠 Symptom Checker (Awareness Only)")
symptom_voice = ""
if sr is not None and st.button("🎙 Speak Symptoms (comma separated)"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak now")
        audio = r.listen(source)
    try:
        symptom_voice = r.recognize_google(audio)
        st.success(f"You said: {symptom_voice}")
    except Exception as e:
        st.error(f"Could not understand audio: {e}")

symptom_input = st.multiselect(
    "Select observed symptoms:",
    all_symptoms,
    default=[s.strip().lower() for s in symptom_voice.split(",") if s.strip()]
)

if symptom_input:
    disease_scores = {}
    risk_levels = {}
    for _, row in df.iterrows():
        disease_symptoms = [s.strip() for s in str(row['symptoms']).lower().split(",") if s.strip()]
        red_flags = [s.strip() for s in str(row.get("red_flags","")).lower().split(",") if s.strip()]
        matched = set(symptom_input) & set(disease_symptoms)
        score = len(matched)
        if score > 0:
            disease_scores[row['name']] = score
            matched_red_flags = len(set(symptom_input) & set(red_flags))
            if matched_red_flags > 0:
                risk_levels[row['name']] = "High 🔴"
            elif score / max(len(disease_symptoms), 1) > 0.5:
                risk_levels[row['name']] = "Medium 🟠"
            else:
                risk_levels[row['name']] = "Low 🟢"
    if disease_scores and px is not None:
        sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1], reverse=True)
        st.success("⚠ Possible conditions based on symptoms (sorted by relevance):")
        for disease, score in sorted_diseases:
            st.markdown(f"- 🦠 *{disease.title()}* – matched symptoms: {score} – Risk Level: {risk_levels[disease]}")
        chart_df = pd.DataFrame([{"Disease": d, "Matched Symptoms": s, "Risk": risk_levels[d]} for d, s in sorted_diseases])
        color_map = {"High 🔴": "red", "Medium 🟠": "orange", "Low 🟢": "green"}
        fig = px.bar(chart_df, x="Disease", y="Matched Symptoms", color="Risk", color_discrete_map=color_map, text="Matched Symptoms")
        st.plotly_chart(fig)
    else:
        st.info("No conditions match the selected symptoms.")
