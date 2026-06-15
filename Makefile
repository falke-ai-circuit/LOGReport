.PHONY: build test release clean web-build go-build run dev test-integration vet

GOCMD=/opt/data/go/bin/go
GOBUILD=$(GOCMD) build
GOVET=$(GOCMD) vet
GOTEST=$(GOCMD) test

# Default port
PORT ?= 8080

# Single command: build everything into one binary
build: web-build go-build

# Build React frontend → web/dist/ (gitignored — AXON pattern)
web-build:
	cd web && npm ci && npm run build

# Build Go binary with embedded web/dist/
go-build:
	$(GOBUILD) -o ./cmd/logreport/logreport ./cmd/logreport/

# Run with embedded web UI
run: build
	./cmd/logreport/logreport --port $(PORT)

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

# Release build (goreleaser or manual)
release: build
	goreleaser release --clean

# Clean
clean:
	rm -f ./cmd/logreport/logreport
	rm -rf web/dist/
	rm -rf build/
