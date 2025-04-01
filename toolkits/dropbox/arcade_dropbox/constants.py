from enum import Enum


class EndpointType(Enum):
    API = "api"
    CONTENT = "content"


class Endpoint(Enum):
    LIST_FOLDER = "/files/list_folder"
    SEARCH_FILES = "/files/search"
    DOWNLOAD_FILE = "/files/download"


class ItemCategory(Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    AUDIO = "audio"
    VIDEO = "video"
    FOLDER = "folder"
    PAPER = "paper"


API_BASE_URL = "https://{endpoint_type}.dropboxapi.com"
API_VERSION = "2"
ENDPOINT_URL_MAP = {
    Endpoint.LIST_FOLDER: (EndpointType.API, "files/list_folder"),
    Endpoint.SEARCH_FILES: (EndpointType.API, "files/search_v2"),
    Endpoint.DOWNLOAD_FILE: (EndpointType.CONTENT, "files/download"),
}
MAX_RESPONSE_BODY_SIZE = 10 * 1024 * 1024  # 10 MiB
