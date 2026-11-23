"""Provider selection with an explicit guard against sample data in production."""

from app.core.config import settings
from app.core.errors import ConflictError
from app.providers.api_football import ApiFootballAdapter
from app.providers.base import ProviderAdapter
from app.providers.sample import SampleAdapter


def get_provider() -> ProviderAdapter:
    code = settings.football_data_provider.lower()
    if code == "api-football":
        return ApiFootballAdapter()
    if code == "sample":
        if settings.environment != "development" or not settings.allow_sample_data:
            raise ConflictError("Sample data is not permitted outside development.")
        return SampleAdapter()
    raise ConflictError(f"Unknown football data provider: {code}")
