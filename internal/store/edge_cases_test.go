package store

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── Edge Case Tests ─────────────────────────────────────────────

// TestEdgeCaseSaveIOPointsNonExistentNode verifies that saving IO points
// for a node that doesn't exist triggers a FK constraint violation.
func TestEdgeCaseSaveIOPointsNonExistentNode(t *testing.T) {
	s := openTestStore(t)

	// Do NOT create the node — attempt to save IO points for a non-existent address.
	points := []types.IOPoint{
		{NodeAddress: "nonexistent.address", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	}

	err := s.SaveIOPoints("nonexistent.address", points)
	if err == nil {
		t.Fatal("SaveIOPoints for non-existent node: expected FK constraint error, got nil")
	}
	t.Logf("Got expected FK error: %v", err)
}

// TestEdgeCaseOpenBadPath verifies that Open returns an error when the
// path is in a directory that doesn't exist (unwritable).
func TestEdgeCaseOpenBadPath(t *testing.T) {
	// Use a path inside a non-existent directory — SQLite cannot create
	// the parent directory, so this should fail.
	badPath := filepath.Join("/nonexistent-dir-xyz", "test.db")

	_, err := Open(badPath)
	if err == nil {
		t.Fatal("Open with bad path: expected error, got nil")
	}
	t.Logf("Got expected error for bad path: %v", err)
}

// TestEdgeCaseOpenReadOnlyDir verifies that Open returns an error when
// the target directory is read-only (cannot create the database file).
func TestEdgeCaseOpenReadOnlyDir(t *testing.T) {
	// Create a read-only directory
	roDir, err := os.MkdirTemp("", "logreport-readonly-*")
	if err != nil {
		t.Fatalf("MkdirTemp: %v", err)
	}
	t.Cleanup(func() {
		os.Chmod(roDir, 0755) // restore perms so cleanup can delete
		os.RemoveAll(roDir)
	})

	if err := os.Chmod(roDir, 0555); err != nil {
		t.Fatalf("Chmod read-only: %v", err)
	}

	dbPath := filepath.Join(roDir, "test.db")
	_, err = Open(dbPath)
	if err == nil {
		t.Fatal("Open in read-only dir: expected error, got nil")
	}
	t.Logf("Got expected error for read-only dir: %v", err)
}

// TestEdgeCaseSaveDeleteSaveCycle verifies that a SaveNode → DeleteNode →
// SaveNode cycle with the same address works correctly (INSERT OR REPLACE).
func TestEdgeCaseSaveDeleteSaveCycle(t *testing.T) {
	s := openTestStore(t)

	addr := "192.168.99.1"

	// Step 1: Save node
	n1 := &types.Node{
		Address: addr,
		Name:    "FirstVersion",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n1); err != nil {
		t.Fatalf("SaveNode 1: %v", err)
	}

	got1, err := s.GetNode(addr)
	if err != nil {
		t.Fatalf("GetNode 1: %v", err)
	}
	if got1.Name != "FirstVersion" {
		t.Errorf("Name after first save: got %q, want FirstVersion", got1.Name)
	}

	// Step 2: Delete node
	if err := s.DeleteNode(addr); err != nil {
		t.Fatalf("DeleteNode: %v", err)
	}

	_, err = s.GetNode(addr)
	if err == nil {
		t.Fatal("GetNode after delete: expected error, got nil")
	}

	// Step 3: Save node again with same address — should succeed (INSERT OR REPLACE)
	n2 := &types.Node{
		Address: addr,
		Name:    "SecondVersion",
		Type:    types.DIA,
		Status:  types.StatusConnected,
		Port:    8080,
	}
	if err := s.SaveNode(n2); err != nil {
		t.Fatalf("SaveNode 2 (re-save after delete): %v", err)
	}

	got2, err := s.GetNode(addr)
	if err != nil {
		t.Fatalf("GetNode 2: %v", err)
	}
	if got2.Name != "SecondVersion" {
		t.Errorf("Name after re-save: got %q, want SecondVersion", got2.Name)
	}
	if got2.Type != types.DIA {
		t.Errorf("Type after re-save: got %q, want DIA", got2.Type)
	}
	if got2.Port != 8080 {
		t.Errorf("Port after re-save: got %d, want 8080", got2.Port)
	}

	// Verify only one node with this address exists
	nodes, err := s.ListNodes()
	if err != nil {
		t.Fatalf("ListNodes: %v", err)
	}
	count := 0
	for _, n := range nodes {
		if n.Address == addr {
			count++
		}
	}
	if count != 1 {
		t.Errorf("Expected 1 node with addr %s, got %d", addr, count)
	}
}

// TestEdgeCaseGetIOPointsNonExistentNode verifies that GetIOPoints on a
// non-existent node returns an empty slice, not an error.
func TestEdgeCaseGetIOPointsNonExistentNode(t *testing.T) {
	s := openTestStore(t)

	// Query IO points for a node that was never created.
	points, err := s.GetIOPoints("nonexistent.address.999")
	if err != nil {
		t.Fatalf("GetIOPoints on non-existent node: expected no error, got: %v", err)
	}
	if points == nil {
		t.Fatal("GetIOPoints returned nil, want empty slice")
	}
	if len(points) != 0 {
		t.Errorf("GetIOPoints on non-existent node: got %d points, want 0", len(points))
	}
}

// TestEdgeCaseCloseTwice verifies that calling Close() twice on a Store
// does not panic. The second call should return an error (or nil) but
// must not crash the process.
func TestEdgeCaseCloseTwice(t *testing.T) {
	// Create a store without using openTestStore (which auto-closes on cleanup)
	path := "/tmp/logreport-edge-close-test.db"
	s, err := Open(path)
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	t.Cleanup(func() {
		os.Remove(path)
	})

	// First close — should succeed
	if err := s.Close(); err != nil {
		t.Errorf("First Close: %v", err)
	}

	// Second close — should NOT panic.
	// It may return an error (sql.DB.Close on already-closed connection),
	// but the test passes as long as it doesn't panic.
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("Second Close panicked: %v", r)
		}
	}()
	_ = s.Close() // intentionally ignore error — some drivers return error, some return nil
}