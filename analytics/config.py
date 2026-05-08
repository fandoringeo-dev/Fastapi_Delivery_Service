from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalyticsSettings(BaseSettings):
    """
    Настройки аналитического контура.
    """

    mongodb_host: str
    mongodb_port: int
    mongodb_db: str

    clickhouse_host: str
    clickhouse_port: int
    clickhouse_db: str
    clickhouse_user: str
    clickhouse_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def mongodb_url(self) -> str:
        """
        Возвращает URL подключения к MongoDB.
        """
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/"


analytics_settings = AnalyticsSettings()
