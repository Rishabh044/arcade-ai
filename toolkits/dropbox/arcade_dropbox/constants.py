from arcade_dropbox.enums import DropboxEndpoint

DROPBOX_BASE_URL = "https://api.dropboxapi.com"
DROPBOX_API_VERSION = "2"
DROPBOX_ENDPOINT_URL_MAP = {
    DropboxEndpoint.LIST_FOLDER: "files/list_folder",
    DropboxEndpoint.LIST_FOLDER_CONTINUE: "files/list_folder/continue",
}
