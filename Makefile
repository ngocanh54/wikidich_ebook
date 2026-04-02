VENV      := .venv
PYTHON    := $(VENV)/bin/python3
UV        := uv
APP_NAME  := Wikidich Ebook Creator
APP_DEST  := /Applications/$(APP_NAME).app

VERSION   := $(shell $(PYTHON) -c "import wikidich_ebook; print(wikidich_ebook.__version__)" 2>/dev/null || echo "0.0.0")
DMG       := dist/WikidichEbookCreator-$(VERSION).dmg

.PHONY: setup install-deps playwright run build install release clean help

## ── Environment ────────────────────────────────────────────────────────────

setup: ## Create .venv, install all deps, and download Playwright Chromium
	$(UV) venv $(VENV)
	$(UV) pip install -r requirements-build.txt
	$(VENV)/bin/playwright install chromium

## ── Development ─────────────────────────────────────────────────────────────

run: ## Launch the GUI
	$(PYTHON) gui.py

## ── Build & Release ─────────────────────────────────────────────────────────

build: ## Build the macOS .app and .dmg
	./build_mac_app.sh

install: ## Copy built app to /Applications (removes old version first)
	@if [ ! -d "dist/$(APP_NAME).app" ]; then \
		echo "❌ App not found. Run 'make build' first."; exit 1; \
	fi
	rm -rf "$(APP_DEST)"
	cp -R "dist/$(APP_NAME).app" "$(APP_DEST)"
	@echo "✓ Installed $(VERSION) to $(APP_DEST)"

release: build install ## Build, install, push, and upload DMG to GitHub release
	git add -A
	git diff --cached --quiet || git commit -m "Release v$(VERSION)"
	git push
	gh release upload v$(VERSION) "$(DMG)" --clobber
	@echo "✓ Released v$(VERSION)"

## ── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove build artefacts (uses sudo if root-owned)
	@if [ -d "build" ] && [ ! -w "build" ]; then \
		sudo rm -rf build dist; \
	else \
		rm -rf build dist; \
	fi
	@echo "✓ Cleaned build artefacts"

## ── Help ─────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
