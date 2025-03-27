from typing import Any, Optional


class DropboxApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error_summary: str,
        user_message: Optional[str],
    ):
        if "path/not_found" in error_summary:
            self.message = "The specified path was not found by Dropbox"
        elif "unsupported_file" in error_summary:
            self.message = "The specified file is not supported for the requested operation"
        else:
            self.message = user_message or error_summary

        self.status_code = status_code


class DropboxPathError(Exception):
    def __init__(self, path: Any):
        self.message = f"Path must be a string, got '{type(path).__name__}({path})', instead."
