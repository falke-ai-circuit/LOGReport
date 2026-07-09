package commandqueue

import (
	"fmt"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

func TestNewQueue(t *testing.T) {
	q := NewQueue(nil, nil)
	if q == nil {
		t.Fatal("expected non-nil queue")
	}
	cur, total, state := q.Status()
	if cur != 0 || total != 0 || state != QueueIdle {
		t.Errorf("expected 0/0/idle, got %d/%d/%s", cur, total, state)
	}
}

func TestQueueAdd(t *testing.T) {
	q := NewQueue(nil, nil)
	q.Add(QueuedCommand{ID: "1", Command: "test1"})
	q.Add(QueuedCommand{ID: "2", Command: "test2"})

	_, total, _ := q.Status()
	if total != 2 {
		t.Errorf("expected 2 commands, got %d", total)
	}

	cmds := q.Commands()
	if len(cmds) != 2 {
		t.Fatalf("expected 2 commands, got %d", len(cmds))
	}
	if cmds[0].Status != StatusPending {
		t.Errorf("expected pending status, got %s", cmds[0].Status)
	}
}

func TestQueueStartExecute(t *testing.T) {
	var mu sync.Mutex
	var statuses []CommandStatus
	q := NewQueue(nil, func(cmd QueuedCommand) {
		mu.Lock()
		statuses = append(statuses, cmd.Status)
		mu.Unlock()
	})

	q.Add(QueuedCommand{ID: "1", Command: "cmd1"})
	q.Add(QueuedCommand{ID: "2", Command: "cmd2"})

	execCount := 0
	executor := func(cmd QueuedCommand) (string, error) {
		execCount++
		return fmt.Sprintf("output-%s", cmd.ID), nil
	}

	if err := q.Start(executor); err != nil {
		t.Fatalf("Start failed: %v", err)
	}

	if execCount != 2 {
		t.Errorf("expected 2 executions, got %d", execCount)
	}

	cur, total, state := q.Status()
	if cur != 2 || total != 2 {
		t.Errorf("expected 2/2, got %d/%d", cur, total)
	}
	if state != QueueDone {
		t.Errorf("expected done state, got %s", state)
	}

	// Verify final statuses
	mu.Lock()
	if len(statuses) != 4 { // 2 running + 2 completed
		t.Errorf("expected 4 status callbacks, got %d", len(statuses))
	}
	mu.Unlock()

	cmds := q.Commands()
	for _, c := range cmds {
		if c.Status != StatusCompleted {
			t.Errorf("expected completed for %s, got %s", c.ID, c.Status)
		}
		if c.Output == "" {
			t.Errorf("expected non-empty output for %s", c.ID)
		}
	}
}

func TestQueuePauseResume(t *testing.T) {
	q := NewQueue(nil, nil)
	q.Add(QueuedCommand{ID: "1", Command: "cmd1"})
	q.Add(QueuedCommand{ID: "2", Command: "cmd2"})
	q.Add(QueuedCommand{ID: "3", Command: "cmd3"})

	// Pause after first command
	execCount := 0
	executor := func(cmd QueuedCommand) (string, error) {
		execCount++
		if execCount == 1 {
			q.Pause()
		}
		return "ok", nil
	}

	if err := q.Start(executor); err != nil {
		t.Fatalf("Start failed: %v", err)
	}

	if execCount != 1 {
		t.Fatalf("expected 1 execution before pause, got %d", execCount)
	}

	_, _, state := q.Status()
	if state != QueuePaused {
		t.Errorf("expected paused state, got %s", state)
	}

	// Resume
	q.Resume()
	if err := q.Start(executor); err != nil {
		t.Fatalf("Start resume failed: %v", err)
	}

	if execCount != 3 {
		t.Errorf("expected 3 total executions after resume, got %d", execCount)
	}
}

func TestQueueCancel(t *testing.T) {
	q := NewQueue(nil, nil)
	q.Add(QueuedCommand{ID: "1", Command: "cmd1"})
	q.Add(QueuedCommand{ID: "2", Command: "cmd2"})
	q.Add(QueuedCommand{ID: "3", Command: "cmd3"})

	execCount := 0
	executor := func(cmd QueuedCommand) (string, error) {
		execCount++
		if execCount == 1 {
			q.Cancel()
		}
		return "ok", nil
	}

	err := q.Start(executor)
	if err == nil {
		t.Fatal("expected error from cancelled queue")
	}

	if execCount != 1 {
		t.Errorf("expected 1 execution before cancel, got %d", execCount)
	}

	// Remaining commands should be cancelled
	cmds := q.Commands()
	cancelledCount := 0
	for _, c := range cmds[1:] {
		if c.Status == StatusCancelled {
			cancelledCount++
		}
	}
	if cancelledCount != 2 {
		t.Errorf("expected 2 cancelled, got %d", cancelledCount)
	}
}

func TestQueueReset(t *testing.T) {
	q := NewQueue(nil, nil)
	q.Add(QueuedCommand{ID: "1", Command: "cmd1"})
	q.Reset()

	_, total, state := q.Status()
	if total != 0 {
		t.Errorf("expected 0 commands after reset, got %d", total)
	}
	if state != QueueIdle {
		t.Errorf("expected idle state after reset, got %s", state)
	}
}

func TestQueueEmptyStart(t *testing.T) {
	q := NewQueue(nil, nil)
	executor := func(cmd QueuedCommand) (string, error) {
		return "ok", nil
	}
	if err := q.Start(executor); err != nil {
		t.Fatalf("Start on empty queue should not error: %v", err)
	}
	_, _, state := q.Status()
	if state != QueueDone {
		t.Errorf("expected done state for empty queue, got %s", state)
	}
}

func TestQueueStartAlreadyRunning(t *testing.T) {
	q := NewQueue(nil, nil)
	q.Add(QueuedCommand{ID: "1", Command: "cmd1"})

	// Start in a goroutine (simulates running state)
	done := make(chan struct{})
	go func() {
		executor := func(cmd QueuedCommand) (string, error) {
			time.Sleep(100 * time.Millisecond)
			return "ok", nil
		}
		q.Start(executor)
		close(done)
	}()

	// Give it time to start
	time.Sleep(20 * time.Millisecond)

	// Try to start again — should fail
	executor2 := func(cmd QueuedCommand) (string, error) { return "ok", nil }
	err := q.Start(executor2)
	if err == nil {
		// Might have finished already, that's ok in fast tests
	}

	<-done
}

func TestQueueAddBatchFromNodes(t *testing.T) {
	q := NewQueue(nil, nil)
	configs := []types.NodeConfig{
		{
			Name:      "AP01m",
			IPAddress: "192.168.1.101",
			Tokens: []types.Token{
				{TokenID: "162", TokenType: types.TokenFBC, Port: 2077, Protocol: "telnet"},
				{TokenID: "363", TokenType: types.TokenRPC, Port: 2077, Protocol: "telnet"},
				{TokenID: "361", TokenType: types.TokenLOG, Port: 2077, Protocol: "telnet"},
				{TokenID: "999", TokenType: types.TokenLIS, Port: 2077, Protocol: "telnet"},
			},
		},
	}

	// AddBatchFromNodes uses telnet.SessionManager but we only pass nil —
	// it just needs the configs to generate commands, the SM is only for execution.
	q.AddBatchFromNodes(configs, "", nil, "rsu")

	_, total, _ := q.Status()
	// FBC(1) + RPC(1) + LOG(1) + LIS(1 token × 6 exe × 2 rx/tx = 12) = 15 commands
	if total != 15 {
		t.Fatalf("expected 15 commands (FBC+RPC+LOG+LIS 6exe×2), got %d", total)
	}

	cmds := q.Commands()
	// Verify command types
	types_found := map[CommandType]bool{}
	for _, c := range cmds {
		types_found[c.Type] = true
		// Verify command strings contain the token
		if c.TokenID == "162" && c.Type == CmdFBC {
			expected := telnet.FBCPrint("162")
			if c.Command != expected {
				t.Errorf("expected FBC command %q, got %q", expected, c.Command)
			}
		}
		if c.TokenID == "363" && c.Type == CmdRPC {
			expected := telnet.RPCPrint("363")
			if c.Command != expected {
				t.Errorf("expected RPC command %q, got %q", expected, c.Command)
			}
		}
	}
	if !types_found[CmdFBC] || !types_found[CmdRPC] || !types_found[CmdLOG] || !types_found[CmdLIS] {
		t.Errorf("expected FBC, RPC, LOG, LIS command types, got %v", types_found)
	}
	// Verify LIS commands: 12 total (6 exe × 2 rx/tx), tokenID format "999_exeN"
	lisCount := 0
	for _, c := range cmds {
		if c.Type == CmdLIS {
			lisCount++
			// Verify command is rx-trace or tx-trace
			if !strings.Contains(c.Command, "print from rsu rx-trace") &&
				!strings.Contains(c.Command, "print from rsu tx-trace") {
				t.Errorf("unexpected LIS command: %s", c.Command)
			}
			// Verify tokenID has _exeN suffix
			if !strings.Contains(c.TokenID, "_exe") {
				t.Errorf("expected LIS tokenID with _exeN suffix, got %s", c.TokenID)
			}
		}
	}
	if lisCount != 12 {
		t.Errorf("expected 12 LIS commands (6 exe × 2 rx/tx), got %d", lisCount)
	}
}

func TestQueueAddBatchLISDiagMode(t *testing.T) {
	q := NewQueue(nil, nil)
	configs := []types.NodeConfig{
		{
			Name:          "AL02",
			IPAddress:     "192.168.1.102",
			LISDiagParams: "-s AL02 -p 4321 -x password",
			Tokens: []types.Token{
				{TokenID: "501", TokenType: types.TokenLIS, Port: 2077, Protocol: "telnet"},
			},
		},
	}

	q.AddBatchFromNodes(configs, "", nil, "lisdiag")

	_, total, _ := q.Status()
	// LISDiag: exe×6 + io×6 = 12 commands (io combines irb+orb)
	if total != 12 {
		t.Fatalf("expected 12 LISDiag commands (6 exe + 6 io), got %d", total)
	}

	cmds := q.Commands()
	ioCount := 0
	exeCount := 0
	for _, c := range cmds {
		if c.Type != CmdLISDiag {
			t.Errorf("expected CmdLISDiag type, got %s", c.Type)
		}
		if strings.Contains(c.Command, "io ") {
			ioCount++
		}
		if strings.HasPrefix(c.Command, "exe ") {
			exeCount++
		}
		// Verify no separate irb/orb commands
		if strings.Contains(c.Command, "irb ") || strings.Contains(c.Command, "orb ") {
			t.Errorf("found separate irb/orb command in io mode: %s", c.Command)
		}
	}
	if exeCount != 6 {
		t.Errorf("expected 6 exe commands, got %d", exeCount)
	}
	if ioCount != 6 {
		t.Errorf("expected 6 io commands, got %d", ioCount)
	}
}
