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
        symptom_voice = r.recognize
