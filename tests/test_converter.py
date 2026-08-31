from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.converter import main, move_pdf_file, run_conversion, write_output_to_md
from pdf_converter.exceptions import PDFMoveError


@patch("pdf_converter.converter.write_output_to_md")
@patch("pdf_converter.converter.move_pdf_file", return_value="storage/test.pdf")
def test_run_conversion(
    mock_move: MagicMock,
    mock_write: MagicMock,
) -> None:
    extractor = MagicMock()
    extractor.extract.return_value = "Extracted text"

    run_conversion("test.pdf", "storage", extractor)

    mock_move.assert_called_once_with("test.pdf", "storage")
    mock_write.assert_called_once_with("Extracted text", "test.pdf", "storage/test.pdf")


@patch("pdf_converter.converter.write_output_to_md")
@patch("pdf_converter.converter.move_pdf_file")
def test_run_conversion_does_not_claim_failed_move(mock_move: MagicMock, mock_write: MagicMock) -> None:
    extractor = MagicMock()
    extractor.extract.return_value = "Extracted text"
    mock_move.side_effect = PDFMoveError("move failed")

    with pytest.raises(PDFMoveError, match="move failed"):
        run_conversion("test.pdf", "storage", extractor)

    mock_write.assert_not_called()


def test_write_output_records_actual_moved_path(tmp_path: Path) -> None:
    output_path = write_output_to_md(
        "Content",
        "source.pdf",
        "/archive/source.pdf",
        str(tmp_path),
    )

    output = Path(output_path).read_text(encoding="utf-8")
    assert "`/archive/source.pdf`" in output
    assert output.endswith("Content")


def test_move_pdf_file_returns_destination(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_text("pdf", encoding="utf-8")
    storage = tmp_path / "archive"

    moved_path = move_pdf_file(str(source), str(storage))

    assert Path(moved_path) == storage / source.name
    assert not source.exists()


@patch("pdf_converter.converter.run_conversion")
@patch("pdf_converter.converter.get_extractor")
def test_main_accepts_argument_list_without_program_name(
    mock_get_extractor: MagicMock,
    mock_run_conversion: MagicMock,
) -> None:
    main(["document.pdf", "--extractor", "mupdf"])

    mock_get_extractor.assert_called_once_with("mupdf")
    mock_run_conversion.assert_called_once_with(
        "document.pdf",
        None,
        mock_get_extractor.return_value,
    )
