import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from ai_booking import recommend_doctors, symptom_specialization_map, generate_slots
from utils.email_alert import send_confirmation_email
from datetime import datetime, timedelta
import calendar
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Slot Booking System", page_icon="🩺", layout="centered")

st.title("🤖 AI Doctor Slot Booking")
st.write("Easily find and book the best doctor slots using AI.")

# Load doctor data
doctor_df = pd.read_csv("doctors.csv")

# Patient Name Input
patient_name = st.text_input("Enter your name:")

# User Input with multiselect symptoms + voice input
symptom_options = list(symptom_specialization_map.keys())

st.markdown("### 🤒 Select your symptom(s):")
cols = st.columns([4, 1])
with cols[0]:
    symptoms = st.multiselect("", options=symptom_options, key="symptoms")

with cols[1]:
    st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
    components.html("""
    <button onclick="recordAndSend()" style="padding:8px 12px;background-color:#4CAF50;color:white;border:none;border-radius:5px;cursor:pointer;">
      🎙️ Voice Input
    </button>
    <script>
    async function recordAndSend() {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Sorry, your browser doesn't support Speech Recognition.");
            return;
        }
        const recognition = new webkitSpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.onresult = function(event) {
            const result = event.results[0][0].transcript;
            const stream = new EventSource(`/streamlit/voice_result?result=${result}`);
        }
        recognition.onerror = function(event) {
            alert("Error: " + event.error);
        }
        recognition.start();
    }
    </script>
    """, height=50)
    st.markdown("</div>", unsafe_allow_html=True)

# Optional general doctor dropdown booking
st.markdown("---")
st.subheader("📋 Or Book Directly by Choosing a Doctor")
doctor_names = doctor_df['Doctor Name'].unique().tolist()
selected_doctor = st.selectbox("Choose a doctor to book directly (optional):", ["None"] + doctor_names)

direct_slot = ""
selected_date = None
if selected_doctor != "None":
    selected_info = doctor_df[doctor_df['Doctor Name'] == selected_doctor].iloc[0]
    st.markdown(f"**Specialization:** {selected_info['Specialization']}")
    st.markdown(f"**Chamber:** {selected_info['Chamber']}")
    slots = generate_slots(selected_info['Visiting Time'])
    direct_slot = st.selectbox("Select a slot:", slots, key="direct_slot")

    today = datetime.today()
    selected_date = st.date_input("Choose appointment date:", min_value=today)

    if st.button(f"📅 Book Appointment with Dr. {selected_doctor}", key="direct_book"):
        st.session_state.booked = True
        st.session_state.booked_doctor = selected_doctor
        st.session_state.slot = f"{direct_slot} on {selected_date.strftime('%d %B %Y')}"
        st.session_state.symptoms_used = symptoms or ["Direct Booking"]

# Email input
patient_email = st.text_input("Enter your email to receive confirmation:")

# Recommendation based on symptoms
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
    st.session_state.doctor_message = ""
    st.session_state.booked = False
    st.session_state.booked_doctor = ""
    st.session_state.slot = ""
    st.session_state.symptoms_used = []

if st.button("🔍 Find Doctors") and symptoms:
    message, recommendations = recommend_doctors(symptoms)
    st.session_state.recommendations = recommendations
    st.session_state.doctor_message = message
    st.session_state.booked = False
    st.session_state.symptoms_used = symptoms

st.subheader(st.session_state.doctor_message)

if st.session_state.recommendations:
    for idx, doc in enumerate(st.session_state.recommendations):
        with st.expander(f"{idx+1}. Dr. {doc['Doctor']} - {doc['Specialization']}"):
            st.markdown(f"**Chamber:** {doc['Chamber']}")
            slot = st.selectbox(f"Select a slot for Dr. {doc['Doctor']}", options=doc['Slots'], key=f"slot_{idx}")
            appt_date = st.date_input(f"Choose date for Dr. {doc['Doctor']}", key=f"date_{idx}", min_value=datetime.today())

            if st.button(f"Book Appointment with Dr. {doc['Doctor']}", key=f"book_{idx}"):
                st.session_state.booked = True
                st.session_state.booked_doctor = doc['Doctor']
                st.session_state.slot = f"{slot} on {appt_date.strftime('%d %B %Y')}"
                st.session_state.symptoms_used = symptoms

if st.session_state.booked:
    st.success(f"✅ Appointment Booked with Dr. {st.session_state.booked_doctor} at {st.session_state.slot}")

    confirmation_text = f"""
Appointment Confirmed!
Name: {patient_name}
Doctor: {st.session_state.booked_doctor}
Slot: {st.session_state.slot}
Symptoms: {', '.join(st.session_state.symptoms_used)}
"""

    appointment_df = pd.DataFrame([{
        "Patient Name": patient_name,
        "Email": patient_email,
        "Symptoms": '; '.join(st.session_state.symptoms_used),
        "Doctor": st.session_state.booked_doctor,
        "Slot": st.session_state.slot,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    if os.path.exists("appointments.csv"):
        appointment_df.to_csv("appointments.csv", mode="a", header=False, index=False)
    else:
        appointment_df.to_csv("appointments.csv", mode="w", header=True, index=False)

    csv_file = io.StringIO()
    csv_file.write("Doctor,Slot,Symptoms\n")
    csv_file.write(f"{st.session_state.booked_doctor},{st.session_state.slot},{'; '.join(st.session_state.symptoms_used)}\n")
    st.download_button("⬇️ Download CSV", csv_file.getvalue(), "appointment.csv", mime="text/csv")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in confirmation_text.split("\n"):
        pdf.cell(200, 10, txt=line.strip(), ln=True)
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output = io.BytesIO(pdf_bytes)
    st.download_button("⬇️ Download PDF", pdf_output, file_name="appointment.pdf", mime="application/pdf")

    if patient_email:
        email_status = send_confirmation_email(patient_email, confirmation_text)
        st.write(f"📧 Attempting to send email to: {patient_email}")
        if email_status:
            st.success("✅ Email Confirmation Sent")
        else:
            st.error("❌ Failed to send email")
    else:
        st.warning("❗ No email provided, skipping confirmation email.")

# Admin Dashboard
st.markdown("---")
st.header("📊 Admin Dashboard - All Appointments")
if os.path.exists("appointments.csv"):
    df = pd.read_csv("appointments.csv")

    st.markdown("### 🔍 Filter by Doctor")
    doctor_filter = st.selectbox("Select Doctor:", options=["All"] + sorted(df["Doctor"].unique().tolist()))
    if doctor_filter != "All":
        df = df[df["Doctor"] == doctor_filter]

    st.dataframe(df)

    st.markdown("### 🧾 View Patient History")
    patient_query = st.text_input("Search by Patient Name or Email:")
    if patient_query:
        filtered = df[df['Patient Name'].str.contains(patient_query, case=False) | df['Email'].str.contains(patient_query, case=False)]
        st.dataframe(filtered)

    st.markdown("### ⏰ Upcoming Appointment Reminders")
    today = datetime.today()
    df['Parsed Date'] = pd.to_datetime(df['Slot'].str.extract(r'on (.+)$')[0], errors='coerce')
    upcoming = df[df['Parsed Date'].between(today, today + timedelta(days=3))]
    for _, row in upcoming.iterrows():
        st.info(f"📅 {row['Parsed Date'].strftime('%d %b %Y')} - {row['Patient Name']} with Dr. {row['Doctor']}")

    csv_download = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Export CSV", csv_download, "appointments_admin_view.csv", mime="text/csv")

    st.markdown("### 📅 Calendar View")
    if not df['Parsed Date'].isnull().all():
        grouped = df.groupby(['Parsed Date', 'Doctor']).size().reset_index(name='Appointments')
        for date, group in grouped.groupby('Parsed Date'):
            st.markdown(f"#### {date.strftime('%d %B %Y')}")
            for _, row in group.iterrows():
                st.write(f"👨‍⚕️ {row['Doctor']} - {row['Appointments']} appointments")
else:
    st.info("No appointments booked yet.")

st.markdown("---")
st.caption("Built with ❤️ by AI Slot Booking System")
