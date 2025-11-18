# Makefile for Gee Stott Final Presentation
# Requires: marp-cli (https://github.com/marp-team/marp-cli)

# Variables
PRESENTATION = presentation.md
OUTPUT_PDF = gee_stott_final_presentation.pdf
OUTPUT_HTML = gee_stott_final_presentation.html
OUTPUT_PPTX = gee_stott_final_presentation.pptx

# Default target - build PDF
.PHONY: all
all: pdf

# Build PDF version
.PHONY: pdf
pdf: $(OUTPUT_PDF)

$(OUTPUT_PDF): $(PRESENTATION)
	@echo "Building PDF presentation..."
	marp $(PRESENTATION) --pdf --allow-local-files -o $(OUTPUT_PDF)
	@echo "PDF built successfully: $(OUTPUT_PDF)"

# Build HTML version
.PHONY: html
html: $(OUTPUT_HTML)

$(OUTPUT_HTML): $(PRESENTATION)
	@echo "Building HTML presentation..."
	marp $(PRESENTATION) --html --allow-local-files -o $(OUTPUT_HTML)
	@echo "HTML built successfully: $(OUTPUT_HTML)"

# Build PowerPoint version
.PHONY: pptx
pptx: $(OUTPUT_PPTX)

$(OUTPUT_PPTX): $(PRESENTATION)
	@echo "Building PowerPoint presentation..."
	marp $(PRESENTATION) --pptx --allow-local-files -o $(OUTPUT_PPTX)
	@echo "PowerPoint built successfully: $(OUTPUT_PPTX)"

# Build all formats
.PHONY: all-formats
all-formats: pdf html pptx
	@echo "All presentation formats built successfully!"

# Watch mode - automatically rebuild PDF on changes
.PHONY: watch
watch:
	@echo "Watching for changes (PDF output)..."
	marp -w $(PRESENTATION) --pdf --allow-local-files -o $(OUTPUT_PDF)

# Watch with server - preview in browser
.PHONY: serve
serve:
	@echo "Starting Marp server at http://localhost:8080"
	marp -s $(PRESENTATION) --allow-local-files

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	rm -f $(OUTPUT_PDF) $(OUTPUT_HTML) $(OUTPUT_PPTX)
	@echo "Clean complete."

# View the PDF (requires a PDF viewer)
.PHONY: view
view: pdf
	@if command -v xdg-open > /dev/null 2>&1; then \
		xdg-open $(OUTPUT_PDF); \
	elif command -v open > /dev/null 2>&1; then \
		open $(OUTPUT_PDF); \
	elif command -v evince > /dev/null 2>&1; then \
		evince $(OUTPUT_PDF) & \
	elif command -v okular > /dev/null 2>&1; then \
		okular $(OUTPUT_PDF) & \
	else \
		echo "No PDF viewer found. Please open $(OUTPUT_PDF) manually."; \
	fi

# Check if marp is installed
.PHONY: check
check:
	@echo "Checking for required tools..."
	@command -v marp >/dev/null 2>&1 || { echo "Error: marp is not installed. Run: npm install -g @marp-team/marp-cli"; exit 1; }
	@echo "marp version: $$(marp --version)"
	@echo "All required tools are installed."

# Slide count
.PHONY: count
count:
	@echo "Slide count:"
	@grep -c "^---$$" $(PRESENTATION)

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all (default)  - Build PDF presentation"
	@echo "  pdf            - Build PDF format"
	@echo "  html           - Build HTML format"
	@echo "  pptx           - Build PowerPoint format"
	@echo "  all-formats    - Build all formats (PDF, HTML, PPTX)"
	@echo "  watch          - Watch for changes and rebuild PDF"
	@echo "  serve          - Start preview server (http://localhost:8080)"
	@echo "  view           - Build and open PDF in viewer"
	@echo "  clean          - Remove all generated files"
	@echo "  check          - Verify marp-cli is installed"
	@echo "  count          - Show number of slides"
	@echo "  help           - Show this help message"
	@echo ""
	@echo "Installation:"
	@echo "  npm install -g @marp-team/marp-cli"
