from backend.core.config import Settings


class TestSettings(Settings):
    """Настройки для тестового окружения"""
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    SECRET_KEY: str = "test-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


test_settings = TestSettings()