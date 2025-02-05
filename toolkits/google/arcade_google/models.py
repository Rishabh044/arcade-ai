from enum import Enum


class GmailMessageReadStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    ALL = "all"


class GmailFolder(Enum):
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"
    TRASH = "trash"
    SPAM = "spam"
    IMPORTANT = "important"
    STARRED = "starred"
    SNOOZED = "snoozed"
