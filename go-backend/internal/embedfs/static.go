package embedfs

import "embed"

//go:embed web/dist
var StaticFiles embed.FS
