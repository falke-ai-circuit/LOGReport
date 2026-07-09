// Package commandqueue implements a sequential command execution queue
// with pause/resume/cancel support. It mirrors the Python command_queue.py
// and sequential_command_processor.py behavior for the Commander window.
package commandqueue

import (
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/lisdiag"
	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// CommandType identifies the type of command to execute.
type CommandType string

const (
	CmdFBC    CommandType = "fbc"
	CmdRPC    CommandType = "rpc"
	CmdLOG    CommandType = "log"
	CmdLIS    CommandType = "lis"
	CmdBsTool  CommandType = "bstool"
	CmdRaw     CommandType = "raw"
	CmdLISDiag CommandType = "lisdiag"
)

// CommandStatus represents the execution state of a queued command.
type CommandStatus string

const (
	StatusPending   CommandStatus = "pending"
	StatusRunning   CommandStatus = "running"
	StatusCompleted CommandStatus = "completed"
	StatusFailed    CommandStatus = "failed"
	StatusCancelled CommandStatus = "cancelled"
)

// QueuedCommand represents a single command in the queue.
type QueuedCommand struct {
	ID         string        `json:"id"`
	Type       CommandType   `json:"type"`
	NodeName   string        `json:"node_name"`
	TokenID    string        `json:"token_id"`
	Command    string        `json:"command"`
	Status     CommandStatus `json:"status"`
	Output     string        `json:"output,omitempty"`
	Error      string        `json:"error,omitempty"`
	IPAddress  string        `json:"ip_address,omitempty"`
	LISDiagPwd string        `json:"lisdiag_pwd,omitempty"` // password for LisDiag telnet auth
	StartedAt  *time.Time    `json:"started_at,omitempty"`
	FinishedAt *time.Time    `json:"finished_at,omitempty"`
}

// QueueState represents the overall queue state.
type QueueState string

const (
	QueueIdle    QueueState = "idle"
	QueueRunning QueueState = "running"
	QueuePaused  QueueState = "paused"
	QueueDone    QueueState = "done"
)

// Queue manages sequential command execution with pause/resume/cancel.
type Queue struct {
	mu        sync.Mutex
	commands  []QueuedCommand
	current   int
	paused    bool
	cancelled bool
	state     QueueState
	onOutput  func(QueuedCommand) // callback for output streaming
	onStatus  func(QueuedCommand) // callback for status changes
	cmdCh     chan struct{}       // signals for pause/resume/cancel
	cancelCh  chan struct{}       // closed to abort the current in-flight command
}

// NewQueue creates a new command queue with optional output and status callbacks.
func NewQueue(onOutput, onStatus func(QueuedCommand)) *Queue {
	return &Queue{
		commands: make([]QueuedCommand, 0),
		state:    QueueIdle,
		onOutput: onOutput,
		onStatus: onStatus,
	}
}

// Add adds a command to the end of the queue.
func (q *Queue) Add(cmd QueuedCommand) {
	q.mu.Lock()
	defer q.mu.Unlock()
	if cmd.Status == "" {
		cmd.Status = StatusPending
	}
	q.commands = append(q.commands, cmd)
}

// AddMultiple adds multiple commands at once.
func (q *Queue) AddMultiple(cmds []QueuedCommand) {
	q.mu.Lock()
	defer q.mu.Unlock()
	for i := range cmds {
		if cmds[i].Status == "" {
			cmds[i].Status = StatusPending
		}
		q.commands = append(q.commands, cmds[i])
	}
}

// Start begins sequential execution. Blocks until queue is empty, paused
// (after current command), or cancelled. Each command is executed via
// the provided executor function.
func (q *Queue) Start(executor func(QueuedCommand) (string, error)) error {
	q.mu.Lock()
	if q.state == QueueRunning {
		q.mu.Unlock()
		return fmt.Errorf("queue already running")
	}
	if len(q.commands) == 0 {
		q.state = QueueDone
		q.mu.Unlock()
		return nil
	}
	q.state = QueueRunning
	q.cancelled = false
	q.paused = false
	q.cancelCh = make(chan struct{})
	q.mu.Unlock()

	for {
		q.mu.Lock()
		if q.cancelled {
			// Mark remaining as cancelled
			for i := q.current; i < len(q.commands); i++ {
				q.commands[i].Status = StatusCancelled
				if q.onStatus != nil {
					q.onStatus(q.commands[i])
				}
			}
			q.state = QueueIdle
			q.mu.Unlock()
			return fmt.Errorf("queue cancelled")
		}
		if q.paused {
			q.state = QueuePaused
			q.mu.Unlock()
			return nil
		}
		if q.current >= len(q.commands) {
			q.state = QueueDone
			q.mu.Unlock()
			return nil
		}

		cmd := &q.commands[q.current]
		cmd.Status = StatusRunning
		now := time.Now()
		cmd.StartedAt = &now
		if q.onStatus != nil {
			q.onStatus(*cmd)
		}
		q.mu.Unlock()

		// Execute the command (outside lock)
		output, err := executor(*cmd)

		q.mu.Lock()
		finTime := time.Now()
		cmd.FinishedAt = &finTime
		cmd.Output = output
		if err != nil {
			cmd.Status = StatusFailed
			cmd.Error = err.Error()
		} else {
			cmd.Status = StatusCompleted
		}
		if q.onOutput != nil {
			q.onOutput(*cmd)
		}
		if q.onStatus != nil {
			q.onStatus(*cmd)
		}
		q.current++
		q.mu.Unlock()
	}
}

// CancelCh returns the current cancel channel. Returns nil if the queue
// is not running. The channel is closed when Pause or Cancel is called,
// allowing in-flight executors to abort immediately.
func (q *Queue) CancelCh() chan struct{} {
	q.mu.Lock()
	defer q.mu.Unlock()
	return q.cancelCh
}

// Pause pauses execution after the current command completes.
// If a command is currently executing, the cancel channel is closed to
// abort it immediately rather than waiting for the command timeout.
func (q *Queue) Pause() {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.paused = true
	if q.cancelCh != nil {
		select {
		case <-q.cancelCh:
			// already closed
		default:
			close(q.cancelCh)
		}
	}
}

// Resume resumes execution from the paused position.
// Sets state to idle so Start() can be called again to continue execution.
func (q *Queue) Resume() {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.paused = false
	q.state = QueueIdle
}

// Cancel cancels all pending commands.
// If a command is currently executing, the cancel channel is closed to
// abort it immediately rather than waiting for the command timeout.
func (q *Queue) Cancel() {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.cancelled = true
	if q.cancelCh != nil {
		select {
		case <-q.cancelCh:
			// already closed
		default:
			close(q.cancelCh)
		}
	}
}

// Status returns the current queue state.
func (q *Queue) Status() (current int, total int, state QueueState) {
	q.mu.Lock()
	defer q.mu.Unlock()
	return q.current, len(q.commands), q.state
}

// Commands returns a copy of all commands in the queue.
func (q *Queue) Commands() []QueuedCommand {
	q.mu.Lock()
	defer q.mu.Unlock()
	result := make([]QueuedCommand, len(q.commands))
	copy(result, q.commands)
	return result
}

// Reset clears the queue and resets state to idle.
func (q *Queue) Reset() {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.commands = make([]QueuedCommand, 0)
	q.current = 0
	q.paused = false
	q.cancelled = false
	q.cancelCh = nil
	q.state = QueueIdle
}

// EnrichedStatus returns queue state with progress tracking fields.
type EnrichedStatus struct {
	Current   int             `json:"current"`
	Total     int             `json:"total"`
	State     string          `json:"state"`
	Commands  []QueuedCommand `json:"commands"`
	Percentage float64        `json:"percentage"`
	Remaining  int            `json:"remaining"`
	Message    string         `json:"message"`
}

// EnrichedStatus returns the current queue state plus progress tracking
// fields: percentage complete, remaining count, and a human-readable message.
func (q *Queue) EnrichedStatus() EnrichedStatus {
	q.mu.Lock()
	defer q.mu.Unlock()

	total := len(q.commands)
	current := q.current
	state := q.state

	var percentage float64
	var remaining int
	if total > 0 {
		percentage = float64(current) / float64(total) * 100
		if state == QueueRunning {
			remaining = total - current - 1
		} else {
			remaining = total - current
		}
		if remaining < 0 {
			remaining = 0
		}
	}

	message := buildProgressMessage(current, total, state, q.commands)

	cmds := make([]QueuedCommand, total)
	copy(cmds, q.commands)

	return EnrichedStatus{
		Current:    current,
		Total:      total,
		State:      string(state),
		Commands:   cmds,
		Percentage: percentage,
		Remaining:  remaining,
		Message:    message,
	}
}

// buildProgressMessage creates a human-readable progress string.
func buildProgressMessage(current, total int, state QueueState, cmds []QueuedCommand) string {
	if total == 0 {
		return "Queue empty"
	}
	if state == QueueIdle && current == 0 {
		return "Queue ready"
	}
	if state == QueueDone {
		return "Queue complete"
	}
	if state == QueuePaused {
		if current < total {
			return fmt.Sprintf("Paused at %d/%d (%s on %s)", current, total, cmds[current].Type, cmds[current].NodeName)
		}
		return "Paused"
	}
	if state == QueueRunning && current < total {
		cmd := cmds[current]
		return fmt.Sprintf("Executing %s on %s token %s (%d/%d)", cmd.Type, cmd.NodeName, cmd.TokenID, current+1, total)
	}
	return fmt.Sprintf("%d/%d complete", current, total)
}

// Remove removes a pending command by ID. Returns false if not found or
// not pending (already executed/running). Does not affect running queue.
func (q *Queue) Remove(id string) bool {
	q.mu.Lock()
	defer q.mu.Unlock()

	for i := q.current; i < len(q.commands); i++ {
		if q.commands[i].ID == id && q.commands[i].Status == StatusPending {
			q.commands = append(q.commands[:i], q.commands[i+1:]...)
			return true
		}
	}
	return false
}

// Reorder moves a pending command from one position to another among pending
// commands. Indices are absolute positions in the full command slice.
// Returns false if either index is out of range, refers to an already-
// executed command, or the queue is running.
func (q *Queue) Reorder(fromIdx int, toIdx int) bool {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.state == QueueRunning {
		return false
	}
	if fromIdx < q.current || fromIdx >= len(q.commands) {
		return false
	}
	if toIdx < q.current || toIdx >= len(q.commands) {
		return false
	}
	if fromIdx == toIdx {
		return true
	}
	if q.commands[fromIdx].Status != StatusPending {
		return false
	}

	cmd := q.commands[fromIdx]
	// Remove from source
	q.commands = append(q.commands[:fromIdx], q.commands[fromIdx+1:]...)
	// Insert at target (adjust if target shifted due to removal)
	if fromIdx < toIdx {
		toIdx-- // the slice shifted left
	}
	// Re-insert at target position
	q.commands = append(q.commands[:toIdx], append([]QueuedCommand{cmd}, q.commands[toIdx:]...)...)
	return true
}

// Restart resets all completed/failed/cancelled commands back to pending
// and resets the cursor to 0, allowing the queue to be re-run. Only allowed
// when the queue is idle or done (not while running or paused).
func (q *Queue) Restart() {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.state == QueueRunning || q.state == QueuePaused {
		return
	}

	for i := range q.commands {
		q.commands[i].Status = StatusPending
		q.commands[i].Error = ""
		q.commands[i].StartedAt = nil
		q.commands[i].FinishedAt = nil
		q.commands[i].Output = ""
	}
	q.current = 0
	q.paused = false
	q.cancelled = false
	q.cancelCh = nil
	q.state = QueueIdle
}

// ClearPending removes all pending commands but preserves the history of
// completed/failed/cancelled commands. Only allowed when not running.
func (q *Queue) ClearPending() {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.state == QueueRunning {
		return
	}

	// Keep commands up to current (executed ones) — remove the rest
	if q.current >= len(q.commands) {
		return
	}
	q.commands = q.commands[:q.current]
}

// InsertAt inserts a command at a specific position among pending commands.
// index is an absolute position in the full command slice. If index is
// beyond the slice length, the command is appended. Returns false if the
// queue is running or index refers to an already-executed slot.
func (q *Queue) InsertAt(cmd QueuedCommand, index int) bool {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.state == QueueRunning {
		return false
	}
	if index < q.current {
		return false
	}
	if cmd.Status == "" {
		cmd.Status = StatusPending
	}

	if index >= len(q.commands) {
		q.commands = append(q.commands, cmd)
		return true
	}

	// Insert at position
	q.commands = append(q.commands[:index], append([]QueuedCommand{cmd}, q.commands[index:]...)...)
	return true
}

// AddBatchFromNodesLISDiag generates LISDIAG telnet commands for LIS tokens.
// Uses the "io" command which combines irb (received) + orb (transmitted) in
// a single output — reverse-engineered from FUN_00406530 in LisDiag.exe.
// Per LIS token: exe×6 + io×6 = 12 commands total (down from 18 with separate
// irb+orb). Each io output contains both received and transmitted frames.
func (q *Queue) AddBatchFromNodesLISDiag(configs []types.NodeConfig, defaultPassword string) {
	for _, node := range configs {
		port, password := lisdiag.ParseParameters(node.LISDiagParams)
		if password == "" {
			password = defaultPassword
		}
		_ = port

		for _, tok := range node.Tokens {
			if tok.TokenType == types.TokenLIS {
				for exeNum := 1; exeNum <= 6; exeNum++ {
					channel := exeNum - 1
					tokenIDWithExe := fmt.Sprintf("%s_exe%d", tok.TokenID, exeNum)
					// exe N — set channel
					q.Add(QueuedCommand{
						ID: fmt.Sprintf("%s-LISDiag-%s-exe%d", node.Name, tok.TokenID, exeNum),
						Type: CmdLISDiag, NodeName: node.Name, TokenID: tokenIDWithExe,
						Command: fmt.Sprintf("exe %d", exeNum), Status: StatusPending,
						IPAddress: node.IPAddress, LISDiagPwd: password,
					})
					// io — combined irb+orb in one output
					q.Add(QueuedCommand{
						ID: fmt.Sprintf("%s-LISDiag-%s-exe%d-io", node.Name, tok.TokenID, exeNum),
						Type: CmdLISDiag, NodeName: node.Name, TokenID: tokenIDWithExe,
						Command: lisdiag.IOCommand(channel), Status: StatusPending,
						IPAddress: node.IPAddress, LISDiagPwd: password,
					})
				}
			}
		}
	}
}

// AddBatchFromNodes generates FBC+RPC+LOG commands for all nodes in a
// NodeConfig list. Matches Python "Print All Nodes" behavior: for each
// node, for each token, generate the appropriate print command.
// LIS tokens are handled based on lisMode: "rsu" generates RSU6 commands
// via DIA, "lisdiag" generates telnet commands for LisDiag on port 4321.
func (q *Queue) AddBatchFromNodes(configs []types.NodeConfig, sessionID string, sm *telnet.SessionManager, lisMode string) {
	// Reorder tokens to match the tree display order: FBC first (sorted by TokenID),
	// then RPC (sorted), then LOG, then LIS, then FTP.
	// This ensures queue items appear in the same order as the node tree.
	groupOrder := []types.TokenType{types.TokenFBC, types.TokenRPC, types.TokenLOG, types.TokenLIS, types.TokenFTP}
	for _, node := range configs {
		// Group tokens by type
		grouped := make(map[types.TokenType][]types.Token)
		for _, tok := range node.Tokens {
			grouped[tok.TokenType] = append(grouped[tok.TokenType], tok)
		}
		// Sort within each group by TokenID
		for _, gt := range grouped {
			sort.Slice(gt, func(i, j int) bool {
				return gt[i].TokenID < gt[j].TokenID
			})
		}
		// Build ordered token list matching tree display
		orderedTokens := make([]types.Token, 0)
		for _, tt := range groupOrder {
			orderedTokens = append(orderedTokens, grouped[tt]...)
		}
		// Include any tokens not in standard group order (e.g. custom types)
		for tt, toks := range grouped {
			found := false
			for _, gt := range groupOrder {
				if gt == tt {
					found = true
					break
				}
			}
			if !found {
				orderedTokens = append(orderedTokens, toks...)
			}
		}

		for _, tok := range orderedTokens {
			var cmd string
			var cmdType CommandType

			switch tok.TokenType {
			case types.TokenFBC:
				cmd = telnet.FBCPrint(tok.TokenID)
				cmdType = CmdFBC
			case types.TokenRPC:
				cmd = telnet.RPCPrint(tok.TokenID)
				cmdType = CmdRPC
			case types.TokenLOG:
				// LOG tokens use BsTool errlog (not telnet "print from log structure")
				q.Add(QueuedCommand{
					ID:        fmt.Sprintf("%s-LOG-%s", node.Name, tok.TokenID),
					Type:      CmdBsTool, NodeName: node.Name, TokenID: tok.TokenID,
					Command: "errlog", Status: StatusPending,
					IPAddress: node.IPAddress,
				})
				continue
			case types.TokenLIS:
				if lisMode == "lisdiag" {
					// LISDIAG path: generate telnet commands for LisDiag
					// Uses "io" command which combines irb+orb in one output
					_, password := lisdiag.ParseParameters(node.LISDiagParams)
					if password == "" {
						password = "password"
					}
					for exeNum := 1; exeNum <= 6; exeNum++ {
						channel := exeNum - 1
						tokenIDWithExe := fmt.Sprintf("%s_exe%d", tok.TokenID, exeNum)
						q.Add(QueuedCommand{
							ID: fmt.Sprintf("%s-LISDiag-%s-exe%d", node.Name, tok.TokenID, exeNum),
							Type: CmdLISDiag, NodeName: node.Name, TokenID: tokenIDWithExe,
							Command: fmt.Sprintf("exe %d", exeNum), Status: StatusPending,
							IPAddress: node.IPAddress, LISDiagPwd: password,
						})
						q.Add(QueuedCommand{
							ID: fmt.Sprintf("%s-LISDiag-%s-exe%d-io", node.Name, tok.TokenID, exeNum),
							Type: CmdLISDiag, NodeName: node.Name, TokenID: tokenIDWithExe,
							Command: lisdiag.IOCommand(channel), Status: StatusPending,
							IPAddress: node.IPAddress, LISDiagPwd: password,
						})
					}
					continue
				}
				// RSU6 path (default): generate rx+tx trace commands for each exe
				rsuid := tok.TokenID + "0000"
				for exeNum := 1; exeNum <= 6; exeNum++ {
					channel := exeNum - 1
					// TokenID encodes exe number: "162_exe1" so logwriter writes to
					// {station}_{ip}_{tokenID}_exe{N}.lis
					tokenIDWithExe := fmt.Sprintf("%s_exe%d", tok.TokenID, exeNum)
					// rx-trace command
					q.Add(QueuedCommand{
						ID:        fmt.Sprintf("%s-LIS-%s-exe%d-rx", node.Name, tok.TokenID, exeNum),
						Type:      CmdLIS,
						NodeName:  node.Name,
						TokenID:   tokenIDWithExe,
						Command:   fmt.Sprintf("print from rsu rx-trace %s %d", rsuid, channel),
						Status:    StatusPending,
						IPAddress: node.IPAddress,
					})
					// tx-trace command
					q.Add(QueuedCommand{
						ID:        fmt.Sprintf("%s-LIS-%s-exe%d-tx", node.Name, tok.TokenID, exeNum),
						Type:      CmdLIS,
						NodeName:  node.Name,
						TokenID:   tokenIDWithExe,
						Command:   fmt.Sprintf("print from rsu tx-trace %s %d", rsuid, channel),
						Status:    StatusPending,
						IPAddress: node.IPAddress,
					})
				}
				continue // Already added commands above, skip the generic Add below
			default:
				continue // Skip FTP, etc.
			}

			q.Add(QueuedCommand{
				ID:        fmt.Sprintf("%s-%s-%s", node.Name, tok.TokenType, tok.TokenID),
				Type:      cmdType,
				NodeName:  node.Name,
				TokenID:   tok.TokenID,
				Command:   cmd,
				Status:    StatusPending,
				IPAddress: node.IPAddress,
			})
		}
	}
}
