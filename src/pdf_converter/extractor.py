from typing import Protocol, runtime_checkable

from .exceptions import ExtractionError, UnknownExtractorError


@runtime_checkable
class ExtractionStrategy(Protocol):
    """Protocol for extraction strategies."""

    def __call__(self, pdf_path: str) -> str: ...


def pypdf_strategy(pdf_path: str) -> str:
    """Extraction strategy using pypdf."""
    import pypdf

    try:
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(str(page_text))
            return "".join(pages)
    except Exception as error:
        message = f"pypdf could not extract text from '{pdf_path}'"
        raise ExtractionError(message) from error


def mupdf_strategy(pdf_path: str) -> str:
    """Extraction strategy using pymupdf4llm."""
    import pymupdf4llm

    try:
        return str(pymupdf4llm.to_markdown(pdf_path))
    except Exception as error:
        message = f"pymupdf4llm could not extract text from '{pdf_path}'"
        raise ExtractionError(message) from error


EXTRACTION_STRATEGIES: dict[str, ExtractionStrategy] = {
    "pypdf": pypdf_strategy,
    "mupdf": mupdf_strategy,
}
SUPPORTED_EXTRACTORS: tuple[str, ...] = tuple(EXTRACTION_STRATEGIES)


class PDFExtractor:
    """Main extractor class that uses composition (DI) to apply a strategy."""

    def __init__(self, strategy: ExtractionStrategy):
        self.strategy = strategy

    def extract(self, pdf_path: str) -> str:
        """Extracts text using the configured strategy."""
        return self.strategy(pdf_path)


def get_extractor(extractor_type: str) -> PDFExtractor:
    """Factory method to get an extractor with the desired strategy."""
    strategy = EXTRACTION_STRATEGIES.get(extractor_type.lower())
    if strategy is None:
        available = ", ".join(SUPPORTED_EXTRACTORS)
        message = f"Unknown extractor type '{extractor_type}'. Available: {available}"
        raise UnknownExtractorError(message)

    return PDFExtractor(strategy)


def extract_text_from_pdf(pdf_path: str, extractor_type: str = "pypdf") -> str:
    """
    Convenience function that uses the factory to extract text.
    """
    extractor = get_extractor(extractor_type)
    return extractor.extract(pdf_path)
