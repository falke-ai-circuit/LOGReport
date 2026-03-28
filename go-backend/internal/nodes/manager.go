package nodes

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"

	"github.com/goranjovic55/LOGReport/internal/models"
)

type Manager struct {
	mu    sync.RWMutex
	nodes []models.Node
	path  string
}

func NewManager(path string) (*Manager, error) {
	m := &Manager{path: path}
	if err := m.Load(); err != nil {
		if os.IsNotExist(err) {
			m.nodes = []models.Node{}
			return m, nil
		}
		return nil, err
	}
	return m, nil
}

func (m *Manager) Load() error {
	m.mu.Lock()
	defer m.mu.Unlock()
	data, err := os.ReadFile(m.path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, &m.nodes)
}

func (m *Manager) Save() error {
	m.mu.RLock()
	defer m.mu.RUnlock()
	data, err := json.MarshalIndent(m.nodes, "", "    ")
	if err != nil {
		return err
	}
	return os.WriteFile(m.path, data, 0644)
}

func (m *Manager) GetAll() []models.Node {
	m.mu.RLock()
	defer m.mu.RUnlock()
	result := make([]models.Node, len(m.nodes))
	copy(result, m.nodes)
	return result
}

func (m *Manager) GetByName(name string) (*models.Node, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	for i := range m.nodes {
		if m.nodes[i].Name == name {
			n := m.nodes[i]
			return &n, nil
		}
	}
	return nil, fmt.Errorf("node %q not found", name)
}

func (m *Manager) Add(node models.Node) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, n := range m.nodes {
		if n.Name == node.Name {
			return fmt.Errorf("node %q already exists", node.Name)
		}
	}
	if node.Status == "" {
		node.Status = "offline"
	}
	m.nodes = append(m.nodes, node)
	return nil
}

func (m *Manager) Update(name string, updated models.Node) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	for i := range m.nodes {
		if m.nodes[i].Name == name {
			m.nodes[i] = updated
			return nil
		}
	}
	return fmt.Errorf("node %q not found", name)
}

func (m *Manager) Delete(name string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	for i := range m.nodes {
		if m.nodes[i].Name == name {
			m.nodes = append(m.nodes[:i], m.nodes[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("node %q not found", name)
}
