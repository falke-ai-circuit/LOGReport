package store

import (
	"fmt"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// openTestStore creates a temporary JSON store for testing.
func openTestStore(t *testing.T) *Store {
	t.Helper()
	path := fmt.Sprintf("/tmp/logreport-test-%d", time.Now().UnixNano())
	s, err := Open(path)
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	t.Cleanup(func() {
		s.Close()
		os.RemoveAll(path)
	})
	return s
}

// TestOpenAndMigrate verifies that Open creates the store and Migrate works.
func TestOpenMigrate(t *testing.T) {
	s := openTestStore(t)

	// Verify the store is functional by saving and retrieving a node
	n := &types.Node{
		Address: "10.0.0.1",
		Name:    "TestNode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	got, err := s.GetNode("10.0.0.1")
	if err != nil {
		t.Fatalf("GetNode: %v", err)
	}
	if got.Name != "TestNode" {
		t.Errorf("Name: got %q, want TestNode", got.Name)
	}

	// Migrate should be a no-op and idempotent
	if err := s.Migrate(); err != nil {
		t.Fatalf("Migrate: %v", err)
	}
}

// TestSaveGetNodeRoundTrip tests SaveNode → GetNode round-trip.
func TestSaveGetNodeRoundTrip(t *testing.T) {
	s := openTestStore(t)

	now := time.Now().Truncate(time.Second)
	n := &types.Node{
		Address:  "192.168.1.100",
		Name:     "ACN-01",
		Type:     types.ACN,
		Status:   types.StatusConnected,
		TokenID:  "tok-12345",
		Port:     23,
		Username: "admin",
		Password: "secret",
		LastSeen: now,
	}

	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	got, err := s.GetNode("192.168.1.100")
	if err != nil {
		t.Fatalf("GetNode: %v", err)
	}

	if got.Address != n.Address {
		t.Errorf("Address: got %q, want %q", got.Address, n.Address)
	}
	if got.Name != n.Name {
		t.Errorf("Name: got %q, want %q", got.Name, n.Name)
	}
	if got.Type != n.Type {
		t.Errorf("Type: got %q, want %q", got.Type, n.Type)
	}
	if got.Status != n.Status {
		t.Errorf("Status: got %q, want %q", got.Status, n.Status)
	}
	if got.TokenID != n.TokenID {
		t.Errorf("TokenID: got %q, want %q", got.TokenID, n.TokenID)
	}
	if got.Port != n.Port {
		t.Errorf("Port: got %d, want %d", got.Port, n.Port)
	}
	if got.Username != n.Username {
		t.Errorf("Username: got %q, want %q", got.Username, n.Username)
	}
	if got.Password != n.Password {
		t.Errorf("Password: got %q, want %q", got.Password, n.Password)
	}
	if !got.LastSeen.Equal(now) {
		t.Errorf("LastSeen: got %v, want %v", got.LastSeen, now)
	}
}

// TestListNodesEmptySlice verifies ListNodes returns empty slice (not nil) when no nodes.
func TestListNodesEmptySlice(t *testing.T) {
	s := openTestStore(t)

	nodes, err := s.ListNodes()
	if err != nil {
		t.Fatalf("ListNodes: %v", err)
	}
	if nodes == nil {
		t.Error("ListNodes returned nil, want empty slice")
	}
	if len(nodes) != 0 {
		t.Errorf("ListNodes: got %d nodes, want 0", len(nodes))
	}
}

// TestDeleteNode verifies DeleteNode removes a node and GetNode returns error.
func TestDeleteNode(t *testing.T) {
	s := openTestStore(t)

	n := &types.Node{
		Address: "10.0.0.1",
		Name:    "TestNode",
		Type:    types.DIA,
		Status:  types.StatusUnknown,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	// Verify it exists
	_, err := s.GetNode("10.0.0.1")
	if err != nil {
		t.Fatalf("GetNode before delete: %v", err)
	}

	// Delete
	if err := s.DeleteNode("10.0.0.1"); err != nil {
		t.Fatalf("DeleteNode: %v", err)
	}

	// Verify it's gone
	_, err = s.GetNode("10.0.0.1")
	if err == nil {
		t.Error("GetNode after delete: expected error, got nil")
	}
}

// TestSaveGetIOPointsBatch verifies batch insert and retrieval of IO points.
func TestSaveGetIOPointsBatch(t *testing.T) {
	s := openTestStore(t)

	// Create the node first (foreign key requirement)
	n := &types.Node{
		Address: "192.168.1.1",
		Name:    "TestNode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	points := []types.IOPoint{
		{NodeAddress: "192.168.1.1", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.1", ModulePosition: 1, ChannelPosition: 2, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.1", ModulePosition: 2, ChannelPosition: 1, ChannelType: types.DI16, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.1", ModulePosition: 3, ChannelPosition: 1, ModuleType: types.ModuleRPC, CounterName: "ERR_TX", CounterValue: 42},
		{NodeAddress: "192.168.1.1", ModulePosition: 3, ChannelPosition: 2, ModuleType: types.ModuleRPC, CounterName: "ERR_RX", CounterValue: 7},
	}

	if err := s.SaveIOPoints("192.168.1.1", points); err != nil {
		t.Fatalf("SaveIOPoints: %v", err)
	}

	got, err := s.GetIOPoints("192.168.1.1")
	if err != nil {
		t.Fatalf("GetIOPoints: %v", err)
	}

	if len(got) != len(points) {
		t.Fatalf("GetIOPoints: got %d points, want %d", len(got), len(points))
	}

	// Verify FBC points
	fbcCount := 0
	rpcCount := 0
	for _, p := range got {
		if p.ModuleType == types.ModuleFBC {
			fbcCount++
		} else if p.ModuleType == types.ModuleRPC {
			rpcCount++
		}
	}
	if fbcCount != 3 {
		t.Errorf("FBC points: got %d, want 3", fbcCount)
	}
	if rpcCount != 2 {
		t.Errorf("RPC points: got %d, want 2", rpcCount)
	}

	// Verify specific RPC counter
	found := false
	for _, p := range got {
		if p.CounterName == "ERR_TX" && p.CounterValue == 42 {
			found = true
			break
		}
	}
	if !found {
		t.Error("ERR_TX counter with value 42 not found")
	}
}

// TestSaveReportRoundTrip tests SaveReport → GetReport round-trip.
func TestSaveReportRoundTrip(t *testing.T) {
	s := openTestStore(t)

	r := &types.Report{
		ID:          "rpt-001",
		NodeAddress: "192.168.1.100",
		Format:      types.FormatDOCX,
		Template:    "standard",
		Title:       "ACN-01 Report",
		Author:      "Operator",
		Status:      types.StatusCompleted,
		FilePath:    "/tmp/reports/rpt-001.docx",
		CreatedAt:   "2026-06-15T10:00:00Z",
		CompletedAt: "2026-06-15T10:05:00Z",
	}

	if err := s.SaveReport(r); err != nil {
		t.Fatalf("SaveReport: %v", err)
	}

	got, err := s.GetReport("rpt-001")
	if err != nil {
		t.Fatalf("GetReport: %v", err)
	}

	if got.ID != r.ID {
		t.Errorf("ID: got %q, want %q", got.ID, r.ID)
	}
	if got.NodeAddress != r.NodeAddress {
		t.Errorf("NodeAddress: got %q, want %q", got.NodeAddress, r.NodeAddress)
	}
	if got.Format != r.Format {
		t.Errorf("Format: got %q, want %q", got.Format, r.Format)
	}
	if got.Template != r.Template {
		t.Errorf("Template: got %q, want %q", got.Template, r.Template)
	}
	if got.Title != r.Title {
		t.Errorf("Title: got %q, want %q", got.Title, r.Title)
	}
	if got.Author != r.Author {
		t.Errorf("Author: got %q, want %q", got.Author, r.Author)
	}
	if got.Status != r.Status {
		t.Errorf("Status: got %q, want %q", got.Status, r.Status)
	}
	if got.FilePath != r.FilePath {
		t.Errorf("FilePath: got %q, want %q", got.FilePath, r.FilePath)
	}
	if got.CreatedAt != r.CreatedAt {
		t.Errorf("CreatedAt: got %q, want %q", got.CreatedAt, r.CreatedAt)
	}
	if got.CompletedAt != r.CompletedAt {
		t.Errorf("CompletedAt: got %q, want %q", got.CompletedAt, r.CompletedAt)
	}
}

// TestConcurrentWrites verifies that concurrent goroutine writes don't corrupt data.
func TestConcurrentWrites(t *testing.T) {
	s := openTestStore(t)

	var wg sync.WaitGroup
	numGoroutines := 10
	nodesPerGoroutine := 10

	for g := 0; g < numGoroutines; g++ {
		wg.Add(1)
		go func(goroutineID int) {
			defer wg.Done()
			for i := 0; i < nodesPerGoroutine; i++ {
				addr := fmt.Sprintf("10.0.%d.%d", goroutineID, i)
				n := &types.Node{
					Address: addr,
					Name:    fmt.Sprintf("Node-%d-%d", goroutineID, i),
					Type:    types.ACN,
					Status:  types.StatusConnected,
					Port:    23,
				}
				if err := s.SaveNode(n); err != nil {
					t.Errorf("goroutine %d SaveNode %s: %v", goroutineID, addr, err)
				}
			}
		}(g)
	}

	wg.Wait()

	// Verify all nodes were saved
	nodes, err := s.ListNodes()
	if err != nil {
		t.Fatalf("ListNodes: %v", err)
	}

	expected := numGoroutines * nodesPerGoroutine
	if len(nodes) != expected {
		t.Errorf("ListNodes: got %d nodes, want %d", len(nodes), expected)
	}
}

// TestSchemaMigration verifies that Migrate is idempotent (no-op for JSON store).
func TestSchemaMigration(t *testing.T) {
	s := openTestStore(t)

	// Migrate should be a no-op and idempotent
	if err := s.Migrate(); err != nil {
		t.Fatalf("first Migrate: %v", err)
	}

	// Re-run Migrate — should be idempotent
	if err := s.Migrate(); err != nil {
		t.Fatalf("second Migrate: %v", err)
	}

	// Store should still be functional
	n := &types.Node{
		Address: "10.0.0.1",
		Name:    "MigrateTest",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode after migrate: %v", err)
	}
}

// TestLargeDataset verifies performance with 1000+ IO points.
func TestLargeDataset(t *testing.T) {
	s := openTestStore(t)

	// Create the node first (foreign key requirement)
	n := &types.Node{
		Address: "192.168.1.1",
		Name:    "LargeNode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	numPoints := 2000
	points := make([]types.IOPoint, numPoints)
	for i := 0; i < numPoints; i++ {
		points[i] = types.IOPoint{
			NodeAddress:     "192.168.1.1",
			ModulePosition:  (i / 16) + 1,
			ChannelPosition: (i % 16) + 1,
			ChannelType:     types.AI8,
			ModuleType:      types.ModuleFBC,
		}
	}

	start := time.Now()
	if err := s.SaveIOPoints("192.168.1.1", points); err != nil {
		t.Fatalf("SaveIOPoints large: %v", err)
	}
	saveDuration := time.Since(start)

	start = time.Now()
	got, err := s.GetIOPoints("192.168.1.1")
	if err != nil {
		t.Fatalf("GetIOPoints large: %v", err)
	}
	getDuration := time.Since(start)

	if len(got) != numPoints {
		t.Errorf("GetIOPoints large: got %d points, want %d", len(got), numPoints)
	}

	// Performance assertions: should be reasonably fast
	if saveDuration > 5*time.Second {
		t.Errorf("SaveIOPoints 2000 points took %v, want < 5s", saveDuration)
	}
	if getDuration > 2*time.Second {
		t.Errorf("GetIOPoints 2000 points took %v, want < 2s", getDuration)
	}

	t.Logf("Large dataset: save %v, get %v", saveDuration, getDuration)
}

// TestListReportsEmptySlice verifies ListReports returns empty slice when no reports.
func TestListReportsEmptySlice(t *testing.T) {
	s := openTestStore(t)

	reports, err := s.ListReports()
	if err != nil {
		t.Fatalf("ListReports: %v", err)
	}
	if reports == nil {
		t.Error("ListReports returned nil, want empty slice")
	}
	if len(reports) != 0 {
		t.Errorf("ListReports: got %d reports, want 0", len(reports))
	}
}

// TestDeleteReport verifies DeleteReport removes a report.
func TestDeleteReport(t *testing.T) {
	s := openTestStore(t)

	r := &types.Report{
		ID:          "rpt-del",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatJSON,
		Status:      types.StatusPending,
		CreatedAt:   "2026-06-15T10:00:00Z",
	}
	if err := s.SaveReport(r); err != nil {
		t.Fatalf("SaveReport: %v", err)
	}

	if err := s.DeleteReport("rpt-del"); err != nil {
		t.Fatalf("DeleteReport: %v", err)
	}

	_, err := s.GetReport("rpt-del")
	if err == nil {
		t.Error("GetReport after delete: expected error, got nil")
	}
}

// TestSaveNodeUpdate verifies that saving a node twice updates it (INSERT OR REPLACE).
func TestSaveNodeUpdate(t *testing.T) {
	s := openTestStore(t)

	n1 := &types.Node{
		Address: "192.168.1.200",
		Name:    "Original",
		Type:    types.ACN,
		Status:  types.StatusUnknown,
		Port:    23,
	}
	if err := s.SaveNode(n1); err != nil {
		t.Fatalf("SaveNode 1: %v", err)
	}

	n2 := &types.Node{
		Address: "192.168.1.200",
		Name:    "Updated",
		Type:    types.DIA,
		Status:  types.StatusConnected,
		Port:    8080,
	}
	if err := s.SaveNode(n2); err != nil {
		t.Fatalf("SaveNode 2: %v", err)
	}

	got, err := s.GetNode("192.168.1.200")
	if err != nil {
		t.Fatalf("GetNode: %v", err)
	}

	if got.Name != "Updated" {
		t.Errorf("Name: got %q, want Updated", got.Name)
	}
	if got.Type != types.DIA {
		t.Errorf("Type: got %q, want DIA", got.Type)
	}
	if got.Status != types.StatusConnected {
		t.Errorf("Status: got %q, want connected", got.Status)
	}
	if got.Port != 8080 {
		t.Errorf("Port: got %d, want 8080", got.Port)
	}
}

// TestSaveIOPointsReplaces verifies that saving IO points replaces old ones.
func TestSaveIOPointsReplaces(t *testing.T) {
	s := openTestStore(t)

	// Create the node first
	n := &types.Node{
		Address: "10.0.0.1",
		Name:    "ReplaceNode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	old := []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	}
	if err := s.SaveIOPoints("10.0.0.1", old); err != nil {
		t.Fatalf("SaveIOPoints old: %v", err)
	}

	newPoints := []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 2, ChannelPosition: 1, ChannelType: types.DI16, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 2, ChannelPosition: 2, ChannelType: types.DI16, ModuleType: types.ModuleFBC},
	}
	if err := s.SaveIOPoints("10.0.0.1", newPoints); err != nil {
		t.Fatalf("SaveIOPoints new: %v", err)
	}

	got, err := s.GetIOPoints("10.0.0.1")
	if err != nil {
		t.Fatalf("GetIOPoints: %v", err)
	}

	if len(got) != 2 {
		t.Fatalf("GetIOPoints: got %d points, want 2", len(got))
	}
	if got[0].ModulePosition != 2 {
		t.Errorf("first point module position: got %d, want 2", got[0].ModulePosition)
	}
}

// TestGetIOPointsEmptySlice verifies GetIOPoints returns empty slice for unknown node.
func TestGetIOPointsEmptySlice(t *testing.T) {
	s := openTestStore(t)

	points, err := s.GetIOPoints("nonexistent")
	if err != nil {
		t.Fatalf("GetIOPoints: %v", err)
	}
	if points == nil {
		t.Error("GetIOPoints returned nil, want empty slice")
	}
	if len(points) != 0 {
		t.Errorf("GetIOPoints: got %d points, want 0", len(points))
	}
}

// TestDeleteIOPoints verifies DeleteIOPoints removes all points for a node.
func TestDeleteIOPoints(t *testing.T) {
	s := openTestStore(t)

	// Create the node first
	n := &types.Node{
		Address: "10.0.0.2",
		Name:    "DeleteIONode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	points := []types.IOPoint{
		{NodeAddress: "10.0.0.2", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.2", ModulePosition: 1, ChannelPosition: 2, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	}
	if err := s.SaveIOPoints("10.0.0.2", points); err != nil {
		t.Fatalf("SaveIOPoints: %v", err)
	}

	if err := s.DeleteIOPoints("10.0.0.2"); err != nil {
		t.Fatalf("DeleteIOPoints: %v", err)
	}

	got, err := s.GetIOPoints("10.0.0.2")
	if err != nil {
		t.Fatalf("GetIOPoints after delete: %v", err)
	}
	if len(got) != 0 {
		t.Errorf("GetIOPoints after delete: got %d points, want 0", len(got))
	}
}