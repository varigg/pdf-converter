from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.exceptions import UnknownProviderError
from pdf_converter.services.llm_client_factory import PROVIDER_FACTORIES, LLMClientFactory


def test_factory_builds_service_from_registry() -> None:
    provider = MagicMock()
    provider_factory = MagicMock(return_value=provider)

    with patch.dict(PROVIDER_FACTORIES, {"gemini": provider_factory}, clear=True):
        service = LLMClientFactory.create_client("GEMINI", api_key="key", model="model")

    provider_factory.assert_called_once_with("key", "model")
    assert service.provider is provider
    assert service.provider_name == "gemini"


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(UnknownProviderError, match="(?i)unsupported"):
        LLMClientFactory.create_client("unknown")


def test_factory_formats_provider_name() -> None:
    assert LLMClientFactory.get_client_type_name("some-provider") == "Some Provider"
