import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.exceptions import ExtractionError, UnknownExtractorError
from pdf_converter.extractor import (
    SUPPORTED_EXTRACTORS,
    ExtractionResult,
    PDFExtractor,
    calculate_extraction_quality,
    docling_ocr_strategy,
    docling_strategy,
    extract_pdf_with_metadata,
    extract_text_from_pdf,
    get_extractor,
    pypdf_strategy,
)


def _fake_docling_modules(converter_class: MagicMock) -> dict[str, ModuleType]:
    """Build importable stand-ins for the optional docling dependency."""
    base_models_module = ModuleType("docling.datamodel.base_models")
    base_models_module.InputFormat = MagicMock(name="InputFormat")  # type: ignore[attr-defined]
    pipeline_options_module = ModuleType("docling.datamodel.pipeline_options")
    pipeline_options_module.OcrAutoOptions = MagicMock(name="OcrAutoOptions")  # type: ignore[attr-defined]
    pipeline_options_module.PdfPipelineOptions = MagicMock(name="PdfPipelineOptions")  # type: ignore[attr-defined]
    datamodel_module = ModuleType("docling.datamodel")
    datamodel_module.base_models = base_models_module  # type: ignore[attr-defined]
    datamodel_module.pipeline_options = pipeline_options_module  # type: ignore[attr-defined]
    converter_module = ModuleType("docling.document_converter")
    converter_module.DocumentConverter = converter_class  # type: ignore[attr-defined]
    converter_module.PdfFormatOption = MagicMock(name="PdfFormatOption")  # type: ignore[attr-defined]
    docling_module = ModuleType("docling")
    docling_module.datamodel = datamodel_module  # type: ignore[attr-defined]
    docling_module.document_converter = converter_module  # type: ignore[attr-defined]
    return {
        "docling": docling_module,
        "docling.datamodel": datamodel_module,
        "docling.datamodel.base_models": base_models_module,
        "docling.datamodel.pipeline_options": pipeline_options_module,
        "docling.document_converter": converter_module,
    }


@patch("pypdf.PdfReader")
def test_pypdf_strategy(mock_reader_class: MagicMock) -> None:
    first_page = MagicMock()
    first_page.extract_text.return_value = "First page"
    blank_page = MagicMock()
    blank_page.extract_text.return_value = None
    mock_reader_class.return_value.pages = [first_page, blank_page]

    with patch("builtins.open", MagicMock()):
        assert pypdf_strategy("dummy.pdf") == "First page"


@patch("pypdf.PdfReader")
def test_extract_pdf_with_metadata_preserves_pypdf_page_offsets(mock_reader_class: MagicMock) -> None:
    first_page = MagicMock()
    first_page.extract_text.return_value = "First page"
    blank_page = MagicMock()
    blank_page.extract_text.return_value = None
    third_page = MagicMock()
    third_page.extract_text.return_value = "Third"
    mock_reader_class.return_value.pages = [first_page, blank_page, third_page]

    with patch("builtins.open", MagicMock()):
        result = extract_pdf_with_metadata("dummy.pdf")

    assert result.text == "First pageThird"
    assert result.page_offsets == (0, 10, 10)
    assert result.quality.page_count == 3
    assert result.quality.character_count == 15


def test_calculate_extraction_quality_flags_consonant_garble() -> None:
    quality = calculate_extraction_quality("A readable heading pqqqqrs follows.", page_count=1)

    assert quality.alphabetic_character_ratio > 0.9
    assert quality.suspicious_word_count == 1
    assert quality.garble_score == 0.2
    assert quality.is_likely_garbled


def test_calculate_extraction_quality_handles_empty_text() -> None:
    quality = calculate_extraction_quality("")

    assert quality.character_count == 0
    assert quality.alphabetic_character_ratio == 0.0
    assert quality.garble_score == 0.0
    assert not quality.is_likely_garbled


def test_pypdf_strategy_wraps_backend_errors() -> None:
    with (
        patch("builtins.open", side_effect=OSError("unreadable")),
        pytest.raises(ExtractionError, match="pypdf could not extract"),
    ):
        pypdf_strategy("dummy.pdf")


def test_docling_extraction_emits_page_markers_and_offsets() -> None:
    document = MagicMock()
    document.pages = {1: MagicMock(), 2: MagicMock(), 3: MagicMock()}
    page_markdown = {1: "# Title\n\nFirst page body", 2: "", 3: "Closing text"}
    document.export_to_markdown.side_effect = lambda *, page_no, traverse_pictures: page_markdown[page_no]
    converter_class = MagicMock()
    converter_class.return_value.convert.return_value.document = document

    with patch.dict(sys.modules, _fake_docling_modules(converter_class)):
        result = extract_pdf_with_metadata("dummy.pdf", "docling")

    assert result.text == (
        "<!-- page 1 -->\n# Title\n\nFirst page body\n\n<!-- page 2 -->\n<!-- page 3 -->\nClosing text\n\n"
    )
    assert len(result.page_offsets) == 3
    for page_number, offset in enumerate(result.page_offsets, start=1):
        assert result.text[offset:].startswith(f"<!-- page {page_number} -->")
    assert result.quality.page_count == 3
    converter_class.assert_called_once_with()
    converter_class.return_value.convert.assert_called_once_with("dummy.pdf")
    for call in document.export_to_markdown.call_args_list:
        # OCR text nested under picture items (map labels, handouts) is only
        # serialized when picture traversal is enabled.
        assert call.kwargs["traverse_pictures"] is True


def test_docling_ocr_extraction_emits_page_markers_and_offsets() -> None:
    document = MagicMock()
    document.pages = {1: MagicMock(), 2: MagicMock(), 3: MagicMock()}
    page_markdown = {1: "OCR text", 2: "", 3: "Final"}
    document.export_to_markdown.side_effect = lambda *, page_no, traverse_pictures: page_markdown[page_no]
    converter_class = MagicMock()
    converter_class.return_value.convert.return_value.document = document

    with patch.dict(sys.modules, _fake_docling_modules(converter_class)):
        result = extract_pdf_with_metadata("dummy.pdf", "docling-ocr")

    assert result.text == "<!-- page 1 -->\nOCR text\n\n<!-- page 2 -->\n<!-- page 3 -->\nFinal\n\n"
    assert result.page_offsets == (0, 26, 42)
    assert result.quality.page_count == 3
    assert result.text[result.page_offsets[1] :].startswith("<!-- page 2 -->")
    assert result.text[result.page_offsets[2] :].startswith("<!-- page 3 -->")
    for call in document.export_to_markdown.call_args_list:
        assert call.kwargs["traverse_pictures"] is True


def test_docling_ocr_requests_full_page_ocr() -> None:
    document = MagicMock()
    document.pages = {}
    converter_class = MagicMock()
    converter_class.return_value.convert.return_value.document = document
    fake_modules = _fake_docling_modules(converter_class)

    with patch.dict(sys.modules, fake_modules):
        extract_pdf_with_metadata("dummy.pdf", "docling-ocr")

    base_models_module = fake_modules["docling.datamodel.base_models"]
    pipeline_options_module = fake_modules["docling.datamodel.pipeline_options"]
    converter_module = fake_modules["docling.document_converter"]
    ocr_auto_options = pipeline_options_module.OcrAutoOptions
    pdf_pipeline_options = pipeline_options_module.PdfPipelineOptions
    pdf_format_option = converter_module.PdfFormatOption
    input_format = base_models_module.InputFormat

    ocr_auto_options.assert_called_once_with(force_full_page_ocr=True)
    pdf_pipeline_options.assert_called_once_with(do_ocr=True, ocr_options=ocr_auto_options.return_value)
    pdf_format_option.assert_called_once_with(pipeline_options=pdf_pipeline_options.return_value)
    converter_class.assert_called_once_with(
        format_options={input_format.PDF: pdf_format_option.return_value},
    )


def test_docling_strategy_returns_marked_markdown() -> None:
    document = MagicMock()
    document.pages = {1: MagicMock()}
    document.export_to_markdown.return_value = "Only page"
    converter_class = MagicMock()
    converter_class.return_value.convert.return_value.document = document

    with patch.dict(sys.modules, _fake_docling_modules(converter_class)):
        assert docling_strategy("dummy.pdf") == "<!-- page 1 -->\nOnly page\n\n"


def test_docling_strategy_reports_missing_optional_dependency() -> None:
    with (
        patch.dict(sys.modules, {"docling": None, "docling.document_converter": None}),
        pytest.raises(ExtractionError, match=r"pdf-converter\[docling\]"),
    ):
        docling_strategy("dummy.pdf")


def test_docling_strategy_wraps_backend_errors() -> None:
    converter_class = MagicMock()
    converter_class.return_value.convert.side_effect = RuntimeError("conversion failed")

    with (
        patch.dict(sys.modules, _fake_docling_modules(converter_class)),
        pytest.raises(ExtractionError, match="docling could not extract"),
    ):
        docling_strategy("dummy.pdf")


def test_docling_ocr_strategy_reports_missing_optional_dependency() -> None:
    with (
        patch.dict(sys.modules, {"docling": None, "docling.datamodel": None, "docling.document_converter": None}),
        pytest.raises(ExtractionError, match=r"pdf-converter\[docling\]"),
    ):
        docling_ocr_strategy("dummy.pdf")


def test_docling_ocr_strategy_wraps_backend_errors() -> None:
    converter_class = MagicMock()
    converter_class.return_value.convert.side_effect = RuntimeError("conversion failed")

    with (
        patch.dict(sys.modules, _fake_docling_modules(converter_class)),
        pytest.raises(ExtractionError, match="docling could not extract"),
    ):
        docling_ocr_strategy("dummy.pdf")


def test_pdf_extractor_delegates_to_strategy() -> None:
    strategy = MagicMock(return_value="Mock text")

    assert PDFExtractor(strategy).extract("dummy.pdf") == "Mock text"
    strategy.assert_called_once_with("dummy.pdf")


def test_supported_extractors_match_factory() -> None:
    assert SUPPORTED_EXTRACTORS == ("pypdf", "docling", "docling-ocr")
    assert get_extractor("PYPDF").strategy is pypdf_strategy
    assert get_extractor("DOCLING").strategy is docling_strategy
    assert get_extractor("DOCLING-OCR").strategy is docling_ocr_strategy


def test_get_extractor_rejects_unknown_backend() -> None:
    with pytest.raises(UnknownExtractorError, match="Unknown extractor"):
        get_extractor("invalid")


@patch("pdf_converter.extractor.get_extractor")
def test_extract_text_from_pdf(mock_get_extractor: MagicMock) -> None:
    mock_get_extractor.return_value.extract.return_value = "Extracted text"

    assert extract_text_from_pdf("dummy.pdf", "DOCLING") == "Extracted text"
    mock_get_extractor.assert_called_once_with("DOCLING")
    mock_get_extractor.return_value.extract.assert_called_once_with("dummy.pdf")


@patch("pdf_converter.extractor.EXTRACTION_RESULT_STRATEGIES")
def test_extract_pdf_with_metadata_uses_selected_backend(mock_strategies: MagicMock) -> None:
    expected = MagicMock(spec=ExtractionResult)
    strategy = MagicMock(return_value=expected)
    mock_strategies.get.return_value = strategy

    assert extract_pdf_with_metadata("dummy.pdf", "DOCLING") is expected
    mock_strategies.get.assert_called_once_with("docling")
    strategy.assert_called_once_with("dummy.pdf")
