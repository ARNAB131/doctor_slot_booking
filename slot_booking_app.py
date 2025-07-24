import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from ai_booking import recommend_doctors, symptom_specialization_map, generate_slots
from utils.email_alert import send_confirmation_email
from datetime import datetime
import os

st.set_page_config(page_title="AI Slot Booking System", page_icon="🩺", layout="centered")

st.title("🤖 AI Doctor Slot Booking")
st.write("Easily book appointments using AI and voice-to-text.")

# Load doctor data
doctor_df = pd.read_csv("doctors.csv")

# Extract lists
doctor_list = doctor_df['Doctor Name'].tolist()
symptom_list = list(symptom_specialization_map.keys())

# Inject JavaScript for voice input
def inject_voice_input(field_id):
    st.markdown(f"""
    <script>
    const insertVoice = () => {{
        const recognition = new(window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.onresult = (event) => {{
            const transcript = event.results[0][0].transcript;
            const input = window.parent.document.querySelector('input[id="{field_id}"]');
            if(input) {{ input.value = transcript; input.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
        }};
        recognition.start();
    }};
    </script>
    <button onclick="insertVoice()">🎤 Speak for {field_id}</button><br><br>
    """, unsafe_allow_html=True)

# Input fields with voice buttons
name = st.text_input("Enter Patient Name:", key="patient_name")
inject_voice_input("patient_name")

symptom_text = st.text_input("Enter Symptoms (comma separated):", key="symptoms")
inject_voice_input("symptoms")

doctor_text = st.text_input("Enter Doctor's Name (optional):", key="doctor")
inject_voice_input("doctor")

appointment_date = st.date_input("Choose Appointment Date:", min_value=datetime.today())
patient_email = st.text_input("Enter Email:")

if st.button("🔔 Book Appointment"):
    used_name = name
    used_symptoms = [s.strip() for s in symptom_text.split(",") if s.strip()]
    used_doctor = doctor_text

    visiting = doctor_df[doctor_df['Doctor Name'] == used_doctor]['Visiting Time'].values
    if visiting.any():
        slots = generate_slots(visiting[0])
        used_slot = slots[0] if slots else "Slot Not Available"
    else:
        used_slot = "Slot Not Available"

    full_slot = f"{used_slot} on {appointment_date.strftime('%d %B %Y')}"

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
