# LOGReport Makefile
# Usage:
#   make           → build for current OS
#   make windows   → cross-compile Windows x64 .exe
#   make linux     → cross-compile Linux x64
#   make all       → build all targets
#   make dist      → full release: build React + build all binaries
#   make react     → build React only (web/dist)
#   make clean     → remove build artifacts

APP      := LOGReporter
MODULE   := github.com/goranjovic55/LOGReport
CMD      := ./cmd/server
LDFLAGS  := -s -w
WIN_LDFLAGS := $(LDFLAGS) -H windowsgui

.PHONY: all dist windows linux darwin react clean sync-assets

## Default: build for current platform
all:
	@$(MAKE) sync-assets
	go build -ldflags="$(LDFLAGS)" -o $(APP) $(CMD)
	@echo "Built: $(APP)"

## Full release build: React + all binaries
dist: react sync-assets windows linux

## Build React frontend
react:
	@echo "Building React..."
	cd ../web && npm install && npx vite build
	@echo "React built → go-backend/web/dist"

## Sync embedded assets from build output
sync-assets:
	@echo "Syncing embedded assets..."
	@cp -r web/dist internal/embedfs/web/dist 2>/dev/null || true
	@echo "Assets synced."

## Windows x64 (primary target)
windows: sync-assets
	GOOS=windows GOARCH=amd64 go build \
		-ldflags="$(WIN_LDFLAGS)" \
		-o dist/$(APP).exe $(CMD)
	@echo "Built: dist/$(APP).exe"
	@ls -lh dist/$(APP).exe

## Linux x64
linux: sync-assets
	GOOS=linux GOARCH=amd64 go build \
		-ldflags="$(LDFLAGS)" \
		-o dist/$(APP)-linux $(CMD)
	@echo "Built: dist/$(APP)-linux"

## macOS (ARM + Intel)
darwin: sync-assets
	GOOS=darwin GOARCH=amd64 go build \
		-ldflags="$(LDFLAGS)" \
		-o dist/$(APP)-mac-intel $(CMD)
	GOOS=darwin GOARCH=arm64 go build \
		-ldflags="$(LDFLAGS)" \
		-o dist/$(APP)-mac-arm64 $(CMD)
	@echo "Built macOS binaries"

## Replace embedded BsTool.exe with real one before building
# Usage: make embed-bstool BSTOOL_PATH=/path/to/BsTool.exe
embed-bstool:
	@if [ -z "$(BSTOOL_PATH)" ]; then echo "ERROR: set BSTOOL_PATH=/path/to/BsTool.exe"; exit 1; fi
	cp $(BSTOOL_PATH) internal/embedfs/resources/BsTool.exe
	cp $(BSTOOL_PATH) cmd/server/resources/BsTool.exe
	@echo "BsTool.exe embedded from $(BSTOOL_PATH)"

clean:
	rm -rf dist/ $(APP) $(APP).exe
	@echo "Clean."
