import re
import email
import smtplib
import imaplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup

from arcade.sdk import Param, tool, get_secret


@tool
async def send_email(
    recipient_email: Param(str, "Email address of the recipient"),
    subject: Param(str, "Subject of the email"),
    body: Param(str, "Body of the email"),
):
    """Send an email via gmail SMTP server"""

    sender_email = get_secret("gmail_email")
    sender_password = get_secret("gmail_password")
    server = get_secret("gmail_stmp_server", "smtp.gmail.com")
    port = get_secret("gmail_stmp_port", 587)

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(server, port)
    server.starttls()
    server.login(sender_email, sender_password)
    print(f"Logged in to SMTP server at {':'.join((server, port))}", "DEBUG")

    server.send_message(message)
    server.quit()

    print(f"Email sent from {sender_email} to {recipient_email}", "INFO")


@tool
async def read_email(
    n_emails: Param(int, "Number of emails to read") = 5,
) -> Param(str, "emails"):
    """Read emails from a Gmail account and extract plain text content, removing any HTML."""

    email_address = get_secret("gmail_email")
    password = get_secret("gmail_password")
    server = get_secret("gmail_stmp_server", "smtp.gmail.com")

    # Connect to the Gmail IMAP server
    mail = imaplib.IMAP4_SSL(server)
    mail.login(email_address, password)
    mail.select("inbox")  # connect to inbox.

    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()
    email_ids.reverse()  # Reverse to get the most recent emails first

    emails = []

    for email_id in email_ids[:n_emails]:
        try:
            result, data = mail.fetch(email_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            email_details = {"from": msg["From"], "to": msg["To"], "date": msg["Date"]}

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8")
                        email_details["body"] = clean_email_body(body)
            else:
                body = msg.get_payload(decode=True).decode("utf-8")
                email_details["body"] = clean_email_body(body)
        except Exception as e:
            log(f"Error reading email {email_id}: {e}", "ERROR")
            continue

        emails.append(email_details)

    mail.close()
    mail.logout()
    data = "\n".join(
        [f"{email['from']} - {email['date']}\n{email['body']}\n" for email in emails]
    )
    return data


def clean_email_body(body: str) -> str:
    """Remove HTML tags and non-sentence elements from email body text."""

    # Remove HTML tags using BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text(separator=" ")

    # Remove any non-sentence elements (e.g., URLs, email addresses, etc.)
    text = re.sub(r"\S*@\S*\s?", "", text)  # Remove emails
    text = re.sub(r"http\S+", "", text)  # Remove URLs
    text = re.sub(r"[^.!?a-zA-Z0-9\s]", "", text)  # Remove non-sentence characters
    text = " ".join(text.split())  # Remove extra whitespace

    return text
