import re
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from arcade_google.tools.models import Day, TimeSlot


def parse_datetime(datetime_str: str, time_zone: str) -> datetime:
    """
    Parse a datetime string in ISO 8601 format and ensure it is timezone-aware.

    Args:
        datetime_str (str): The datetime string to parse. Expected format: 'YYYY-MM-DDTHH:MM:SS'.
        time_zone (str): The timezone to apply if the datetime string is naive.

    Returns:
        datetime: A timezone-aware datetime object.

    Raises:
        ValueError: If the datetime string is not in the correct format.
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(time_zone))
    except ValueError as e:
        raise ValueError(
            f"Invalid datetime format: '{datetime_str}'. "
            "Expected ISO 8601 format, e.g., '2024-12-31T15:30:00'."
        ) from e
    return dt


class DateRange(Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"

    def to_date_query(self) -> str:
        today = datetime.now()
        result = "after:"
        comparison_date = today

        if self == DateRange.YESTERDAY:
            comparison_date = today - timedelta(days=1)
        elif self == DateRange.LAST_7_DAYS:
            comparison_date = today - timedelta(days=7)
        elif self == DateRange.LAST_30_DAYS:
            comparison_date = today - timedelta(days=30)
        elif self == DateRange.THIS_MONTH:
            comparison_date = today.replace(day=1)
        elif self == DateRange.LAST_MONTH:
            comparison_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        elif self == DateRange.THIS_YEAR:
            comparison_date = today.replace(month=1, day=1)
        elif self == DateRange.LAST_MONTH:
            comparison_date = (today.replace(month=1, day=1) - timedelta(days=1)).replace(
                month=1, day=1
            )

        return result + comparison_date.strftime("%Y/%m/%d")


def process_email_messages(service: Any, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    emails = []
    for msg in messages:
        try:
            email_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
            email_details = parse_email(email_data)
            emails += [email_details] if email_details else []
        except HttpError as e:
            print(f"Error reading email {msg['id']}: {e}")
    return emails


def parse_email(email_data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse email data and extract relevant information.

    Args:
        email_data (Dict[str, Any]): Raw email data from Gmail API.

    Returns:
        Optional[Dict[str, str]]: Parsed email details or None if parsing fails.
    """
    try:
        payload = email_data.get("payload", {})
        headers = {d["name"].lower(): d["value"] for d in payload.get("headers", [])}

        body_data = _get_email_body(payload)

        return {
            "id": email_data.get("id", ""),
            "thread_id": email_data.get("threadId", ""),
            "from": headers.get("from", ""),
            "date": headers.get("date", ""),
            "subject": headers.get("subject", ""),
            "body": _clean_email_body(body_data) if body_data else "",
        }
    except Exception as e:
        print(f"Error parsing email {email_data.get('id', 'unknown')}: {e}")
        return email_data


def parse_draft_email(draft_email_data: dict[str, Any]) -> dict[str, str]:
    """
    Parse draft email data and extract relevant information.

    Args:
        draft_email_data (Dict[str, Any]): Raw draft email data from Gmail API.

    Returns:
        Optional[Dict[str, str]]: Parsed draft email details or None if parsing fails.
    """
    try:
        message = draft_email_data.get("message", {})
        payload = message.get("payload", {})
        headers = {d["name"].lower(): d["value"] for d in payload.get("headers", [])}

        body_data = _get_email_body(payload)

        return {
            "id": draft_email_data.get("id", ""),
            "thread_id": draft_email_data.get("threadId", ""),
            "from": headers.get("from", ""),
            "date": headers.get("internaldate", ""),
            "subject": headers.get("subject", ""),
            "body": _clean_email_body(body_data) if body_data else "",
        }
    except Exception as e:
        print(f"Error parsing draft email {draft_email_data.get('id', 'unknown')}: {e}")
        return draft_email_data


def get_draft_url(draft_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"


def get_sent_email_url(sent_email_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#sent/{sent_email_id}"


def get_email_in_trash_url(email_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#trash/{email_id}"


def _get_email_body(payload: dict[str, Any]) -> Optional[str]:
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


def _clean_email_body(body: str) -> str:
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
        cleaned_text = _clean_text(text)

        return cleaned_text.strip()
    except Exception as e:
        print(f"Error cleaning email body: {e}")
        return body


def _clean_text(text: str) -> str:
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


def _update_datetime(day: Day | None, time: TimeSlot | None, time_zone: str) -> dict | None:
    """
    Update the datetime for a Google Calendar event.

    Args:
        day (Day | None): The day of the event.
        time (TimeSlot | None): The time of the event.
        time_zone (str): The time zone of the event.

    Returns:
        dict | None: The updated datetime for the event.
    """
    if day and time:
        dt = datetime.combine(day.to_date(time_zone), time.to_time())
        return {"dateTime": dt.isoformat(), "timeZone": time_zone}
    return None


def build_query_string(
    sender: str | None,
    recipient: str | None,
    subject: str | None,
    body: str | None,
    date_range: DateRange | None,
) -> str:
    """Helper function to build a query string
    for Gmail list_emails_by_header and search_threads tools.
    """
    query = []
    if sender:
        query.append(f"from:{sender}")
    if recipient:
        query.append(f"to:{recipient}")
    if subject:
        query.append(f"subject:{subject}")
    if body:
        query.append(body)
    if date_range:
        query.append(date_range.to_date_query())
    return " ".join(query)


def fetch_messages(service: Any, query_string: str, limit: int) -> list[dict[str, Any]]:
    """
    Helper function to fetch messages from Gmail API for the list_emails_by_header tool.
    """
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query_string, maxResults=limit or 100)
        .execute()
    )
    return response.get("messages", [])  # type: ignore[no-any-return]


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.
    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}


# Drive utils
def build_drive_service(auth_token: Optional[str]) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("drive", "v3", credentials=Credentials(auth_token))


# Docs utils
def build_docs_service(auth_token: Optional[str]) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("docs", "v1", credentials=Credentials(auth_token))


def parse_rfc3339(dt_str: str, tz: timezone = timezone.utc) -> datetime:
    """
    Parse an RFC3339 datetime string into a timezone-aware datetime.
    Converts a trailing 'Z' (UTC) into +00:00.
    If the parsed datetime is naive, assume it is in the provided timezone.
    """
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt


def merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """
    Given a list of (start, end) tuples, merge overlapping or adjacent intervals.
    """
    merged = []
    for start, end in sorted(intervals, key=lambda x: x[0]):
        if not merged:
            merged.append((start, end))
        else:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))
    return merged


def get_business_hours_for_day(
    current_date: datetime,
    business_tz: timezone,
    global_start: datetime,
    global_end: datetime,
) -> tuple[datetime, datetime]:
    """
    Compute the allowed business hours for the given day, adjusting for global bounds.

    Business hours are defined as 08:00 to 19:00 in the business_tz timezone.
    On the first and last day, the business hours are trimmed to the global_start/global_end.
    """
    day_business_start = datetime(
        current_date.year, current_date.month, current_date.day, 8, 0, tzinfo=business_tz
    )
    day_business_end = datetime(
        current_date.year, current_date.month, current_date.day, 19, 0, tzinfo=business_tz
    )
    if current_date == global_start.date():
        day_business_start = max(day_business_start, global_start)
    if current_date == global_end.date():
        day_business_end = min(day_business_end, global_end)
    return day_business_start, day_business_end


def gather_busy_intervals(
    busy_data: dict[str, Any],
    day_start: datetime,
    day_end: datetime,
    business_tz: timezone,
) -> list[tuple[datetime, datetime]]:
    """
    Collect busy intervals from all calendars that intersect with the day's business hours.
    Busy intervals are clipped to lie within [day_start, day_end].
    """
    busy_intervals = []
    for calendar in busy_data:
        for slot in busy_data[calendar].get("busy", []):
            slot_start = parse_rfc3339(slot["start"]).astimezone(business_tz)
            slot_end = parse_rfc3339(slot["end"]).astimezone(business_tz)
            if slot_end > day_start and slot_start < day_end:
                busy_intervals.append((max(slot_start, day_start), min(slot_end, day_end)))
    return busy_intervals


def subtract_busy_intervals(
    business_start: datetime,
    business_end: datetime,
    busy_intervals: list[tuple[datetime, datetime]],
) -> list[dict[str, Any]]:
    """
    Subtract the merged busy intervals from the business hours and return free time slots.
    """
    free_slots = []
    merged_busy = merge_intervals(busy_intervals)
    current_free_start = business_start
    for busy_start, busy_end in merged_busy:
        if current_free_start < busy_start:
            free_slots.append({
                "start": current_free_start.isoformat(),
                "end": busy_start.isoformat(),
            })
        current_free_start = max(current_free_start, busy_end)
    if current_free_start < business_end:
        free_slots.append({
            "start": current_free_start.isoformat(),
            "end": business_end.isoformat(),
        })
    return free_slots


def find_free_times(
    busy_data: dict[str, Any],
    global_start_str: str,
    global_end_str: str,
    tz: timezone = timezone.utc,
) -> list[dict[str, Any]]:
    """
    Returns the free time slots across all calendars within the global bounds,
    ensuring that the global start is not in the past.

    Only considers business days (Monday to Friday) and business hours (08:00-19:00)
    in the provided timezone.
    """
    # Parse the global boundaries and convert them to the business timezone.
    global_start = parse_rfc3339(global_start_str).astimezone(tz)
    global_end = parse_rfc3339(global_end_str).astimezone(tz)

    # Ensure global_start is never in the past relative to now.
    now = get_now(tz)
    if now > global_start:
        global_start = now

    # If after adjusting the start, there's no interval left, return empty.
    if global_start >= global_end:
        return []

    free_slots = []
    current_date = global_start.date()

    while current_date <= global_end.date():
        # Only consider weekdays (Monday=0 to Friday=4)
        if current_date.weekday() < 5:
            day_start, day_end = get_business_hours_for_day(
                current_date, tz, global_start, global_end
            )
            # Skip if the day's business window is empty.
            if day_start >= day_end:
                current_date += timedelta(days=1)
                continue

            busy_intervals = gather_busy_intervals(busy_data, day_start, day_end, tz)
            free_slots.extend(subtract_busy_intervals(day_start, day_end, busy_intervals))
        current_date += timedelta(days=1)

    return free_slots


def get_now(tz: timezone = timezone.utc) -> datetime:
    return datetime.now(tz)
