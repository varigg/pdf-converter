import os
import textwrap

from .services import LLMClientFactory


def summarize_text_with_llm(text_content: str, provider: str | None = None) -> str:
    """
    Summarizes a block of text using an LLM provider.

    Args:
        text_content (str): The text to summarize.
        provider (str | None): LLM provider to use ('gemini', 'perplexity', 'openai', 'anthropic').
                               If None, reads from LLM_PROVIDER env var or defaults to 'gemini'.

    Returns:
        str: The generated summary.
    
    Raises:
        ValueError: If API key is not configured for the selected provider.
        RuntimeError: If summary generation fails after all retries.
    """
    # Determine provider: parameter > env var > default
    if provider is None:
        provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    
    # Create system prompt - instructions for the LLM
    system_prompt = (
        "You are a helpful assistant that creates concise, informative summaries of documents. "
        "Focus on the main points and key takeaways. "
        "Provide a clear, well-structured summary."
    )
    
    # Create user prompt with the content to summarize
    user_prompt = f"""Please provide a concise summary of the following document content, focusing on the main points and key takeaways:

---
{text_content}
---"""

    try:
        # Create LLM client using factory
        llm_service = LLMClientFactory.create_client(provider=provider)
        
        # Generate summary with retry logic and error handling
        summary = llm_service.summarize_text(
            text=user_prompt,
            system_prompt=system_prompt,
            max_retries=3
        )
        
        # Use textwrap to format the summary nicely with line breaks
        wrapped_summary = textwrap.fill(summary, width=80)
        return wrapped_summary
        
    except ValueError as e:
        # API key or configuration error
        print(f"Configuration error: {e}")
        print(f"Please set the appropriate API key environment variable for provider '{provider}'.")
        raise
    except RuntimeError as e:
        # Generation failed after retries
        print(f"Failed to generate summary: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while generating the summary: {e}")
        raise
