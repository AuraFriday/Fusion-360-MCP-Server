# Makefile for AuraFriday MCP Server Fusion 360 Add-in
# Author: Christopher Nathan Drake
# Project: MCP-Link Fusion 360 Add-in

# Read version from ver.txt (strip whitespace)
VERSION := $(shell cat ver.txt | tr -d '\n\r ')

# Output zip filename
ZIP_NAME := MCP-Link-Fusion-$(VERSION).zip

# Directories to exclude from the zip (as find patterns)
EXCLUDE_PATTERNS := -path "./.git/*" -o -path "./.github/*" -o -path "./.vscode/*" -o -path "./.specstory/*" \
	-o -path "./old/*" -o -path "./python_mcp/*" -o -path "./fusion_ai/*" -o -path "./docs-mine/*" -o -path "./todo.txt" -o -path "./__pycache__/*"  \
	-o -path "./Fusion-360-MCP-Server/*" -o -path "./ragtag/*"

.PHONY: all clean help package list-files

# Default target
all: package

# Create the distribution zip file
package:
	@echo "=================================================="
	@echo "Building MCP-Link Fusion 360 Add-in Package"
	@echo "Version: $(VERSION)"
	@echo "Output: $(ZIP_NAME)"
	@echo "=================================================="
	@echo ""
	@echo "Collecting files..."
	@rm -f $(ZIP_NAME)
	@FILES=$$(find . -type f \
		-not \( $(EXCLUDE_PATTERNS) \) \
		-not -path "./.git" \
		-not -path "./.github" \
		-not -path "./.vscode" \
		-not -path "./.specstory" \
		-not -path "./.*" \
		-not -name ".*" \
		-not -name "Makefile" \
		-not -name "*.zip" \
		-not -name "$(ZIP_NAME)"); \
	FILE_COUNT=$$(echo "$$FILES" | wc -l); \
	echo "Found $$FILE_COUNT files to package"; \
	echo ""; \
	echo "Creating zip archive..."; \
	echo ""; \
	echo "$$FILES" | zip -@ $(ZIP_NAME); \
	echo ""; \
	ZIP_SIZE=$$(du -h $(ZIP_NAME) | cut -f1); \
	echo "=================================================="; \
	echo "✅ Package created successfully!"; \
	echo "📦 File: $(ZIP_NAME)"; \
	echo "📊 Size: $$ZIP_SIZE"; \
	echo "==================================================";

# List files that will be included in the package (dry run)
list-files:
	@echo "Files that will be included in $(ZIP_NAME):"
	@echo "=================================================="
	@find . -type f \
		-not \( $(EXCLUDE_PATTERNS) \) \
		-not -path "./.git" \
		-not -path "./.github" \
		-not -path "./.vscode" \
		-not -path "./.specstory" \
		-not -path "./.*" \
		-not -name ".*" \
		-not -name "Makefile" \
		-not -name "*.zip" \
		| sed 's|^\./||' | sort
	@echo ""
	@echo "Total: $$(find . -type f \
		-not \( $(EXCLUDE_PATTERNS) \) \
		-not -path "./.git" \
		-not -path "./.github" \
		-not -path "./.vscode" \
		-not -path "./.specstory" \
		-not -path "./.*" \
		-not -name ".*" \
		-not -name "Makefile" \
		-not -name "*.zip" | wc -l) files"

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	@rm -f MCP-Link-Fusion-*.zip
	@echo "✅ Clean complete"

# Show help
help:
	@echo "=================================================="
	@echo "MCP-Link Fusion 360 Add-in - Makefile Help"
	@echo "=================================================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  make              - Build the distribution package (default)"
	@echo "  make package      - Build the distribution package"
	@echo "  make list-files   - List files that will be included (dry run)"
	@echo "  make clean        - Remove generated zip files"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "Current version: $(VERSION)"
	@echo "Output file: $(ZIP_NAME)"
	@echo ""
	@echo "Excluded directories:"
	@echo "  .git .github .vscode .specstory old python_mcp fusion_ai"
	@echo "  Fusion-360-MCP-Server ragtag"
	@echo ""
	@echo "Excluded files:"
	@echo "  Hidden files (.*), Makefile, *.zip"
	@echo ""
	@echo "RELEASE:"
	@echo "cd Fusion-360-MCP-Server"
	@echo 'for FN in `find . -type f -not -path "./.*/*" -not -path "./.*" -not -path "./old/*" -not -path "./python_mcp/*"  -not -path "./fusion_ai/*"   -not -path "./Fusion-360-MCP-Server/*" `;do if cmp -s $$FN ~/Downloads/cursor/MCP-Link-fusion-new/$$FN; then echo -e "$${GRN}SAME$${NORM}  $$FN"; else echo /bin/cp -a ~/Downloads/cursor/MCP-Link-fusion-new/$$FN $$FN; fi;   done'
	@echo "=================================================="

