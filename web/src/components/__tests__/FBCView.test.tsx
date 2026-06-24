import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import FBCView from '../FBCView';
import type { ApiFBCModule } from '../../types/api';

const modules: ApiFBCModule[] = [
  {
    module_position: 1,
    channels: [
      { channel_position: 1, channel_type: 'AI8' },
      { channel_position: 2, channel_type: 'DI16' },
      { channel_position: 3, channel_type: 'AO4' },
    ],
  },
  {
    module_position: 2,
    channels: [
      { channel_position: 1, channel_type: 'N/E' },
    ],
  },
  {
    module_position: 3,
    channels: [
      { channel_position: 1, channel_type: 'DO16' },
      { channel_position: 2, channel_type: 'DO16' },
    ],
  },
];

describe('FBCView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing with modules', () => {
    render(<FBCView modules={modules} />);
    expect(screen.getByText('Position 1')).toBeInTheDocument();
  });

  it('shows empty state when no modules', () => {
    render(<FBCView modules={[]} />);
    expect(screen.getByText('No FBC modules found. Run a scan to populate data.')).toBeInTheDocument();
  });

  it('displays module positions for all modules', () => {
    render(<FBCView modules={modules} />);
    expect(screen.getByText('Position 1')).toBeInTheDocument();
    expect(screen.getByText('Position 2')).toBeInTheDocument();
    expect(screen.getByText('Position 3')).toBeInTheDocument();
  });

  it('shows channel count per module', () => {
    render(<FBCView modules={modules} />);
    expect(screen.getByText('3 channels')).toBeInTheDocument();
    expect(screen.getByText('1 channel')).toBeInTheDocument();
    expect(screen.getByText('2 channels')).toBeInTheDocument();
  });

  it('shows channel labels (AI, DI, AO, DO)', () => {
    render(<FBCView modules={modules} />);
    // AI8 → AI, DI16 → DI, AO4 → AO, DO16 → DO
    const aiLabels = screen.getAllByText('AI');
    expect(aiLabels.length).toBeGreaterThan(0);
    const diLabels = screen.getAllByText('DI');
    expect(diLabels.length).toBeGreaterThan(0);
    const aoLabels = screen.getAllByText('AO');
    expect(aoLabels.length).toBeGreaterThan(0);
    const doLabels = screen.getAllByText('DO');
    expect(doLabels.length).toBeGreaterThan(0);
  });

  it('shows N/E label for not-equipped channels', () => {
    render(<FBCView modules={modules} />);
    // N/E maps to '—'
    const neLabels = screen.getAllByText('—');
    expect(neLabels.length).toBeGreaterThan(0);
  });

  it('shows Totals section with module and channel counts', () => {
    render(<FBCView modules={modules} />);
    expect(screen.getByText('Totals')).toBeInTheDocument();
    expect(screen.getByText('3 modules')).toBeInTheDocument();
    // Total channels: 3 + 1 + 2 = 6
    expect(screen.getByText('6 channels')).toBeInTheDocument();
  });

  it('shows type breakdown in totals', () => {
    render(<FBCView modules={modules} />);
    // We have AI8: 1, DI16: 1, AO4: 1, N/E: 1, DO16: 2
    expect(screen.getByText('AI8: 1')).toBeInTheDocument();
    expect(screen.getByText('DO16: 2')).toBeInTheDocument();
    expect(screen.getByText('N/E: 1')).toBeInTheDocument();
  });

  it('renders channel cells with title tooltips', () => {
    const { container } = render(<FBCView modules={modules} />);
    const titledElements = container.querySelectorAll('[title]');
    expect(titledElements.length).toBeGreaterThan(0);
    // Check a specific tooltip
    const aiTooltip = Array.from(titledElements).find((el) =>
      el.getAttribute('title')?.includes('AI8'),
    );
    expect(aiTooltip).toBeTruthy();
  });

  it('shows channel position numbers', () => {
    render(<FBCView modules={modules} />);
    // Channel positions are 1, 2, 3
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
    expect(screen.getAllByText('3').length).toBeGreaterThan(0);
  });

  it('handles modules with empty channels array', () => {
    const modsWithEmpty: ApiFBCModule[] = [
      { module_position: 1, channels: [] },
    ];
    render(<FBCView modules={modsWithEmpty} />);
    expect(screen.getByText('Position 1')).toBeInTheDocument();
    expect(screen.getAllByText('0 channels').length).toBeGreaterThan(0);
  });
});