from http import server
import smtplib
from email.mime.text import MIMEText

GMAIL = "basava72@gmail.com"
APP_PASSWORD = "ycpcanxgrftxawfh"  # Use an app password for Gmail

def send_email(email, otp):
    massage =MIMEText( f"Your Cricket scoring admin OTP code is: {otp}")

    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL
    msg['To'] = email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:

            print("Email:", GMAIL)
            print("Password length:", len(APP_PASSWORD))

            server.login(GMAIL, APP_PASSWORD)
            server.sendmail(GMAIL, email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
    server.login(GMAIL, APP_PASSWORD)
    server.sendmessage(GMAIL, email, msg.as_string())
    server.quit()

    print("Email Sent Successfully")

if __name__ == "__main__":
    send_email(
        "basava72@gmail.com",
        "123456"
    )