import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { NewExperiment } from '../pages/NewExperiment.jsx';
import * as apiModule from '../api.js';

const mockDatasets = [
  {
    id: 'd-1',
    name: 'Iris',
    n_rows: 150,
    n_features: 4,
    n_classes: 3,
    class_counts: { '0': 50, '1': 50, '2': 50 },
    profile: { sample_overlap: 0.12 },
    created_at: '2026-03-29T10:00:00Z',
  },
  {
    id: 'd-2',
    name: 'Wine',
    n_rows: 178,
    n_features: 13,
    n_classes: 3,
    class_counts: { '0': 59, '1': 75, '2': 48 },
    profile: null,
    created_at: '2026-03-29T11:00:00Z',
  },
];

describe('Phase 3: Configure Screen (NewExperiment)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('preselects dataset from query string and displays summary', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      if (path === '/recommend') return Promise.reject(new Error('501 Not Implemented'));
      return Promise.resolve({});
    });

    render(
      <MemoryRouter initialEntries={['/experiments/new?dataset=d-2']}>
        <Routes>
          <Route path="/experiments/new" element={<NewExperiment token="test-token" />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('dataset-select')).toHaveValue('d-2');
    });

    // Wine summary: 178 rows, 13 features, 3 classes, mildly imbalanced. Not profiled.
    const summary = screen.getByTestId('dataset-summary');
    expect(summary).toHaveTextContent('178 rows, 13 features, 3 classes, mildly imbalanced. Not profiled.');
  });

  it('renders AI recommendation when available and applies it', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      if (path === '/recommend') {
        return Promise.resolve({
          method: 'm1',
          params: {
            variant: 'mfhlsnn2014_midpoint',
            keep_fraction: 0.7,
            interior_keep_rate: 0.2,
          },
          rationale: 'Boundary selection prioritized for this feature space.',
        });
      }
      return Promise.resolve({});
    });

    render(
      <MemoryRouter initialEntries={['/experiments/new?dataset=d-1']}>
        <Routes>
          <Route path="/experiments/new" element={<NewExperiment token="test-token" />} />
        </Routes>
      </MemoryRouter>
    );

    // Wait for recommendation to load
    await waitFor(() => {
      expect(screen.getByTestId('use-recommendation-btn')).toBeInTheDocument();
      expect(
        screen.getByText(/Boundary selection prioritized for this feature space/i)
      ).toBeInTheDocument();
    });

    // Click Use recommendation
    fireEvent.click(screen.getByTestId('use-recommendation-btn'));

    // Check that method changed to m1
    expect(screen.getByTestId('method-radio-m1')).toBeChecked();
    expect(screen.getByTestId('variant-select')).toHaveValue('mfhlsnn2014_midpoint');
    expect(screen.getByTestId('keep-fraction-input')).toHaveValue(0.7);
    expect(screen.getByTestId('interior-keep-rate-input')).toHaveValue(0.2);
  });

  it('handles 501 / error for recommendations without showing a button', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      if (path === '/recommend') return Promise.reject(new Error('501 Not Implemented'));
      return Promise.resolve({});
    });

    render(
      <MemoryRouter initialEntries={['/experiments/new?dataset=d-1']}>
        <Routes>
          <Route path="/experiments/new" element={<NewExperiment token="test-token" />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('recommendation-unavailable')).toHaveTextContent(
        'Recommendation not available yet'
      );
    });

    expect(screen.queryByTestId('use-recommendation-btn')).not.toBeInTheDocument();
  });

  it('conditionally displays parameters based on selected method', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      if (path === '/recommend') return Promise.reject(new Error('501'));
      return Promise.resolve({});
    });

    render(
      <MemoryRouter initialEntries={['/experiments/new']}>
        <Routes>
          <Route path="/experiments/new" element={<NewExperiment token="test-token" />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('method-radio-hybrid')).toBeChecked();
    });

    // Default 'hybrid': all fields visible
    expect(screen.getByTestId('keep-fraction-input')).toBeInTheDocument();
    expect(screen.getByTestId('interior-keep-rate-input')).toBeInTheDocument();
    expect(screen.getByTestId('min-wins-input')).toBeInTheDocument();
    expect(screen.getByTestId('variant-select')).toBeInTheDocument();
    expect(screen.getByTestId('seed-input')).toBeInTheDocument();
    expect(screen.getByTestId('tune-checkbox')).toBeInTheDocument();

    // Switch to unreduced: hides keep_fraction, interior_keep_rate, min_wins
    fireEvent.click(screen.getByTestId('method-radio-unreduced'));
    expect(screen.queryByTestId('keep-fraction-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('interior-keep-rate-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('min-wins-input')).not.toBeInTheDocument();

    // Switch to m1: shows keep_fraction and interior_keep_rate, hides min_wins
    fireEvent.click(screen.getByTestId('method-radio-m1'));
    expect(screen.getByTestId('keep-fraction-input')).toBeInTheDocument();
    expect(screen.getByTestId('interior-keep-rate-input')).toBeInTheDocument();
    expect(screen.queryByTestId('min-wins-input')).not.toBeInTheDocument();

    // Switch to m3: hides keep_fraction and interior_keep_rate, shows min_wins
    fireEvent.click(screen.getByTestId('method-radio-m3'));
    expect(screen.queryByTestId('keep-fraction-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('interior-keep-rate-input')).not.toBeInTheDocument();
    expect(screen.getByTestId('min-wins-input')).toBeInTheDocument();
  });

  it('validates parameter ranges before submission', async () => {
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path) => {
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      if (path === '/recommend') return Promise.reject(new Error('501'));
      return Promise.resolve({});
    });

    render(
      <MemoryRouter initialEntries={['/experiments/new']}>
        <Routes>
          <Route path="/experiments/new" element={<NewExperiment token="test-token" />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('keep-fraction-input')).toBeInTheDocument();
    });

    // 1. Test keep_fraction out of bounds (< 0.2)
    fireEvent.change(screen.getByTestId('keep-fraction-input'), { target: { value: '0.1' } });
    fireEvent.click(screen.getByTestId('run-experiment-btn'));
    expect(await screen.findByText(/Keep fraction must be a number between 0.2 and 0.9/i)).toBeInTheDocument();

    // 2. Test keep_fraction > 0.9
    fireEvent.change(screen.getByTestId('keep-fraction-input'), { target: { value: '0.95' } });
    fireEvent.click(screen.getByTestId('run-experiment-btn'));
    expect(await screen.findByText(/Keep fraction must be a number between 0.2 and 0.9/i)).toBeInTheDocument();

    // Reset keep_fraction to valid value
    fireEvent.change(screen.getByTestId('keep-fraction-input'), { target: { value: '0.5' } });

    // 3. Test interior_keep_rate out of bounds (> 1.0)
    fireEvent.change(screen.getByTestId('interior-keep-rate-input'), { target: { value: '1.2' } });
    fireEvent.click(screen.getByTestId('run-experiment-btn'));
    expect(await screen.findByText(/Interior keep rate must be a number between 0.0 and 1.0/i)).toBeInTheDocument();

    // Reset interior_keep_rate
    fireEvent.change(screen.getByTestId('interior-keep-rate-input'), { target: { value: '0.1' } });

    // 4. Test min_wins < 1
    fireEvent.change(screen.getByTestId('min-wins-input'), { target: { value: '0' } });
    fireEvent.click(screen.getByTestId('run-experiment-btn'));
    expect(await screen.findByText(/Min wins must be an integer of at least 1/i)).toBeInTheDocument();

    // Reset min_wins
    fireEvent.change(screen.getByTestId('min-wins-input'), { target: { value: '2' } });

    // 5. Test seed negative
    fireEvent.change(screen.getByTestId('seed-input'), { target: { value: '-1' } });
    fireEvent.click(screen.getByTestId('run-experiment-btn'));
    expect(await screen.findByText(/Random seed must be a non-negative integer/i)).toBeInTheDocument();
  });

  it('submits valid experiment and calls onExperimentCreated', async () => {
    const postExperimentSpy = vi.fn().mockResolvedValue({ id: 'exp-created-123' });
    vi.spyOn(apiModule, 'apiFetch').mockImplementation((path, token, options) => {
      if (path === '/datasets') return Promise.resolve(mockDatasets);
      if (path === '/recommend') return Promise.reject(new Error('501'));
      if (path === '/experiments' && options?.method === 'POST') {
        return postExperimentSpy(options.body);
      }
      return Promise.resolve({});
    });

    const handleCreated = vi.fn();

    render(
      <MemoryRouter initialEntries={['/experiments/new?dataset=d-1']}>
        <Routes>
          <Route
            path="/experiments/new"
            element={<NewExperiment token="test-token" onExperimentCreated={handleCreated} />}
          />
          <Route path="/experiments/:id" element={<div>Experiment View Mock</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('run-experiment-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('run-experiment-btn'));

    await waitFor(() => {
      expect(postExperimentSpy).toHaveBeenCalledTimes(1);
    });

    expect(postExperimentSpy).toHaveBeenCalledWith({
      dataset_id: 'd-1',
      method: 'hybrid',
      params: {
        variant: 'fhlsnn2001',
        keep_fraction: 0.5,
        interior_keep_rate: 0.1,
        min_wins: 1,
        tune_hyperparams: true,
      },
      seed: 42,
    });

    expect(handleCreated).toHaveBeenCalledWith('exp-created-123');
  });
});
