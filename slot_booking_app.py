import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from ai_booking import recommend_doctors, symptom_specialization_map, generate_slots
from utils.email_alert import send_confirmation_email
from datetime import datetime, timedelta
import calendar
import os
import requests
import spacy
import json

# Load spaCy model safely with auto-download
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

st.set_page_config(page_title="AI Slot Booking System", page_icon="🪺", layout="centered")

st.title("🤖 AI Doctor Slot Booking")
st.write("Easily book appointments using smart voice + AI NLP.")

# Load doctor data
doctor_df = pd.read_csv("doctors.csv")

# Extract lists
doctor_list = doctor_df['Doctor Name'].tolist()
symptom_list = list(symptom_specialization_map.keys())

# Real-time Full Sentence Voice to Text (via JS)
st.markdown("""
<script>
  let recognition;
  const startRecognition = () => {
    recognition = new(window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const voiceText = event.results[0][0].transcript;
      fetch(window.location.href, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text: voiceText})
      });
    };
    recognition.start();
  }
</script>
<button onclick="startRecognition()">🎹 Start Voice Booking</button>
""", unsafe_allow_html=True)

# Receive POST request and update session state
try:
    if st.request and st.request.method == "POST":
        data = st.request.body
        if data:
            try:
                payload = json.loads(data)
                st.session_state.voice_text = payload.get("text", "")
            except Exception as e:
                st.error(f"Error processing voice input: {e}")
except:
    pass

# Backend: Accept full sentence input
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# Display and parse voice command
if st.session_state.voice_text:
    st.markdown(f"### 🎤 You said: `{st.session_state.voice_text}`")

    def parse_booking(text):
        doc = nlp(text)
        name, doctor, symptoms, appt_date = "", "", [], ""

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
            elif ent.label_ == "DATE":
                try:
                    import dateparser
                    appt_date = dateparser.parse(ent.text)
                except:
                    pass

        for d in doctor_list:
            if d.lower() in text:
                doctor = d
                break

        for sym in symptom_list:
            if sym.lower() in text:
                symptoms.append(sym)

        return name, doctor, symptoms, appt_date

    name, doctor, symptoms_voice, appt_date = parse_booking(st.session_state.voice_text)

    if name:
        st.text_input("Patient Name:", value=name, key="voice_name")
    if doctor:
        st.text_input("Doctor:", value=doctor, key="voice_doctor")
    if symptoms_voice:
        st.session_state.voice_symptoms = symptoms_voice
    if appt_date:
        st.date_input("Date:", value=appt_date, key="voice_date")

    st.info("Auto-filled data from voice. Verify and book below.")

# Fallback manual input
st.text_input("Patient Name:", key="manual_name")

if st.session_state.get("voice_symptoms"):
    symptoms = st.multiselect("Select Symptoms:", options=symptom_list, default=st.session_state.voice_symptoms, key="manual_symptoms")
else:
    symptoms = st.multiselect("Select Symptoms:", options=symptom_list, key="manual_symptoms")

selected_doctor = st.selectbox("Choose Doctor:", ["None"] + doctor_list, key="manual_doctor")
appointment_date = st.date_input("Choose Date:", min_value=datetime.today(), key="manual_date")
patient_email = st.text_input("Enter Email:")

if st.button("🔔 Book Appointment"):
    used_name = st.session_state.get("voice_name") or st.session_state.manual_name
    used_doctor = st.session_state.get("voice_doctor") or st.session_state.manual_doctor
    used_symptoms = st.session_state.get("voice_symptoms") or st.session_state.manual_symptoms
    used_date = st.session_state.get("voice_date") or st.session_state.manual_date

    visiting = doctor_df[doctor_df['Doctor Name'] == used_doctor]['Visiting Time'].values
    if visiting.any():
        slots = generate_slots(visiting[0])
        used_slot = slots[0] if slots else "Slot Not Available"
    else:
        used_slot = "Slot Not Available"

    full_slot = f"{used_slot} on {used_date.strftime('%d %B %Y')}"

    # Save to appointments
    df_new = pd.DataFrame([{
        "Patient Name": used_name,
        "Email": patient_email,
        "Symptoms": '; '.join(used_symptoms),
        "Doctor": used_doctor,
        "Slot": full_slot,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])

    try:
        if os.path.exists("appointments.csv"):
            df_new.to_csv("appointments.csv", mode="a", header=False, index=False)
        else:
            df_new.to_csv("appointments.csv", index=False)
    except Exception as e:
        st.error(f"❌ Failed to save appointment data: {e}")

    st.success(f"✅ Appointment booked for {used_name} with Dr. {used_doctor} at {full_slot}")
    send_confirmation_email(patient_email, f"Appointment with Dr. {used_doctor} confirmed at {full_slot}")
