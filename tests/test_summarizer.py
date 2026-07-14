from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.exceptions import SummarizationError
from pdf_converter.summarizer import summarize_text_with_llm


@patch("pdf_converter.summarizer.LLMClientFactory.create_client")
def test_summarize_text_with_default_provider(mock_create_client: MagicMock) -> None:
    mock_create_client.return_value.summarize_text.return_value = "This is a summary."

    result = summarize_text_with_llm("Some long text")

    assert result == "This is a summary."
    mock_create_client.assert_called_once_with(provider="gemini")
    mock_create_client.return_value.summarize_text.assert_called_once()


@patch("pdf_converter.summarizer.LLMClientFactory.create_client")
def test_summarize_text_with_custom_provider(mock_create_client: MagicMock) -> None:
    mock_create_client.return_value.summarize_text.return_value = "OpenAI summary."

    assert summarize_text_with_llm("Some long text", provider="openai") == "OpenAI summary."
    mock_create_client.assert_called_once_with(provider="openai")


@patch("pdf_converter.summarizer.LLMClientFactory.create_client")
def test_summarizer_wraps_provider_errors(mock_create_client: MagicMock) -> None:
    mock_create_client.side_effect = ValueError("missing key")

    with pytest.raises(SummarizationError, match="provider 'gemini'"):
        summarize_text_with_llm("Some long text")
