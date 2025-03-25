from enum import Enum


class EndpointType(Enum):
    API = "api"
    CONTENT = "content"


class Endpoint(Enum):
    LIST_FOLDER = "/files/list_folder"
    SEARCH_FILES = "/files/search"
    DOWNLOAD_FILE = "/files/download"
