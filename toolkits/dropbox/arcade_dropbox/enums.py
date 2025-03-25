from enum import Enum


class DropboxEndpoint(Enum):
    LIST_FOLDER = "/files/list_folder"
    SEARCH_FILES = "/files/search"
