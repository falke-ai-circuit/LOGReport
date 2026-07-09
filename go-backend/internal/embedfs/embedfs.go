// Package embedfs holds all embedded static assets.
package embedfs

import _ "embed"

//go:embed resources/BsTool.exe
var BsTool []byte

// StaticFS is imported separately via embed.FS in the main package
