from unittest.mock import MagicMock, patch

from pdf_converter.converter import run_conversion


@patch("pdf_converter.converter.summarize_text_with_llm")
@patch("pdf_converter.converter.write_output_to_md")
@patch("pdf_converter.converter.move_pdf_file")
def test_run_conversion_summarize(
    mock_move: MagicMock,
    mock_write: MagicMock,
    mock_summarize: MagicMock,
) -> None:
    # Arrange
    pdf_path = "test.pdf"
    storage_dir = "storage"
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "Extracted text"
    mock_summarize.return_value = "Summary text"

    # Act
    run_conversion(pdf_path, storage_dir, mock_extractor, mode="summarize")

    # Assert
    mock_extractor.extract.assert_called_once_with(pdf_path)
    mock_summarize.assert_called_once_with("Extracted text", provider="gemini")
    mock_write.assert_called_once_with("Summary text", "test.pdf", storage_dir, "summarize")
    mock_move.assert_called_once_with(pdf_path, storage_dir)


@patch("pdf_converter.converter.summarize_text_with_llm")
@patch("pdf_converter.converter.write_output_to_md")
@patch("pdf_converter.converter.move_pdf_file")
def test_run_conversion_extract(
    mock_move: MagicMock,
    mock_write: MagicMock,
    mock_summarize: MagicMock,
) -> None:
    # Arrange
    pdf_path = "test.pdf"
    storage_dir = "storage"
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "Extracted text"

    # Act
    run_conversion(pdf_path, storage_dir, mock_extractor, mode="extract")

    # Assert
    mock_extractor.extract.assert_called_once_with(pdf_path)
    mock_summarize.assert_not_called()
    mock_write.assert_called_once_with("Extracted text", "test.pdf", storage_dir, "extract")
    mock_move.assert_called_once_with(pdf_path, storage_dir)


@patch("pdf_converter.converter.summarize_text_with_llm")
@patch("pdf_converter.converter.write_output_to_md")
@patch("pdf_converter.converter.move_pdf_file")
def test_run_conversion_no_storage_dir(
    mock_move: MagicMock,
    mock_write: MagicMock,
    mock_summarize: MagicMock,
) -> None:
    # Arrange
    pdf_path = "test.pdf"
    storage_dir = None
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "Extracted text"
    mock_summarize.return_value = "Summary text"

    # Act
    run_conversion(pdf_path, storage_dir, mock_extractor, mode="summarize")

    # Assert
    mock_extractor.extract.assert_called_once_with(pdf_path)
    mock_summarize.assert_called_once_with("Extracted text", provider="gemini")
    mock_write.assert_called_once_with("Summary text", "test.pdf", None, "summarize")
    mock_move.assert_not_called()
