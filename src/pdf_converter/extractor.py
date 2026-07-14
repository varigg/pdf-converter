import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .exceptions import ExtractionError, UnknownExtractorError


@runtime_checkable
class ExtractionStrategy(Protocol):
    """Protocol for extraction strategies."""

    def __call__(self, pdf_path: str) -> str: ...


@dataclass(frozen=True)
class ExtractionQuality:
    """Signals a caller can use to identify likely-bad text extraction."""

    page_count: int
    character_count: int
    alphabetic_character_ratio: float
    suspicious_word_count: int
    garble_score: float

    @property
    def is_likely_garbled(self) -> bool:
        """Whether the text contains a material share of suspicious tokens."""
        return self.garble_score >= 0.05


@dataclass(frozen=True)
class ExtractionResult:
    """Extracted text together with provenance and quality metadata.

    ``page_offsets`` contains one character offset for each source PDF page.
    The entry at index ``page_number - 1`` is the position where that page's
    text begins in ``text``. Empty pages therefore still retain a boundary.
    An empty tuple means that the selected backend did not preserve pages.
    """

    text: str
    page_offsets: tuple[int, ...]
    quality: ExtractionQuality


_WORD_PATTERN = re.compile(r"[^\W\d_]+", re.UNICODE)
_CONSONANT_RUN_PATTERN = re.compile(r"[bcdfghjklmnpqrstvwxyz]{6,}", re.IGNORECASE)


def calculate_extraction_quality(text: str, page_count: int = 0) -> ExtractionQuality:
    """Calculate lightweight, language-independent extraction quality signals.

    ``garble_score`` is the fraction of alphabetic tokens containing a run of
    at least six consonants, a common symptom of broken font encodings. It is
    deliberately a signal rather than a rejection rule so callers can choose
    their own threshold and review process.
    """
    non_whitespace_characters = "".join(text.split())
    alphabetic_characters = sum(character.isalpha() for character in non_whitespace_characters)
    words = _WORD_PATTERN.findall(text)
    suspicious_word_count = sum(bool(_CONSONANT_RUN_PATTERN.search(word)) for word in words)

    return ExtractionQuality(
        page_count=page_count,
        character_count=len(text),
        alphabetic_character_ratio=(alphabetic_characters / len(non_whitespace_characters))
        if non_whitespace_characters
        else 0.0,
        suspicious_word_count=suspicious_word_count,
        garble_score=(suspicious_word_count / len(words)) if words else 0.0,
    )


def pypdf_extraction_result(pdf_path: str) -> ExtractionResult:
    """Extract text and page boundaries using pypdf."""
    import pypdf

    try:
        with open(pdf_path, "rb") as file:
            reader = pypdf.PdfReader(file)
            pages: list[str] = []
            page_offsets: list[int] = []
            character_offset = 0
            for page in reader.pages:
                page_offsets.append(character_offset)
                page_text = page.extract_text()
                if page_text:
                    page_text = str(page_text)
                    pages.append(page_text)
                    character_offset += len(page_text)
            text = "".join(pages)
            return ExtractionResult(
                text=text,
                page_offsets=tuple(page_offsets),
                quality=calculate_extraction_quality(text, page_count=len(page_offsets)),
            )
    except Exception as error:
        message = f"pypdf could not extract text from '{pdf_path}'"
        raise ExtractionError(message) from error


def pypdf_strategy(pdf_path: str) -> str:
    """Extraction strategy using pypdf."""
    return pypdf_extraction_result(pdf_path).text


def mupdf_strategy(pdf_path: str) -> str:
    """Extraction strategy using pymupdf4llm."""
    import pymupdf4llm

    try:
        return str(pymupdf4llm.to_markdown(pdf_path))
    except Exception as error:
        message = f"pymupdf4llm could not extract text from '{pdf_path}'"
        raise ExtractionError(message) from error


def mupdf_extraction_result(pdf_path: str) -> ExtractionResult:
    """Extract MuPDF Markdown and attach quality metadata when pages are unavailable."""
    text = mupdf_strategy(pdf_path)
    return ExtractionResult(text=text, page_offsets=(), quality=calculate_extraction_quality(text))


EXTRACTION_STRATEGIES: dict[str, ExtractionStrategy] = {
    "pypdf": pypdf_strategy,
    "mupdf": mupdf_strategy,
}
EXTRACTION_RESULT_STRATEGIES = {
    "pypdf": pypdf_extraction_result,
    "mupdf": mupdf_extraction_result,
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


def extract_pdf_with_metadata(pdf_path: str, extractor_type: str = "pypdf") -> ExtractionResult:
    """Extract PDF text together with page offsets and quality signals.

    This is additive to :func:`extract_text_from_pdf`; callers that only need
    plain text can continue using the original function unchanged.
    """
    extractor_name = extractor_type.lower()
    strategy = EXTRACTION_RESULT_STRATEGIES.get(extractor_name)
    if strategy is None:
        available = ", ".join(SUPPORTED_EXTRACTORS)
        message = f"Unknown extractor type '{extractor_type}'. Available: {available}"
        raise UnknownExtractorError(message)

    return strategy(pdf_path)
