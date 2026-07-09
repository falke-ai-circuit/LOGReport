// Package assets provides embedded static assets for the LOGReport web UI.
// The //go:embed directive must be in a package at the repo root to reach web/dist-new-flat/.
package assets

import "embed"

// FS contains the embedded web/dist-new-flat/ directory (production React build).
//
//go:embed all:web/dist-new-flat
var FS embed.FS
