import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

# Set up email details from environment variables
sender_email = os.getenv("SENDER_EMAIL")
password = os.getenv("EMAIL_PASSWORD")
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))

receiver_email = "receiver@example.com"
subject = "Welcome to Amazing Company"
body = """\
Hey there!

Thanks for joining us at Amazing Company. Your email has been verified and your account has been created.
Head to the website to login and start using our features."""

# Create the email message
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject

# Attach the email body to the message
message.attach(MIMEText(body, "plain"))

try:
    # Connect to the SMTP server
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(sender_email, password)  # Log in to the SMTP server
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )  # Send the email
    print("Email sent successfully")
except Exception as e:
    print(f"Error: {e}")
