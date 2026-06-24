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
    // The brand text appears once in the sidebar
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

  it('renders SysFile nav link', () => {
    renderComponent();
    expect(screen.getByText('SysFile')).toBeInTheDocument();
  });

  it('renders all 4 navigation links', () => {
    renderComponent();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Nodes')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('SysFile')).toBeInTheDocument();
  });

  it('has anchor elements for navigation links', () => {
    renderComponent();
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/');

    const nodesLink = screen.getByText('Nodes').closest('a');
    expect(nodesLink).toHaveAttribute('href', '/nodes');

    const reportsLink = screen.getByText('Reports').closest('a');
    expect(reportsLink).toHaveAttribute('href', '/reports');

    const sysfileLink = screen.getByText('SysFile').closest('a');
    expect(sysfileLink).toHaveAttribute('href', '/sysfile');
  });

  it('renders an Outlet (main content area)', () => {
    const { container } = renderComponent();
    // The main element is the content area
    const main = container.querySelector('main');
    expect(main).toBeInTheDocument();
  });

  it('renders a nav element as sidebar', () => {
    const { container } = renderComponent();
    const nav = container.querySelector('nav');
    expect(nav).toBeInTheDocument();
  });
});