import os
import re
import email
import smtplib
import imaplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from typing import Dict, List, Annotated
from arcade.sdk.tool import tool, get_secret


@tool
async def send_email(
    recipient_email: Annotated[str, "Email address of the recipient"],
    subject: Annotated[str, "Subject of the email"],
    body: Annotated[str, "Body of the email"],
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
    n_emails: Annotated[int, "Number of emails to read"] = 5,
) -> Annotated[str, "emails"]:
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
            print(f"Error reading email {email_id}: {e}", "ERROR")
            continue

        emails.append(email_details)

    mail.close()
    mail.logout()
    data = "\n".join(
        [f"{email['from']} - {email['date']}\n{email['body']}\n" for email in emails]
    )
    return data


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SECRET_FILE = "/Users/spartee/Dropbox/Arcade/gcp/credentials.json"


@tool
async def oauth_read_email(
    n_emails: Annotated[int, "Number of emails to read"] = 5,
) -> List[Dict[str, str]]:
    """Read emails from a Gmail account and extract plain text content, removing any HTML."""

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                flow = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)

    # Request a list of all the messages
    result = service.users().messages().list(userId="me").execute()
    messages = result.get("messages")

    # If there are no messages, return an empty string
    if not messages:
        return ""

    emails = []

    for msg in messages[:n_emails]:
        txt = service.users().messages().get(userId="me", id=msg["id"]).execute()

        try:
            payload = txt["payload"]
            headers = payload["headers"]

            for d in headers:
                if d["name"] == "From":
                    from_ = d["value"]
                if d["name"] == "Date":
                    date = d["value"]
                if d["name"] == "Subject":
                    subject = d["value"]
                else:
                    subject = "No subject"

            data = None
            parts = payload.get("parts")
            if parts:
                part = parts[0]
                body = part.get("body")
                if body:
                    data = body.get("data")
                    if data:
                        data = urlsafe_b64decode(data).decode()

            email_details = {
                "from": from_,
                "date": date,
                "subject": subject,
                "body": clean_email_body(data) if data else "",
            }
            emails.append(email_details)

        except Exception as e:
            print(f"Error reading email {msg['id']}: {e}", "ERROR")
            continue

    return emails


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


DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]


@tool
async def list_drive_files(
    n_files: Annotated[int, "Number of files to search"] = 5,
) -> list[str]:
    """List files from a Google Drive account and return their details."""

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                flow = InstalledAppFlow.from_client_secrets_file(
                    SECRET_FILE, DRIVE_SCOPES
                )
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, DRIVE_SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    # Call the Drive v3 API
    service = build("drive", "v3", credentials=creds)

    # Request a list of all the files
    results = (
        service.files()
        .list(pageSize=n_files, fields="nextPageToken, files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
        print("No files found.")
    else:
        print("Files:")
        for item in items:
            print("{0} ({1})".format(item["name"], item["id"]))

    return items
