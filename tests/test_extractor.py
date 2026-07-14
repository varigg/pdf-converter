from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.exceptions import ExtractionError, UnknownExtractorError
from pdf_converter.extractor import (
    SUPPORTED_EXTRACTORS,
    PDFExtractor,
    extract_text_from_pdf,
    get_extractor,
    mupdf_strategy,
    pypdf_strategy,
)


@patch("pypdf.PdfReader")
def test_pypdf_strategy(mock_reader_class: MagicMock) -> None:
    first_page = MagicMock()
    first_page.extract_text.return_value = "First page"
    blank_page = MagicMock()
    blank_page.extract_text.return_value = None
    mock_reader_class.return_value.pages = [first_page, blank_page]

    with patch("builtins.open", MagicMock()):
        assert pypdf_strategy("dummy.pdf") == "First page"


def test_pypdf_strategy_wraps_backend_errors() -> None:
    with (
        patch("builtins.open", side_effect=OSError("unreadable")),
        pytest.raises(ExtractionError, match="pypdf could not extract"),
    ):
        pypdf_strategy("dummy.pdf")


@patch("pymupdf4llm.to_markdown")
def test_mupdf_strategy(mock_to_markdown: MagicMock) -> None:
    mock_to_markdown.return_value = "MuPDF markdown"

    assert mupdf_strategy("dummy.pdf") == "MuPDF markdown"
    mock_to_markdown.assert_called_once_with("dummy.pdf")


def test_pdf_extractor_delegates_to_strategy() -> None:
    strategy = MagicMock(return_value="Mock text")

    assert PDFExtractor(strategy).extract("dummy.pdf") == "Mock text"
    strategy.assert_called_once_with("dummy.pdf")


def test_supported_extractors_match_factory() -> None:
    assert SUPPORTED_EXTRACTORS == ("pypdf", "mupdf")
    assert get_extractor("PYPDF").strategy is pypdf_strategy
    assert get_extractor("mupdf").strategy is mupdf_strategy


def test_get_extractor_rejects_unknown_backend() -> None:
    with pytest.raises(UnknownExtractorError, match="Unknown extractor"):
        get_extractor("invalid")


@patch("pdf_converter.extractor.get_extractor")
def test_extract_text_from_pdf(mock_get_extractor: MagicMock) -> None:
    mock_get_extractor.return_value.extract.return_value = "Extracted text"

    assert extract_text_from_pdf("dummy.pdf", "mupdf") == "Extracted text"
    mock_get_extractor.assert_called_once_with("mupdf")
    mock_get_extractor.return_value.extract.assert_called_once_with("dummy.pdf")
