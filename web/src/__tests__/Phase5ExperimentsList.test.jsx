import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ExperimentsList } from '../pages/ExperimentsList.jsx';
import * as apiModule from '../api.js';

const mockDatasets = [
  { id: 'ds-101', name: 'Iris Dataset' },
  { id: 'ds-202', name: 'Wine Quality' },
];

const mockExperiments = [
  {
    id: 'exp-1111-2222-3333',
    dataset_id: 'ds-101',
    method: 'hybrid',
    status: 'done',
    progress: 100,
    created_at: '2026-03-29T10:00:00Z',
  },
  {
    id: 'exp-4444-5555-6666',
    dataset_id: 'ds-202',
    method: 'm1',
    status: 'running',
    progress: 45,
    created_at: '2026-03-29T11:00:00Z',
  },
  {
    id: 'exp-7777-8888-9999',
    dataset_id: 'ds-101',
    method: 'unreduced',
    status: 'failed',
    progress: 10,
    created_at: '2026-03-29T12:00:00Z',
  },
];

describe('Phase 5: ExperimentsList Page', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders experiments list with dataset names, status pills, and short IDs', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/experiments') return Promise.resolve(mockExperiments);
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      return Promise.resolve([]);
    });

    render(
      <MemoryRouter>
        <ExperimentsList token="test-token" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('experiments-table')).toBeInTheDocument();
    });

    // Short IDs
    expect(screen.getByText('exp-1111')).toBeInTheDocument();
    expect(screen.getByText('exp-4444')).toBeInTheDocument();
    expect(screen.getByText('exp-7777')).toBeInTheDocument();

    // Dataset names
    expect(screen.getAllByText('Iris Dataset').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Wine Quality')).toBeInTheDocument();

    // Formatted Methods
    expect(screen.getByText('Hybrid')).toBeInTheDocument();
    expect(screen.getByText('M1 boundary filter')).toBeInTheDocument();
    expect(screen.getByText('Unreduced baseline')).toBeInTheDocument();

    // Progress values
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
    expect(screen.getByText('10%')).toBeInTheDocument();
  });

  it('filters experiments by search term', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/experiments') return Promise.resolve(mockExperiments);
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      return Promise.resolve([]);
    });

    render(
      <MemoryRouter>
        <ExperimentsList token="test-token" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Wine Quality')).toBeInTheDocument();
    });

    const searchInput = screen.getByTestId('search-experiments-input');
    fireEvent.change(searchInput, { target: { value: 'wine' } });

    expect(screen.getByText('Wine Quality')).toBeInTheDocument();
    expect(screen.queryByText('exp-1111')).not.toBeInTheDocument();
  });

  it('filters experiments by status', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/experiments') return Promise.resolve(mockExperiments);
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      return Promise.resolve([]);
    });

    render(
      <MemoryRouter>
        <ExperimentsList token="test-token" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('exp-1111')).toBeInTheDocument();
    });

    const statusSelect = screen.getByTestId('status-filter-select');

    // Filter for running
    fireEvent.change(statusSelect, { target: { value: 'running' } });
    expect(screen.getByText('exp-4444')).toBeInTheDocument();
    expect(screen.queryByText('exp-1111')).not.toBeInTheDocument();
    expect(screen.queryByText('exp-7777')).not.toBeInTheDocument();

    // Filter for failed
    fireEvent.change(statusSelect, { target: { value: 'failed' } });
    expect(screen.getByText('exp-7777')).toBeInTheDocument();
    expect(screen.queryByText('exp-4444')).not.toBeInTheDocument();
  });

  it('renders empty state when no experiments exist', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/experiments') return Promise.resolve([]);
      if (path === '/datasets') return Promise.resolve([]);
      return Promise.resolve([]);
    });

    render(
      <MemoryRouter>
        <ExperimentsList token="test-token" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No experiments found')).toBeInTheDocument();
    });

    expect(screen.getByTestId('new-experiment-btn')).toBeInTheDocument();
  });
});
