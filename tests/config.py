from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    """
    Настройки тестового окружения.
    """

    postgres_host_test: str
    postgres_port_test: int
    postgres_db_test: str
    postgres_user_test: str
    postgres_password_test: str

    redis_host_test: str
    redis_port_test: int

    rabbitmq_host_test: str
    rabbitmq_port_test: int
    rabbitmq_user_test: str
    rabbitmq_password_test: str

    mongodb_host_test: str
    mongodb_port_test: int
    mongodb_db_test: str

    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def postgres_url_test(self) -> str:
        """
        Возвращает URL тестовой базы данных PostgreSQL.
        """
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user_test}:{self.postgres_password_test}"
            f"@{self.postgres_host_test}:{self.postgres_port_test}/"
            f"{self.postgres_db_test}"
        )

    @property
    def redis_url_test(self) -> str:
        """
        Возвращает URL тестового Redis.
        """
        return f"redis://{self.redis_host_test}:{self.redis_port_test}/0"

    @property
    def rabbitmq_url_test(self) -> str:
        """
        Возвращает URL тестового RabbitMQ.
        """
        return (
            f"amqp://{self.rabbitmq_user_test}:{self.rabbitmq_password_test}"
            f"@{self.rabbitmq_host_test}:{self.rabbitmq_port_test}/"
        )

    @property
    def mongodb_url_test(self) -> str:
        """
        Возвращает URL тестового MongoDB.
        """
        return f"mongodb://{self.mongodb_host_test}:{self.mongodb_port_test}/"


test_settings = TestSettings()
