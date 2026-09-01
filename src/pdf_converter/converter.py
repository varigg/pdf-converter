import argparse
import os
import shutil

from pdf_converter.exceptions import OutputWriteError, PDFConverterError, PDFMoveError
from pdf_converter.extractor import SUPPORTED_EXTRACTORS, PDFExtractor, get_extractor


def write_output_to_md(
    content: str,
    original_file_name: str,
    stored_pdf_path: str | None,
    output_dir: str = ".",
) -> str:
    """
    Writes extracted text to a Markdown file.
    """
    base_name = os.path.splitext(original_file_name)[0]
    md_file_name = f"{base_name}_extracted.md"
    md_path = os.path.join(output_dir, md_file_name)

    print(f"Writing extracted output to {md_path}...")
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Extracted text from {original_file_name}\n\n")
            if stored_pdf_path:
                f.write(f"**Original PDF moved to:** `{os.path.abspath(stored_pdf_path)}`\n\n")
            else:
                f.write("**Original PDF remained in its original location.**\n\n")
            f.write(content)
        print("Extracted file created successfully.")
    except OSError as error:
        message = f"Could not write Markdown output to '{md_path}'"
        raise OutputWriteError(message) from error
    else:
        return md_path


def move_pdf_file(pdf_path: str, storage_dir: str) -> str:
    """
    Moves the original PDF file to a specified storage location.
    """
    if not os.path.exists(storage_dir):
        print(f"Storage directory '{storage_dir}' does not exist. Creating it...")
    file_name = os.path.basename(pdf_path)
    destination_path = os.path.join(storage_dir, file_name)
    try:
        os.makedirs(storage_dir, exist_ok=True)
        print(f"Moving '{file_name}' to '{storage_dir}'...")
        moved_path = shutil.move(pdf_path, destination_path)
    except (OSError, shutil.Error) as error:
        message = f"Could not move '{pdf_path}' to '{destination_path}'"
        raise PDFMoveError(message) from error
    else:
        print("File moved successfully.")
        return moved_path


def run_conversion(
    pdf_file_path: str,
    storage_directory: str | None,
    extractor: PDFExtractor,
) -> None:
    """
    Orchestrates extraction using injected dependencies.
    """
    original_file_name = os.path.basename(pdf_file_path)

    # Step 1: Extract text from the PDF
    print(f"Extracting text from {original_file_name}...")
    extracted_text = extractor.extract(pdf_file_path)

    stored_pdf_path = None
    if storage_directory:
        stored_pdf_path = move_pdf_file(pdf_file_path, storage_directory)
    else:
        print(f"Original file '{original_file_name}' was not moved.")

    write_output_to_md(extracted_text, original_file_name, stored_pdf_path)


def main(argv: list[str] | None = None) -> None:
    """
    Entry point for the console script.
    """
    parser = argparse.ArgumentParser(description="Extract text from PDF files.")
    parser.add_argument("pdf_path", help="Path to the source PDF file")
    parser.add_argument(
        "storage_dir",
        nargs="?",
        default=None,
        help="Optional: Directory where the original PDF will be moved",
    )
    parser.add_argument(
        "--extractor",
        "-e",
        choices=SUPPORTED_EXTRACTORS,
        default="pypdf",
        help="PDF extraction library (default: pypdf)",
    )
    args = parser.parse_args(argv)

    # Dependency Injection: Instantiate the extractor here
    extractor = get_extractor(args.extractor)

    try:
        run_conversion(args.pdf_path, args.storage_dir, extractor)
    except PDFConverterError as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
