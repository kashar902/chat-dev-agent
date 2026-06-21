from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    openai_api_key: str = ""
    bitbucket_workspace: str = ""
    bitbucket_username: str = ""
    bitbucket_app_password: str = ""
    google_chat_space_id: str = ""
    repos_dir: str = "./repos"
    model_name: str = "gpt-4o"

    @property
    def repos_path(self) -> Path:
        path = Path(self.repos_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ".env"


settings = Settings()
