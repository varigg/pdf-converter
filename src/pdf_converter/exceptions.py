"""Domain exceptions raised by :mod:`pdf_converter`."""


class PDFConverterError(Exception):
    """Base class for errors that the command-line interface can report cleanly."""


class ExtractionError(PDFConverterError):
    """Raised when a PDF backend cannot extract text."""


class UnknownExtractorError(PDFConverterError, ValueError):
    """Raised when an unsupported extraction backend is requested."""


class OutputWriteError(PDFConverterError):
    """Raised when converted content cannot be written."""


class PDFMoveError(PDFConverterError):
    """Raised when the source PDF cannot be moved."""


class SummarizationError(PDFConverterError):
    """Raised when an LLM cannot summarize extracted text."""


class MissingAPIKeyError(PDFConverterError, ValueError):
    """Raised when an LLM provider's API key is not configured."""

    def __init__(self, provider: str, environment_variable: str):
        super().__init__(f"{provider} API key required. Set {environment_variable}.")


class UnknownProviderError(PDFConverterError, ValueError):
    """Raised when an unsupported LLM provider is requested."""

    def __init__(self, provider: str, available: str):
        super().__init__(f"Unsupported provider '{provider}'. Available: {available}")


class ProviderResponseError(PDFConverterError):
    """Raised when an LLM provider returns an unexpected response."""

    def __init__(self, provider: str):
        super().__init__(f"{provider} returned an invalid response")


class LLMRetryError(PDFConverterError, RuntimeError):
    """Raised when retryable LLM requests exhaust their attempts."""

    def __init__(self, attempts: int, status_code: int = 0):
        reason = f"HTTP {status_code}" if status_code else "a network error"
        super().__init__(f"LLM request failed after {attempts} attempts due to {reason}")


class InvalidRetryCountError(PDFConverterError, ValueError):
    """Raised when an invalid retry count is supplied."""

    def __init__(self):
        super().__init__("max_retries must be at least 1")
