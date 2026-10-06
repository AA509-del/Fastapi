"""应用配置：从环境变量与 .env 加载（pydantic-settings）。"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 课程字段：本项目主用智谱，OpenAI 可留空
    openai_api_key: str = ""
    # 兼容 .env 中 ZHIPU_API_KEY（课程）与 ZHIPUAI_API_KEY（LangChain 常用名）
    zhipu_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("ZHIPU_API_KEY", "ZHIPUAI_API_KEY"),
    )
    # 心知天气（Seniverse）
    seniverse_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("SENIVERSE_API_KEY", "SENIVERSE_KEY"),
    )

    db_path: str = "checkpointer.db"
    port: int = 8000

    database_url:str="postgresql+asyncpg://postgres:password@localhost:5432/agentdb"


settings = Settings()
