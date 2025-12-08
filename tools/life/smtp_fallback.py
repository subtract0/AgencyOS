import smtplib

class SMTPFallback:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.username = ""
        self.password = ""

    def send_email(self, message: dict) -> None:
        # Implement sending email logic using SMTP
        pass
