import base64
import json
import re
from base64 import urlsafe_b64decode
from email.mime.text import MIMEText
from typing import Annotated, Any, Dict, Optional

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from arcade.core.schema import ToolContext
from arcade.sdk import tool
from arcade.sdk.auth import Google


@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def write_draft(
    context: ToolContext,
    subject: Annotated[str, "The subject of the email"],
    body: Annotated[str, "The body of the email"],
    recipient: Annotated[str, "The recipient of the email"],
) -> Annotated[str, "The URL of the draft"]:
    """Compose a new email draft."""

    # Set up the Gmail API client
    service = build("gmail", "v1", credentials=Credentials(context.authorization.token))

    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject

    # Encode the message in base64
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Create the draft
    draft = {"message": {"raw": raw_message}}

    draft_message = service.users().drafts().create(userId="me", body=draft).execute()
    return f"Draft created: {get_draft_url(draft_message['id'])}"


def get_draft_url(draft_id):
    return f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"


@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def get_emails(
    context: ToolContext,
    n_emails: Annotated[int, "Number of emails to read"] = 5,
) -> Annotated[str, "A list of email details in JSON format"]:
    """
    Read emails from a Gmail account and extract plain text content.

    Args:
        context (ToolContext): The context containing authorization information.
        n_emails (int): Number of emails to read (default: 5).

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing a list of email details.
    """
    service = build("gmail", "v1", credentials=Credentials(context.authorization.token))

    try:
        messages = (
            service.users().messages().list(userId="me").execute().get("messages", [])
        )

        if not messages:
            return {"emails": []}

        emails = []
        for msg in messages[:n_emails]:
            try:
                email_data = (
                    service.users().messages().get(userId="me", id=msg["id"]).execute()
                )
                email_details = parse_email(email_data)
                if email_details:
                    emails.append(email_details)
            except Exception as e:
                print(f"Error reading email {msg['id']}: {e}")

        return json.dumps({"emails": emails})

    except Exception as e:
        print(f"Error reading emails: {e}")
        return "Error reading emails"


def parse_email(email_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Parse email data and extract relevant information.

    Args:
        email_data (Dict[str, Any]): Raw email data from Gmail API.

    Returns:
        Optional[Dict[str, str]]: Parsed email details or None if parsing fails.
    """
    try:
        payload = email_data["payload"]
        headers = {d["name"].lower(): d["value"] for d in payload["headers"]}

        body_data = get_email_body(payload)

        return {
            "from": headers.get("from", ""),
            "date": headers.get("date", ""),
            "subject": headers.get("subject", "No subject"),
            "body": clean_email_body(body_data) if body_data else "",
        }
    except Exception as e:
        print(f"Error parsing email {email_data.get('id', 'unknown')}: {e}")
        return None


def get_email_body(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract email body from payload.

    Args:
        payload (Dict[str, Any]): Email payload data.

    Returns:
        Optional[str]: Decoded email body or None if not found.
    """
    if "body" in payload and payload["body"].get("data"):
        return urlsafe_b64decode(payload["body"]["data"]).decode()

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and "data" in part["body"]:
            return urlsafe_b64decode(part["body"]["data"]).decode()

    return None


def clean_email_body(body: str) -> str:
    """
    Remove HTML tags and clean up email body text while preserving most content.

    Args:
        body (str): The raw email body text.

    Returns:
        str: Cleaned email body text.
    """
    try:
        # Remove HTML tags using BeautifulSoup
        soup = BeautifulSoup(body, "html.parser")
        text = soup.get_text(separator=" ")

        # Clean up the text
        text = clean_text(text)

        return text.strip()
    except Exception as e:
        print(f"Error cleaning email body: {e}")
        return body


def clean_text(text: str) -> str:
    """
    Clean up the text while preserving most content.

    Args:
        text (str): The input text.

    Returns:
        str: Cleaned text.
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)

    # Replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace from each line
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text
