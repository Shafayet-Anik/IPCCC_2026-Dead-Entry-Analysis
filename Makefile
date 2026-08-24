# Makefile used for iiswc26example 2026/08/04 version V1.0

PAPER = 00.iiswc_main
TEX = $(wildcard *.tex)
BIB = reference.bib
FIGS = $(wildcard figs/*.png)

.PHONY: all clean

all: $(PAPER).pdf

$(PAPER).pdf: $(TEX) $(BIB) $(FIGS)
	pdflatex $(PAPER)
	bibtex $(PAPER)
	pdflatex $(PAPER)
	pdflatex $(PAPER)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out $(PAPER).pdf
