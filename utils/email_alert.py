import smtplib
from email.mime.text import MIMEText

def send_confirmation_email(patient_email, message):
    sender_email = "your_email@gmail.com"  # Replace with your email
    sender_password = "your_app_password"  # Replace with your Gmail App Password
    subject = "Appointment Confirmation"

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
