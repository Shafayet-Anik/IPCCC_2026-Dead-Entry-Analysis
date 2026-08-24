#!/bin/bash
# Compile the IISWC Dead-Entry paper LaTeX to PDF.
# Usage: ./run.sh [--clean]

set -e
cd "$(dirname "$0")"

MAIN=00.iiswc_main

if [ "${1:-}" = "--clean" ]; then
    rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot "${MAIN}.pdf"
    echo "Cleaned."
    exit 0
fi

# Fix CRLF line endings if present
if command -v dos2unix &> /dev/null; then
    dos2unix -q *.tex *.cls *.sty *.bib 2>/dev/null || true
else
    for f in *.tex *.cls *.sty *.bib; do
        [ -f "$f" ] && sed -i '' $'s/\r$//' "$f" 2>/dev/null || true
    done
fi

pdflatex -interaction=nonstopmode "$MAIN" | tail -5
if grep -q '\\bibdata' "${MAIN}.aux" 2>/dev/null; then
    bibtex "$MAIN" 2>&1 | tail -3
fi
pdflatex -interaction=nonstopmode "$MAIN" > /dev/null
pdflatex -interaction=nonstopmode "$MAIN" > /dev/null

echo "Done: ${MAIN}.pdf"
