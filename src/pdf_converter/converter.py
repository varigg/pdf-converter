import argparse
import os
import shutil

from pdf_converter.exceptions import OutputWriteError, PDFConverterError, PDFMoveError
from pdf_converter.extractor import SUPPORTED_EXTRACTORS, PDFExtractor, get_extractor
from pdf_converter.services import SUPPORTED_PROVIDERS
from pdf_converter.summarizer import summarize_text_with_llm


def write_output_to_md(
    content: str,
    original_file_name: str,
    stored_pdf_path: str | None,
    mode: str,
    output_dir: str = ".",
) -> str:
    """
    Writes the content (summary or raw text) to a Markdown file.
    """
    base_name = os.path.splitext(original_file_name)[0]
    suffix = "summary" if mode == "summarize" else "extracted"
    md_file_name = f"{base_name}_{suffix}.md"
    md_path = os.path.join(output_dir, md_file_name)

    title = "Summary of" if mode == "summarize" else "Extracted text from"

    print(f"Writing {mode} output to {md_path}...")
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title} {original_file_name}\n\n")
            if stored_pdf_path:
                f.write(f"**Original PDF moved to:** `{os.path.abspath(stored_pdf_path)}`\n\n")
            else:
                f.write("**Original PDF remained in its original location.**\n\n")
            f.write(content)
        print(f"{mode.capitalize()} file created successfully.")
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
    mode: str = "summarize",
    provider: str = "gemini",
) -> None:
    """
    Orchestrates the conversion or extraction using injected dependencies.
    """
    original_file_name = os.path.basename(pdf_file_path)

    # Step 1: Extract text from the PDF
    print(f"Extracting text from {original_file_name}...")
    extracted_text = extractor.extract(pdf_file_path)

    if mode == "summarize":
        # Step 2: Summarize the extracted text using an LLM
        print(f"Generating summary with {provider.upper()}...")
        output_content = summarize_text_with_llm(extracted_text, provider=provider)
    else:
        # Step 2: Use raw text
        output_content = extracted_text

    stored_pdf_path = None
    if storage_directory:
        stored_pdf_path = move_pdf_file(pdf_file_path, storage_directory)
    else:
        print(f"Original file '{original_file_name}' was not moved.")

    write_output_to_md(output_content, original_file_name, stored_pdf_path, mode)


def main(argv: list[str] | None = None) -> None:
    """
    Entry point for the console script.
    """
    parser = argparse.ArgumentParser(description="PDF Converter - Summarize or extract text from PDF files.")
    parser.add_argument("pdf_path", help="Path to the source PDF file")
    parser.add_argument(
        "storage_dir",
        nargs="?",
        default=None,
        help="Optional: Directory where the original PDF will be moved",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["summarize", "extract"],
        default="summarize",
        help="Operation mode: summarize (default) or extract (raw text)",
    )
    parser.add_argument(
        "--extractor",
        "-e",
        choices=SUPPORTED_EXTRACTORS,
        default="pypdf",
        help="PDF extraction library (default: pypdf)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        choices=SUPPORTED_PROVIDERS,
        default=None,
        help="LLM provider for summarization (default: reads from LLM_PROVIDER env var or 'gemini')",
    )

    args = parser.parse_args(argv)

    # Dependency Injection: Instantiate the extractor here
    extractor = get_extractor(args.extractor)

    # Determine LLM provider (CLI arg takes precedence over env var)
    provider = args.provider if args.provider else os.environ.get("LLM_PROVIDER", "gemini")

    try:
        run_conversion(args.pdf_path, args.storage_dir, extractor, args.mode, provider)
    except PDFConverterError as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
