from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.extractor import (
    PDFExtractor,
    extract_text_from_pdf,
    get_extractor,
    mupdf_strategy,
    pypdf_strategy,
    unstructured_strategy,
)


@patch("pypdf.PdfReader")
def test_pypdf_strategy(mock_reader_class: MagicMock) -> None:
    mock_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PyPDF text"
    mock_reader.pages = [mock_page]
    mock_reader_class.return_value = mock_reader

    with patch("builtins.open", MagicMock()):
        result = pypdf_strategy("dummy.pdf")
        assert result == "PyPDF text"


@patch("pymupdf4llm.to_markdown")
def test_mupdf_strategy(mock_to_markdown: MagicMock) -> None:
    mock_to_markdown.return_value = "MuPDF markdown"
    result = mupdf_strategy("dummy.pdf")
    assert result == "MuPDF markdown"
    mock_to_markdown.assert_called_once_with("dummy.pdf")


def test_unstructured_strategy() -> None:
    # Use sys.modules patching to handle the local import in unstructured_strategy
    mock_partition = MagicMock()
    mock_pdf_module = MagicMock()
    mock_pdf_module.partition_pdf = mock_partition

    with patch.dict("sys.modules", {"unstructured.partition.pdf": mock_pdf_module}):
        mock_el = MagicMock()
        mock_el.__str__.return_value = "Unstructured text"
        mock_partition.return_value = [mock_el]

        result = unstructured_strategy("dummy.pdf")
        assert result == "Unstructured text"
        mock_partition.assert_called_once_with(filename="dummy.pdf")


def test_pdf_extractor() -> None:
    mock_strategy = MagicMock()
    mock_strategy.return_value = "Mock text"
    extractor = PDFExtractor(mock_strategy)
    result = extractor.extract("dummy.pdf")
    assert result == "Mock text"
    mock_strategy.assert_called_once_with("dummy.pdf")


def test_get_extractor() -> None:
    # Test that get_extractor returns a PDFExtractor with the correct strategy
    extractor = get_extractor("pypdf")
    assert isinstance(extractor, PDFExtractor)
    assert extractor.strategy == pypdf_strategy

    extractor = get_extractor("mupdf")
    assert isinstance(extractor, PDFExtractor)
    assert extractor.strategy == mupdf_strategy

    extractor = get_extractor("unstructured")
    assert isinstance(extractor, PDFExtractor)
    assert extractor.strategy == unstructured_strategy

    with pytest.raises(SystemExit):
        get_extractor("invalid")


@patch("pdf_converter.extractor.get_extractor")
def test_extract_text_from_pdf(mock_get_extractor: MagicMock) -> None:
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "Extracted text"
    mock_get_extractor.return_value = mock_extractor

    result = extract_text_from_pdf("dummy.pdf", "mupdf")
    assert result == "Extracted text"
    mock_get_extractor.assert_called_once_with("mupdf")
    mock_extractor.extract.assert_called_once_with("dummy.pdf")
