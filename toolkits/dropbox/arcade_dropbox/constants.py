from arcade_dropbox.enums import Endpoint, EndpointType

API_BASE_URL = "https://{endpoint_type}.dropboxapi.com"
API_VERSION = "2"
ENDPOINT_URL_MAP = {
    Endpoint.LIST_FOLDER: (EndpointType.API, "files/list_folder"),
    Endpoint.SEARCH_FILES: (EndpointType.API, "files/search"),
    Endpoint.DOWNLOAD_FILE: (EndpointType.CONTENT, "files/download"),
}
