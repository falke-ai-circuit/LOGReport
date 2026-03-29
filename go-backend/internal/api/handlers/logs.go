package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sync"

	"github.com/go-chi/chi/v5"
	"github.com/goranjovic55/LOGReport/internal/generator"
	"github.com/goranjovic55/LOGReport/internal/processor"
)

type ScanRequest struct {
	RootPath    string `json:"root_path"`
	ReadContent bool   `json:"read_content"`
	LineLimit   int    `json:"line_limit"`
	LinesMode   string `json:"lines_mode"`
}

type GenerateRequest struct {
	ScanID    string `json:"scan_id"`
	Title     string `json:"title"`
	MaxLines  int    `json:"max_lines"`
}

type scanEntry struct {
	result *processor.ScanResult
	pdfPath string
}

var (
	scansMu sync.RWMutex
	scans   = map[string]*scanEntry{}
	scanSeq int
)

func nextScanID() string {
	scanSeq++
	return fmt.Sprintf("scan_%d", scanSeq)
}

func ScanLogs(w http.ResponseWriter, r *http.Request) {
	var req ScanRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}
	if req.RootPath == "" {
		writeError(w, http.StatusBadRequest, "root_path required")
		return
	}

	opts := processor.ScanOptions{
		ReadContent: req.ReadContent,
		LineLimit:   req.LineLimit,
		LinesMode:   req.LinesMode,
	}
	result, err := processor.Scan(req.RootPath, opts)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	scansMu.Lock()
	id := nextScanID()
	scans[id] = &scanEntry{result: result}
	scansMu.Unlock()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"scan_id": id,
		"total":   result.Total,
		"groups":  result.Groups,
	})
}

func GenerateReport(w http.ResponseWriter, r *http.Request) {
	var req GenerateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}

	scansMu.RLock()
	entry, ok := scans[req.ScanID]
	scansMu.RUnlock()
	if !ok {
		writeError(w, http.StatusNotFound, "scan not found — run /api/logs/scan first")
		return
	}

	// Re-scan with content for PDF generation if lines are empty
	result := entry.result
	if result.Total > 0 && len(result.Groups) > 0 && len(result.Groups[0].Files) > 0 && result.Groups[0].Files[0].Lines == nil {
		r2, err := processor.Scan(result.RootPath, processor.ScanOptions{ReadContent: true, LinesMode: "first"})
		if err == nil {
			result = r2
		}
	}

	tmpFile := filepath.Join(os.TempDir(), req.ScanID+"_report.pdf")
	if err := generator.GeneratePDF(result, tmpFile, generator.ReportOptions{
		Title:    req.Title,
		MaxLines: req.MaxLines,
	}); err != nil {
		writeError(w, http.StatusInternalServerError, "PDF generation failed: "+err.Error())
		return
	}

	scansMu.Lock()
	scans[req.ScanID].pdfPath = tmpFile
	scansMu.Unlock()

	writeJSON(w, http.StatusOK, map[string]string{
		"scan_id":  req.ScanID,
		"pdf_path": tmpFile,
		"download": "/api/reports/" + req.ScanID + "/download",
	})
}

// GetScanResult returns the cached scan result for use by other handlers
func GetScanResult(scanID string) (*processor.ScanResult, bool) {
	scansMu.RLock()
	defer scansMu.RUnlock()
	entry, ok := scans[scanID]
	if !ok {
		return nil, false
	}
	return entry.result, true
}

func DownloadReport(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")

	scansMu.RLock()
	entry, ok := scans[id]
	scansMu.RUnlock()
	if !ok || entry.pdfPath == "" {
		writeError(w, http.StatusNotFound, "report not found")
		return
	}

	data, err := os.ReadFile(entry.pdfPath)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "cannot read PDF")
		return
	}

	w.Header().Set("Content-Type", "application/pdf")
	w.Header().Set("Content-Disposition", `attachment; filename="logreport.pdf"`)
	w.Write(data)
}
