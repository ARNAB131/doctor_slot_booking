import smtplib
from email.mime.text import MIMEText
import os

def send_confirmation_email(patient_email, message):
    # Fetch credentials from environment variables
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    subject = "Appointment Confirmation"

    print(f"📧 Attempting to send email to: {patient_email}")
    print(f"From: {sender_email}")  # Debugging sender email

    if not sender_email or not sender_password:
        print("❌ Missing sender credentials in environment variables.")
        return False

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = patient_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, patient_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully.")
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False