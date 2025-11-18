# Makefile for Gee Stott Final Report (IEEE Format)
# Requires: typst (https://typst.app/)

# Variables
MAIN = main.typ
OUTPUT = gee_stott_final_report.pdf
SECTIONS = $(wildcard sections/*.typ)

# Default target
.PHONY: all
all: $(OUTPUT)

# Build the PDF
$(OUTPUT): $(MAIN) $(SECTIONS)
	@echo "Building IEEE format report..."
	typst compile $(MAIN) $(OUTPUT)
	@echo "Report built successfully: $(OUTPUT)"

# Watch mode - automatically rebuild on changes
.PHONY: watch
watch:
	@echo "Watching for changes..."
	typst watch $(MAIN) $(OUTPUT)

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	rm -f $(OUTPUT)
	@echo "Clean complete."

# View the PDF (requires a PDF viewer)
.PHONY: view
view: $(OUTPUT)
	@if command -v xdg-open > /dev/null 2>&1; then \
		xdg-open $(OUTPUT); \
	elif command -v open > /dev/null 2>&1; then \
		open $(OUTPUT); \
	elif command -v evince > /dev/null 2>&1; then \
		evince $(OUTPUT) & \
	elif command -v okular > /dev/null 2>&1; then \
		okular $(OUTPUT) & \
	else \
		echo "No PDF viewer found. Please open $(OUTPUT) manually."; \
	fi

# Check if typst is installed
.PHONY: check
check:
	@echo "Checking for required tools..."
	@command -v typst >/dev/null 2>&1 || { echo "Error: typst is not installed. Visit https://typst.app/"; exit 1; }
	@echo "typst version: $$(typst --version)"
	@echo "All required tools are installed."

# Show word count approximation
.PHONY: wordcount
wordcount:
	@echo "Approximate word count:"
	@cat $(MAIN) $(SECTIONS) | sed 's/\/\/.*//' | sed 's/#[a-zA-Z].*//g' | wc -w

# Lint/format check (placeholder for future linting tools)
.PHONY: lint
lint:
	@echo "Linting Typst files..."
	@echo "Note: No linting tool configured yet."

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all (default)  - Build the PDF report"
	@echo "  watch          - Watch for changes and rebuild automatically"
	@echo "  clean          - Remove generated PDF"
	@echo "  view           - Build and open the PDF in a viewer"
	@echo "  check          - Verify required tools are installed"
	@echo "  wordcount      - Show approximate word count"
	@echo "  lint           - Check formatting (not yet implemented)"
	@echo "  help           - Show this help message"
