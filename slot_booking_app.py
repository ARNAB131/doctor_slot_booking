import streamlit as st
import pandas as pd
import io
from fpdf import FPDF
from ai_booking import recommend_doctors
from utils.email_alert import send_confirmation_email

st.set_page_config(page_title="AI Slot Booking System", page_icon="🩺", layout="centered")

st.title("🤖 AI Doctor Slot Booking")
st.write("Easily find and book the best doctor slots using AI.")

# Load doctor data
doctor_df = pd.read_csv("doctors.csv")

# User Input
symptom = st.text_input("Enter your symptom or health issue:", "fever")
patient_email = st.text_input("Enter your email to receive confirmation:")
preferred_time = st.time_input("Preferred Time (optional):", None, disabled=True)

if st.button("🔍 Find Doctors"):
    message, recommendations = recommend_doctors(symptom)
    st.subheader(message)

    if recommendations:
        for idx, doc in enumerate(recommendations):
            with st.expander(f"{idx+1}. Dr. {doc['Doctor']} - {doc['Specialization']}"):
                st.markdown(f"**Chamber:** {doc['Chamber']}")
                st.markdown("**Available Slots:**")

                slot = st.selectbox(f"Select a slot for Dr. {doc['Doctor']}", options=doc['Slots'], key=f"slot_{idx}")

                if st.button(f"Book Appointment with Dr. {doc['Doctor']}", key=f"book_{idx}"):
                    st.success(f"✅ Appointment Booked with Dr. {doc['Doctor']} at {slot}")

                    confirmation_text = f"""
Appointment Confirmed!
Doctor: {doc['Doctor']}
Specialization: {doc['Specialization']}
Chamber: {doc['Chamber']}
Slot: {slot}
"""

                    # CSV Download
                    csv_file = io.StringIO()
                    csv_file.write("Doctor,Specialization,Chamber,Slot\n")
                    csv_file.write(f"{doc['Doctor']},{doc['Specialization']},{doc['Chamber']},{slot}\n")
                    st.download_button("⬇️ Download CSV", csv_file.getvalue(), "appointment.csv", mime="text/csv")

                    # PDF Download
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    for line in confirmation_text.split("\n"):
                        pdf.cell(200, 10, txt=line.strip(), ln=True)
                    pdf_output = io.BytesIO()
                    pdf.output(pdf_output)
                    pdf_output.seek(0)
                    st.download_button("⬇️ Download PDF", pdf_output, file_name="appointment.pdf", mime="application/pdf")

                    # Send Email Confirmation
                    if patient_email:
                        email_status = send_confirmation_email(patient_email, confirmation_text)
                        if email_status:
                            st.success("✅ Email Confirmation Sent")
                        else:
                            st.error("❌ Failed to send email")
    else:
        st.error("No available doctors found for your input.")

st.markdown("---")
st.caption("Built with ❤️ by AI Slot Booking System")