"""Discord custom types for Arcade tools.

This module defines custom types, enums, and models for the Discord toolkit.
These types provide structured data representation for Discord API objects.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    """
    Discord channel types.

    Represents the different types of channels available in Discord.
    Used for channel creation and type identification.
    """

    TEXT = "text"
    VOICE = "voice"
    CATEGORY = "category"
    NEWS = "news"
    STORE = "store"
    FORUM = "forum"
    ANNOUNCEMENT = "announcement"
    STAGE = "stage"


class EmbedField(BaseModel):
    """
    Discord embed field model.

    Represents a single field in a Discord embed with name, value, and inline flag.
    Fields are used to structure information in an embed with titled sections.
    """

    name: str
    value: str
    inline: bool = False


class EmbedAuthor(BaseModel):
    """
    Discord embed author model.

    Represents the author section of a Discord embed, which appears at the top.
    Can include name, URL, and icon URL for the author.
    """

    name: str
    url: Optional[str] = None
    icon_url: Optional[str] = None


class EmbedFooter(BaseModel):
    """
    Discord embed footer model.

    Represents the footer section of a Discord embed, which appears at the bottom.
    Can include text and an icon URL.
    """

    text: str
    icon_url: Optional[str] = None


class EmbedImage(BaseModel):
    """
    Discord embed image model.

    Represents an image to be displayed in a Discord embed.
    Can specify a URL and optional dimensions.
    """

    url: str
    height: Optional[int] = None
    width: Optional[int] = None


class Embed(BaseModel):
    """
    Discord message embed model.

    Represents a rich embed that can be included with Discord messages.
    Embeds can contain formatted text, fields, images, and other rich content.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[int] = None
    timestamp: Optional[datetime] = None
    fields: List[Union[EmbedField, Dict[str, Any]]] = Field(default_factory=list)
    author: Optional[Union[EmbedAuthor, Dict[str, Any]]] = None
    footer: Optional[Union[EmbedFooter, Dict[str, Any]]] = None
    image: Optional[Union[EmbedImage, Dict[str, Any]]] = None
    thumbnail: Optional[Union[EmbedImage, Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to Discord API format dict.

        Returns:
            Dict representing this embed in the format expected by the Discord API
        """
        result = {}
        if self.title is not None:
            result["title"] = self.title
        if self.description is not None:
            result["description"] = self.description
        if self.url is not None:
            result["url"] = self.url
        if self.color is not None:
            result["color"] = self.color
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp.isoformat()
        if self.fields:
            result["fields"] = [
                field.dict() if isinstance(field, EmbedField) else field
                for field in self.fields
            ]
        if self.author is not None:
            result["author"] = (
                self.author.dict()
                if isinstance(self.author, EmbedAuthor)
                else self.author
            )
        if self.footer is not None:
            result["footer"] = (
                self.footer.dict()
                if isinstance(self.footer, EmbedFooter)
                else self.footer
            )
        if self.image is not None:
            result["image"] = (
                self.image.dict() if isinstance(self.image, EmbedImage) else self.image
            )
        if self.thumbnail is not None:
            result["thumbnail"] = (
                self.thumbnail.dict()
                if isinstance(self.thumbnail, EmbedImage)
                else self.thumbnail
            )

        return result


@dataclass
class Message:
    """
    Discord message representation.

    Represents a message in a Discord channel, including content, author,
    and metadata such as creation time and any included embeds.
    """

    id: str
    content: str
    author: Dict[str, Any]
    channel_id: str
    created_at: datetime
    embeds: List[Dict[str, Any]]
    attachments: List[Dict[str, Any]]
    mentions: List[Dict[str, Any]]
    mention_roles: List[str]
    edited_at: Optional[datetime] = None


@dataclass
class Channel:
    """
    Discord channel representation.

    Represents a channel in a Discord server, including its type,
    name, and related metadata.
    """

    id: str
    type: ChannelType
    name: str
    guild_id: Optional[str] = None
    position: Optional[int] = None
    topic: Optional[str] = None
    nsfw: bool = False
    parent_id: Optional[str] = None


@dataclass
class Server:
    """
    Discord server (guild) representation.

    Represents a Discord server/guild with its basic information
    such as name, icon, and member count.
    """

    id: str
    name: str
    icon: Optional[str] = None
    owner_id: Optional[str] = None
    member_count: Optional[int] = None
    description: Optional[str] = None
