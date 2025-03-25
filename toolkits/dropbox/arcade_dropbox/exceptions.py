class DropboxApiError(Exception):
    pass


class DropboxPathNotFoundError(DropboxApiError):
    pass
