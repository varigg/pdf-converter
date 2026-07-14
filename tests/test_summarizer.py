from unittest.mock import MagicMock, patch

from pdf_converter.summarizer import summarize_text_with_llm


@patch("pdf_converter.summarizer.LLMClientFactory.create_client")
def test_summarize_text_with_llm(mock_create_client: MagicMock) -> None:
    """Test summarize_text_with_llm with mocked LLM service."""
    # Create mock LLM service
    mock_service = MagicMock()
    mock_service.summarize_text.return_value = "This is a summary."
    mock_create_client.return_value = mock_service

    # Call the function
    result = summarize_text_with_llm("Some long text")
    
    # Verify the factory was called with default provider
    mock_create_client.assert_called_once_with(provider="gemini")
    
    # Verify the service's summarize_text was called
    mock_service.summarize_text.assert_called_once()
    
    # Verify the result contains the summary
    assert "This is a summary." in result


@patch("pdf_converter.summarizer.LLMClientFactory.create_client")
def test_summarize_text_with_llm_custom_provider(mock_create_client: MagicMock) -> None:
    """Test summarize_text_with_llm with custom provider."""
    # Create mock LLM service
    mock_service = MagicMock()
    mock_service.summarize_text.return_value = "This is a summary from OpenAI."
    mock_create_client.return_value = mock_service

    # Call the function with custom provider
    result = summarize_text_with_llm("Some long text", provider="openai")
    
    # Verify the factory was called with the custom provider
    mock_create_client.assert_called_once_with(provider="openai")
    
    # Verify the result contains the summary
    assert "This is a summary from OpenAI." in result

