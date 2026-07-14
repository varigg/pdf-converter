#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat >&2 <<EOF
Usage: $0 [options] <folder>

Converts all PDF files in <folder> to Markdown using pdf-converter.
Output .md files are written to the current working directory.

Options:
  -m, --mode <mode>          summarize|extract  (default: summarize)
  -e, --extractor <lib>      pypdf|mupdf  (default: pypdf)
  -p, --provider <llm>       gemini|perplexity|openai|anthropic
  -r, --recursive            also search sub-directories
  -h, --help                 show this help
EOF
    exit 1
}

mode=""
extractor=""
provider=""
recursive=false
folder=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--mode)      mode="$2";      shift 2 ;;
        -e|--extractor) extractor="$2"; shift 2 ;;
        -p|--provider)  provider="$2";  shift 2 ;;
        -r|--recursive) recursive=true; shift ;;
        -h|--help)      usage ;;
        -*)             echo "Unknown option: $1" >&2; usage ;;
        *)              folder="$1";    shift ;;
    esac
done

[[ -z "$folder" ]] && usage
[[ ! -d "$folder" ]] && { echo "Error: '$folder' is not a directory." >&2; exit 1; }

# Build extra args to forward
extra_args=()
[[ -n "$mode" ]]      && extra_args+=(--mode "$mode")
[[ -n "$extractor" ]] && extra_args+=(--extractor "$extractor")
[[ -n "$provider" ]]  && extra_args+=(--provider "$provider")

# Collect PDFs
mapfile -d '' pdfs < <(
    if $recursive; then
        find "$folder" -type f -iname "*.pdf" -print0 | sort -z
    else
        find "$folder" -maxdepth 1 -type f -iname "*.pdf" -print0 | sort -z
    fi
)

if [[ ${#pdfs[@]} -eq 0 ]]; then
    echo "No PDF files found in '$folder'." >&2
    exit 0
fi

echo "Found ${#pdfs[@]} PDF file(s). Output will be written to: $(pwd)"
echo

failed=0
for pdf in "${pdfs[@]}"; do
    echo "--- Converting: $pdf"
    if pdf-converter "${extra_args[@]}" "$pdf"; then
        echo "    OK"
    else
        echo "    FAILED" >&2
        ((failed++)) || true
    fi
    echo
done

echo "Done. ${#pdfs[@]} file(s) processed, $failed failed."
[[ $failed -gt 0 ]] && exit 1 || exit 0
