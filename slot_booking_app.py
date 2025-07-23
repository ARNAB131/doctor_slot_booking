import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from ai_booking import recommend_doctors, symptom_specialization_map, generate_slots
from utils.email_alert import send_confirmation_email
from datetime import datetime
import calendar

st.set_page_config(page_title="AI Slot Booking System", page_icon="🩺", layout="centered")

st.title("🤖 AI Doctor Slot Booking")
st.write("Easily find and book the best doctor slots using AI.")

# Load doctor data
doctor_df = pd.read_csv("doctors.csv")

# User Input with multiselect symptoms
symptom_options = list(symptom_specialization_map.keys())
symptoms = st.multiselect("Select your symptom(s):", options=symptom_options)

# Optional general doctor dropdown booking
st.markdown("---")
st.subheader("📋 Or Book Directly by Choosing a Doctor")
doctor_names = doctor_df['Doctor Name'].unique().tolist()
selected_doctor = st.selectbox("Choose a doctor to book directly (optional):", ["None"] + doctor_names)

direct_slot = ""
if selected_doctor != "None":
    selected_info = doctor_df[doctor_df['Doctor Name'] == selected_doctor].iloc[0]
    st.markdown(f"**Specialization:** {selected_info['Specialization']}")
    st.markdown(f"**Chamber:** {selected_info['Chamber']}")
    slots = generate_slots(selected_info['Visiting Time'])
    direct_slot = st.selectbox("Select a slot:", slots, key="direct_slot")

    # 📅 Calendar View
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
Doctor: {st.session_state.booked_doctor}
Slot: {st.session_state.slot}
Symptoms: {', '.join(st.session_state.symptoms_used)}
"""

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

st.markdown("---")
st.caption("Built with ❤️ by AI Slot Booking System")