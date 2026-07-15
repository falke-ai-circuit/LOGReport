import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../Layout';

function renderComponent(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Layout />
    </MemoryRouter>,
  );
}

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    renderComponent();
    expect(screen.getByText('LOGReport')).toBeInTheDocument();
  });

  it('shows the LOGReport brand in the sidebar', () => {
    renderComponent();
    const brand = screen.getAllByText('LOGReport');
    expect(brand.length).toBeGreaterThan(0);
  });

  it('renders Dashboard nav link', () => {
    renderComponent();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders Nodes nav link', () => {
    renderComponent();
    expect(screen.getByText('Nodes')).toBeInTheDocument();
  });

  it('renders Reports nav link', () => {
    renderComponent();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('renders Commander nav link', () => {
    renderComponent();
    expect(screen.getByText('Commander')).toBeInTheDocument();
  });

  it('renders all 4 navigation links', () => {
    renderComponent();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Nodes')).toBeInTheDocument();
    expect(screen.getByText('Commander')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('has anchor elements for navigation links', () => {
    renderComponent();
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/');

    const nodesLink = screen.getByText('Nodes').closest('a');
    expect(nodesLink).toHaveAttribute('href', '/nodes');

    const commanderLink = screen.getByText('Commander').closest('a');
    expect(commanderLink).toHaveAttribute('href', '/commander');

    const reportsLink = screen.getByText('Reports').closest('a');
    expect(reportsLink).toHaveAttribute('href', '/reports');
  });

  it('renders an Outlet (main content area)', () => {
    const { container } = renderComponent();
    const main = container.querySelector('main');
    expect(main).toBeInTheDocument();
  });
});