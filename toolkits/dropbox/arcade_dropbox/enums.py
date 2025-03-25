from enum import Enum


class DropboxEndpoint(Enum):
    LIST_FOLDER = "/files/list_folder"
    LIST_FOLDER_CONTINUE = "/files/list_folder/continue"
