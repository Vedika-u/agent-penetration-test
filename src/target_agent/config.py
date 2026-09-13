from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    memory_db_path: str = "data/memory.sqlite3"
    search_fixtures_path: str = "fixtures/search_fixtures.json"
    api_port: int = 8000


settings = Settings()
