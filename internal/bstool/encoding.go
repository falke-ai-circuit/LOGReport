package bstool

import (
	"bytes"
	"io"

	"golang.org/x/text/encoding/charmap"
	"golang.org/x/text/transform"
)

// decodeWindows1252 converts a Windows-1252/CP1252 byte slice to a UTF-8 string.
// Uses golang.org/x/text/encoding/charmap.Windows1252 for proper conversion.
// Falls back to UTF-8 with replacement characters if decode fails.
//
// Evidence: valmet report §3.1, bstool_command_service.py line 465.
func decodeWindows1252(raw []byte) (string, error) {
	if len(raw) == 0 {
		return "", nil
	}

	decoder := charmap.Windows1252.NewDecoder()
	reader := transform.NewReader(bytes.NewReader(raw), decoder)
	decoded, err := io.ReadAll(reader)
	if err != nil {
		// Fall back: treat as UTF-8 with replacement chars
		return string(bytes.ToValidUTF8(raw, []byte("\uFFFD"))), err
	}
	return string(decoded), nil
}
