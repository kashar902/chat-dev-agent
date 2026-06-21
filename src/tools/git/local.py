import git
import shutil
from pathlib import Path
from src.config import settings
from src.utils.logger import logger


class GitManager:
    def __init__(self):
        self.repos_dir = settings.repos_path

    def _repo_path(self, repo_slug: str) -> Path:
        return self.repos_dir / repo_slug

    def clone(self, repo_slug: str, branch: str = "main") -> git.Repo:
        repo_path = self._repo_path(repo_slug)
        if repo_path.exists():
            shutil.rmtree(repo_path)
        url = f"https://x-token-auth:{settings.bitbucket_api_token}@bitbucket.org/{settings.bitbucket_workspace}/{repo_slug}.git"
        logger.info(f"Cloning {repo_slug} into {repo_path}")
        repo = git.Repo.clone_from(url, str(repo_path), branch=branch)
        return repo

    def get_or_clone(self, repo_slug: str, branch: str = "main") -> git.Repo:
        repo_path = self._repo_path(repo_slug)
        if repo_path.exists() and (repo_path / ".git").exists():
            repo = git.Repo(str(repo_path))
            repo.remotes.origin.pull()
            return repo
        return self.clone(repo_slug, branch)

    def create_branch(self, repo_slug: str, branch_name: str) -> git.Repo:
        repo = self.get_or_clone(repo_slug)
        repo.git.checkout("-b", branch_name)
        return repo

    def commit(self, repo_slug: str, message: str) -> None:
        repo = self.get_or_clone(repo_slug)
        repo.git.add(A=True)
        repo.index.commit(message)

    def push(self, repo_slug: str, branch: str) -> None:
        repo = self.get_or_clone(repo_slug)
        repo.remotes.origin.push(refspec=f"{branch}:{branch}")

    def list_files(self, repo_slug: str, path: str = "") -> list[str]:
        repo = self.get_or_clone(repo_slug)
        repo_path = Path(repo.working_dir)
        target = repo_path / path if path else repo_path
        files = []
        for item in target.iterdir():
            if item.name.startswith("."):
                continue
            rel = item.relative_to(repo_path)
            files.append(str(rel) + ("/" if item.is_dir() else ""))
        return sorted(files)

    def read_file(self, repo_slug: str, file_path: str) -> str:
        repo = self.get_or_clone(repo_slug)
        file = Path(repo.working_dir) / file_path
        if not file.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file.read_text(encoding="utf-8")

    def write_file(self, repo_slug: str, file_path: str, content: str) -> None:
        repo = self.get_or_clone(repo_slug)
        file = Path(repo.working_dir) / file_path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
