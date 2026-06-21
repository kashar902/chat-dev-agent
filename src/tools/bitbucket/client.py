import httpx
from typing import Any
from src.config import settings
from src.utils.logger import logger


class BitbucketClient:
    BASE_URL = "https://api.bitbucket.org/2.0"

    def __init__(self):
        self.headers = {"Authorization": f"Bearer {settings.bitbucket_api_token}"}
        self.workspace = settings.bitbucket_workspace

    def _client(self) -> httpx.Client:
        return httpx.Client(headers=self.headers, timeout=30.0)

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.BASE_URL}{path}"
        with self._client() as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    def _post(self, path: str, json: dict | None = None) -> Any:
        url = f"{self.BASE_URL}{path}"
        with self._client() as client:
            resp = client.post(url, json=json)
            resp.raise_for_status()
            return resp.json()

    def list_repositories(self) -> list[dict]:
        data = self._get(f"/repositories/{self.workspace}", {"pagelen": 50})
        return [
            {"slug": r["slug"], "name": r["name"], "description": r.get("description", "")}
            for r in data.get("values", [])
        ]

    def get_repo_info(self, repo_slug: str) -> dict:
        return self._get(f"/repositories/{self.workspace}/{repo_slug}")

    def get_file_tree(self, repo_slug: str, branch: str = "main", path: str = "") -> list[dict]:
        src_path = f"/repositories/{self.workspace}/{repo_slug}/src/{branch}/{path}"
        data = self._get(src_path)
        entries = []
        for entry in data.get("values", []):
            entries.append({
                "name": entry["name"],
                "type": entry["type"],
                "path": entry["path"],
            })
        return entries

    def read_file(self, repo_slug: str, branch: str, file_path: str) -> str:
        src_path = f"/repositories/{self.workspace}/{repo_slug}/src/{branch}/{file_path}"
        url = f"{self.BASE_URL}{src_path}"
        with self._client() as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text

    def search_code(self, repo_slug: str, query: str, branch: str = "main") -> list[dict]:
        src_path = f"/repositories/{self.workspace}/{repo_slug}/src/{branch}"
        data = self._get(f"/repositories/{self.workspace}/{repo_slug}/src/{branch}", {"q": query})
        results = []
        for entry in data.get("values", []):
            results.append({
                "name": entry["name"],
                "path": entry["path"],
                "type": entry["type"],
            })
        return results

    def create_branch(self, repo_slug: str, branch_name: str, source_branch: str = "main") -> dict:
        return self._post(
            f"/repositories/{self.workspace}/{repo_slug}/refs/branches",
            {"name": branch_name, "target": {"hash": source_branch}},
        )

    def commit_files(
        self, repo_slug: str, branch: str, files: list[dict], message: str
    ) -> dict:
        url = f"{self.BASE_URL}/repositories/{self.workspace}/{repo_slug}/src"
        payload = {"branch": branch, "message": message}
        for f in files:
            payload[f["path"]] = f["content"]
        with self._client() as client:
            resp = client.post(url, data=payload)
            resp.raise_for_status()
            return resp.json()

    def create_pull_request(
        self,
        repo_slug: str,
        source_branch: str,
        dest_branch: str = "main",
        title: str = "",
        description: str = "",
        reviewers: list[str] | None = None,
    ) -> dict:
        pr_data: dict[str, Any] = {
            "title": title,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": dest_branch}},
            "description": description,
        }
        if reviewers:
            pr_data["reviewers"] = [{"uuid": r} for r in reviewers]
        return self._post(
            f"/repositories/{self.workspace}/{repo_slug}/pullrequests", pr_data
        )

    def list_pull_requests(self, repo_slug: str, state: str = "OPEN") -> list[dict]:
        data = self._get(
            f"/repositories/{self.workspace}/{repo_slug}/pullrequests",
            {"state": state, "pagelen": 20},
        )
        return [
            {
                "id": pr["id"],
                "title": pr["title"],
                "author": pr["author"]["display_name"],
                "state": pr["state"],
                "url": pr["links"]["html"]["href"],
                "created_on": pr["created_on"],
            }
            for pr in data.get("values", [])
        ]

    def get_pull_request_diff(self, repo_slug: str, pr_id: int) -> str:
        url = f"{self.BASE_URL}/repositories/{self.workspace}/{repo_slug}/pullrequests/{pr_id}/diff"
        with self._client() as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
