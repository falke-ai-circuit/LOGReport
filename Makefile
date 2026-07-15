.PHONY: build test release clean web-build go-build run dev test-integration vet release-x86 release-x64 release-all fix-pe

GOCMD=/opt/data/go/bin/go
GOBUILD=$(GOCMD) build
GOVET=$(GOCMD) vet
GOTEST=$(GOCMD) test

# Default port — matches config.go default
PORT ?= 8642

# Version (override with: make build VERSION=v1.2.0)
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)

# LDFLAGS: inject version string at link time
LDFLAGS = -X main.version=$(VERSION)

# Single command: build frontend + backend into one self-contained binary
build: web-build go-build

# Build React frontend → web/dist-new-flat/ (gitignored)
web-build:
	cd web && npm ci && npm run build

# Build Go binary with embedded web/dist-new-flat/ and version stamp
go-build:
	$(GOBUILD) -ldflags "$(LDFLAGS)" -o logreport ./cmd/logreport/

# Run with embedded web UI (override port: make run PORT=9000)
run: build
	./logreport --port $(PORT)

# Development mode: separate frontend dev server + Go API
dev:
	cd web && npm run dev & \
	go run ./cmd/logreport/ --port $(PORT) --cors-origin=http://localhost:5173

# Tests
test:
	$(GOTEST) ./internal/... -v -count=1

test-integration:
	$(GOTEST) ./test/integration/... -v -count=1

# Vet
vet:
	$(GOVET) ./...

# Release: clean build with version stamp (no goreleaser needed)
release: clean build

# Clean
clean:
	rm -f ./logreport
	rm -rf web/dist-new-flat/
	rm -rf build/

# Cross-compile for Windows (requires GOOS=GOARCH env vars)
# Build x86 (32-bit) for Windows Server 2003
release-x86: web-build
	GOOS=windows GOARCH=386 $(GOBUILD) -ldflags "$(LDFLAGS)" -o logreport-x86.exe ./cmd/logreport/
	python3 scripts/fix-pe-version.py logreport-x86.exe

# Build x64 (64-bit) for Windows Server 2003/2008+
release-x64: web-build
	GOOS=windows GOARCH=amd64 $(GOBUILD) -ldflags "$(LDFLAGS)" -o logreport-x64.exe ./cmd/logreport/
	python3 scripts/fix-pe-version.py logreport-x64.exe

# Build both x86 + x64
release-all: release-x86 release-x64

# Fix PE version on existing binary (without rebuilding)
fix-pe:
	python3 scripts/fix-pe-version.py logreport-x86.exe logreport-x64.exe
