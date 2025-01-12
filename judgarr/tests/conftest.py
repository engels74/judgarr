"""Global pytest configuration."""

def pytest_configure(config):
    """Configure pytest-asyncio."""
    config.option.asyncio_default_fixture_loop_scope = "function"
