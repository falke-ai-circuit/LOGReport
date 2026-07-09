import { useState, useEffect, useCallback } from 'react';

export interface Project {
  id: number;
  project_number: string;
  ship_name: string;
  log_root: string;
  status: string;
  created_at: string;
  updated_at: string;
}

const STORAGE_KEY = 'activeProjectId';
const LOGROOT_KEY = 'logRoot';
const EVENT_NAME = 'activeProjectChange';

/**
 * Shared hook that manages the active project across all pages.
 * Uses localStorage as the source of truth and a custom event
 * so every component stays in sync without prop drilling.
 *
 * - Only Dashboard selects the project (and sets logRoot from project.log_root).
 * - Nodes, Commander, Reports read the active project and react to changes.
 * - StatusBar shows the active project name.
 */
export function useActiveProject() {
  const [activeProjectId, setActiveProjectId] = useState<number | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? parseInt(stored, 10) : null;
  });

  const [activeLogRoot, setActiveLogRoot] = useState<string>(() => {
    return localStorage.getItem(LOGROOT_KEY) || '';
  });

  useEffect(() => {
    function handleChange() {
      const stored = localStorage.getItem(STORAGE_KEY);
      const newId = stored ? parseInt(stored, 10) : null;
      setActiveProjectId(newId);
      const newLogRoot = localStorage.getItem(LOGROOT_KEY) || '';
      setActiveLogRoot(newLogRoot);
    }
    window.addEventListener(EVENT_NAME, handleChange);
    window.addEventListener('storage', handleChange);
    return () => {
      window.removeEventListener(EVENT_NAME, handleChange);
      window.removeEventListener('storage', handleChange);
    };
  }, []);

  const selectProject = useCallback((id: number | null, logRoot?: string) => {
    if (id !== null) {
      localStorage.setItem(STORAGE_KEY, String(id));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
    if (logRoot !== undefined) {
      if (logRoot) {
        localStorage.setItem(LOGROOT_KEY, logRoot);
      } else {
        localStorage.removeItem(LOGROOT_KEY);
      }
      // Notify the backend about the new log root
      fetch('/api/v1/logs/setroot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: logRoot || '' }),
      }).catch(() => {});
    }
    // Fire event so all other components update
    window.dispatchEvent(new CustomEvent(EVENT_NAME));
  }, []);

  const selectLogRoot = useCallback((logRoot: string) => {
    localStorage.setItem(LOGROOT_KEY, logRoot);
    fetch('/api/v1/logs/setroot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: logRoot }),
    }).catch(() => {});
    window.dispatchEvent(new CustomEvent(EVENT_NAME));
  }, []);

  return { activeProjectId, activeLogRoot, selectProject, selectLogRoot };
}

/**
 * Fetch the full project objects list (for lookups, dropdowns, etc.)
 */
export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function fetchProjects() {
      try {
        const res = await fetch('/api/v1/projects');
        if (!res.ok) return;
        const data = await res.json();
        if (mounted) setProjects(data.projects || []);
      } catch { /* ignore */ } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchProjects();
    return () => { mounted = false; };
  }, []);

  return { projects, loading, setProjects };
}