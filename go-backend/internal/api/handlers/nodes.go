package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/goranjovic55/LOGReport/internal/models"
	"github.com/goranjovic55/LOGReport/internal/nodes"
)

type NodesHandler struct {
	manager *nodes.Manager
}

func NewNodesHandler(m *nodes.Manager) *NodesHandler {
	return &NodesHandler{manager: m}
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}

func (h *NodesHandler) GetAll(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, h.manager.GetAll())
}

func (h *NodesHandler) GetOne(w http.ResponseWriter, r *http.Request) {
	name := chi.URLParam(r, "name")
	node, err := h.manager.GetByName(name)
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, node)
}

func (h *NodesHandler) Create(w http.ResponseWriter, r *http.Request) {
	var node models.Node
	if err := json.NewDecoder(r.Body).Decode(&node); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}
	if err := h.manager.Add(node); err != nil {
		writeError(w, http.StatusConflict, err.Error())
		return
	}
	h.manager.Save()
	writeJSON(w, http.StatusCreated, node)
}

func (h *NodesHandler) Update(w http.ResponseWriter, r *http.Request) {
	name := chi.URLParam(r, "name")
	var node models.Node
	if err := json.NewDecoder(r.Body).Decode(&node); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}
	if err := h.manager.Update(name, node); err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}
	h.manager.Save()
	writeJSON(w, http.StatusOK, node)
}

func (h *NodesHandler) Delete(w http.ResponseWriter, r *http.Request) {
	name := chi.URLParam(r, "name")
	if err := h.manager.Delete(name); err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}
	h.manager.Save()
	w.WriteHeader(http.StatusNoContent)
}
