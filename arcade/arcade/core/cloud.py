import requests


class CloudResource:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key

    def create_worker(self, name: str):
        response = requests.post(
            f"{self.url}/api/v1/workers",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"name": name},
            timeout=45,
        )
        return response

    def delete_worker(self, name: str):
        response = requests.delete(
            f"{self.url}/api/v1/workers/{name}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=45,
        )
        return response

    def upload_local_package(self, name: str, package_name: str, package_bytes: str):
        response = requests.patch(
            f"{self.url}/api/v1/workers/add_package/local",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "worker_name": name,
                "package_name": package_name,
                "package_bytes": package_bytes,
                "force": True,
            },
            timeout=120,
        )
        return response

    def upload_hosted_package(self, name: str, package_name: str):
        response = requests.patch(
            f"{self.url}/api/v1/workers/add_package/hosted",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"worker_name": name, "package_name": package_name, "force": True},
            timeout=45,
        )
        return response

    def remove_package(self, name: str, package_name: str):
        response = requests.patch(
            f"{self.url}/api/v1/workers/remove_package",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"worker_name": name, "package_name": package_name, "force": True},
            timeout=45,
        )
        return response
