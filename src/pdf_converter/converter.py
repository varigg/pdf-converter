import argparse
import os
import shutil
import sys
from typing import Optional

from pdf_converter.extractor import PDFExtractor, get_extractor
from pdf_converter.summarizer import summarize_text_with_llm


def write_output_to_md(
    content: str,
    original_file_name: str,
    storage_dir: Optional[str],
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
            if storage_dir:
                f.write(f"**Original PDF moved to:** `{os.path.abspath(storage_dir)}`\n\n")
            else:
                f.write("**Original PDF remained in its original location.**\n\n")
            f.write(content)
        print(f"{mode.capitalize()} file created successfully.")
    except OSError as e:
        print(f"Error writing to Markdown file: {e}")
        sys.exit(1)
    else:
        return md_path


def move_pdf_file(pdf_path: str, storage_dir: str) -> None:
    """
    Moves the original PDF file to a specified storage location.
    """
    if not os.path.exists(storage_dir):
        print(f"Storage directory '{storage_dir}' does not exist. Creating it...")
        os.makedirs(storage_dir)

    file_name = os.path.basename(pdf_path)
    destination_path = os.path.join(storage_dir, file_name)

    print(f"Moving '{file_name}' to '{storage_dir}'...")
    try:
        shutil.move(pdf_path, destination_path)
        print("File moved successfully.")
    except shutil.Error as e:
        print(f"Error moving file: {e}")
    except OSError as e:
        print(f"Error moving file: {e}")


def run_conversion(
    pdf_file_path: str,
    storage_directory: Optional[str],
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

    # Step 3: Write the result to a Markdown file
    write_output_to_md(output_content, original_file_name, storage_directory, mode)

    # Step 4: Move the original PDF to the storage location (if provided)
    if storage_directory:
        move_pdf_file(pdf_file_path, storage_directory)
    else:
        print(f"Original file '{original_file_name}' was not moved.")


def main(argv: Optional[list[str]] = None) -> None:
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
        choices=["pypdf", "mupdf", "unstructured"],
        default="pypdf",
        help="PDF extraction library (default: pypdf)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        choices=["gemini", "perplexity", "openai", "anthropic"],
        default=None,
        help="LLM provider for summarization (default: reads from LLM_PROVIDER env var or 'gemini')",
    )

    # If argv is passed (e.g. from a test), it might include the script name as argv[0].
    # But argparse.parse_args() by default uses sys.argv[1:].
    # If we pass argv to parse_args(), it should be the list of arguments *excluding* the script name
    # OR if main is called with sys.argv, it has the script name.
    args = parser.parse_args(argv[1:] if argv else []) if argv is not None else parser.parse_args()

    # Dependency Injection: Instantiate the extractor here
    extractor = get_extractor(args.extractor)

    # Determine LLM provider (CLI arg takes precedence over env var)
    provider = args.provider if args.provider else os.environ.get("LLM_PROVIDER", "gemini")

    # Run the conversion
    run_conversion(args.pdf_path, args.storage_dir, extractor, args.mode, provider)


if __name__ == "__main__":
    main()
