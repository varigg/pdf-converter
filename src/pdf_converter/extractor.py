import sys
from typing import Protocol, runtime_checkable


@runtime_checkable
class ExtractionStrategy(Protocol):
    """Protocol for extraction strategies."""

    def __call__(self, pdf_path: str) -> str:
        ...


def pypdf_strategy(pdf_path: str) -> str:
    """Extraction strategy using pypdf."""
    import pypdf

    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += str(page_text)
    except Exception as e:
        print(f"Error using pypdf: {e}")
        sys.exit(1)
    return text


def mupdf_strategy(pdf_path: str) -> str:
    """Extraction strategy using pymupdf4llm."""
    import pymupdf4llm

    try:
        return str(pymupdf4llm.to_markdown(pdf_path))
    except Exception as e:
        print(f"Error using pymupdf4llm: {e}")
        sys.exit(1)


class PDFExtractor:
    """Main extractor class that uses composition (DI) to apply a strategy."""

    def __init__(self, strategy: ExtractionStrategy):
        self.strategy = strategy

    def extract(self, pdf_path: str) -> str:
        """Extracts text using the configured strategy."""
        return self.strategy(pdf_path)


def get_extractor(extractor_type: str) -> PDFExtractor:
    """Factory method to get an extractor with the desired strategy."""
    strategies: dict[str, ExtractionStrategy] = {
        "pypdf": pypdf_strategy,
        "mupdf": mupdf_strategy,
    }

    strategy = strategies.get(extractor_type.lower())
    if not strategy:
        available = ", ".join(strategies.keys())
        print(f"Error: Unknown extractor type '{extractor_type}'. Available: {available}")
        sys.exit(1)

    return PDFExtractor(strategy)


def extract_text_from_pdf(pdf_path: str, extractor_type: str = "pypdf") -> str:
    """
    Convenience function that uses the factory to extract text.
    """
    extractor = get_extractor(extractor_type)
    return extractor.extract(pdf_path)
