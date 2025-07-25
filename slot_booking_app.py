import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.email_alert import send_confirmation_email
from ai_booking import generate_slots, symptom_specialization_map

st.set_page_config(page_title="AI Slot Booking System", page_icon="🩺", layout="centered")

st.title("🤖 AI Doctor Slot Booking (Voice-Enabled)")
st.write("Book appointments using voice or text input.")

# Load doctor data
doctor_df = pd.read_csv("doctors.csv")
doctor_list = doctor_df['Doctor Name'].tolist()
symptom_list = list(symptom_specialization_map.keys())

# Inject JavaScript for voice-to-text
st.markdown("""
<script>
  let recognition;
  function startDictation(field_id) {
    recognition = new(window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.onresult = function(event) {
      const result = event.results[0][0].transcript;
      const input = document.getElementById(field_id);
      if (input) {
        input.value = result;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    };
    recognition.start();
  }
</script>
""", unsafe_allow_html=True)

# Input Fields with Voice Buttons
st.markdown("#### 👤 Patient Name")
st.markdown('<input type="text" id="name_input" placeholder="Say your name..." class="stTextInput"> <button onclick="startDictation(\'name_input\')">🎤 Speak</button>', unsafe_allow_html=True)
patient_name = st.text_input("Your name:", key="name_input_hidden")

st.markdown("#### 🤕 Symptoms")
st.markdown('<input type="text" id="symptom_input" placeholder="Say symptoms..." class="stTextInput"> <button onclick="startDictation(\'symptom_input\')">🎤 Speak</button>', unsafe_allow_html=True)
symptom_text = st.text_input("Symptoms (comma separated):", key="symptom_input_hidden")
symptoms = [s.strip() for s in symptom_text.split(',') if s.strip() in symptom_list]

st.markdown("#### 👨‍⚕️ Doctor Name")
st.markdown('<input type="text" id="doctor_input" placeholder="Say doctor name..." class="stTextInput"> <button onclick="startDictation(\'doctor_input\')">🎤 Speak</button>', unsafe_allow_html=True)
selected_doctor = st.selectbox("Choose Doctor:", ["None"] + doctor_list)

appointment_date = st.date_input("Choose Date:", min_value=datetime.today())
email = st.text_input("Your Email:")

if st.button("✅ Book Appointment"):
    final_doctor = selected_doctor if selected_doctor != "None" else None
    if not (patient_name and final_doctor and symptoms):
        st.error("Please fill all fields (name, symptoms, doctor).")
    else:
        visiting_time = doctor_df[doctor_df['Doctor Name'] == final_doctor]['Visiting Time'].values
        slot = generate_slots(visiting_time[0])[0] if len(visiting_time) else "Slot Unavailable"
        final_slot = f"{slot} on {appointment_date.strftime('%d %B %Y')}"

        record = pd.DataFrame([{
            "Patient Name": patient_name,
            "Doctor": final_doctor,
            "Slot": final_slot,
            "Symptoms": '; '.join(symptoms),
            "Email": email,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])

        if os.path.exists("appointments.csv"):
            record.to_csv("appointments.csv", mode="a", header=False, index=False)
        else:
            record.to_csv("appointments.csv", index=False)

        st.success(f"✅ Appointment booked with Dr. {final_doctor} on {final_slot}")
        send_confirmation_email(email, f"Appointment confirmed with Dr. {final_doctor} on {final_slot}")
