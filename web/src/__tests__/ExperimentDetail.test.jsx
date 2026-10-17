import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { ExperimentDetail } from '../pages/ExperimentDetail.jsx';
import * as apiModule from '../api.js';

describe('ExperimentDetail Component Tests', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  // Test 1: the progress bar renders the row value
  it('renders the progress bar with the exact row value from the database', () => {
    const mockExp = {
      id: 'exp-101',
      method: 'hybrid',
      status: 'running',
      progress: 65,
      metrics: null,
      error: null,
    };

    // Render with initialExperiment so it renders immediately
    render(
      <ExperimentDetail
        experimentId="exp-101"
        token="test-token"
        initialExperiment={mockExp}
      />
    );

    const progressValueEl = screen.getByTestId('progress-value');
    expect(progressValueEl).toHaveTextContent('65%');

    const progressFillEl = screen.getByTestId('progress-fill');
    expect(progressFillEl).toHaveStyle({ width: '65%' });
    expect(progressFillEl).toHaveTextContent('65%');
  });

  // Test 2: polling stops on 'done'
  it('polls the API every 2 seconds and stops polling when status is done', async () => {
    // Initial experiment is 'running'
    const expRunning = {
      id: 'exp-202',
      method: 'm1',
      status: 'running',
      progress: 50,
      metrics: null,
    };

    const expDone = {
      id: 'exp-202',
      method: 'm1',
      status: 'done',
      progress: 100,
      metrics: { dummy: true },
    };

    // Mock apiFetch to return running first, then done, then throw if called again
    const apiSpy = vi.spyOn(apiModule, 'apiFetch');
    apiSpy
      .mockResolvedValueOnce(expRunning) // First poll
      .mockResolvedValueOnce(expDone); // Second poll (status done)

    await act(async () => {
      render(
        <ExperimentDetail
          experimentId="exp-202"
          token="test-token"
          initialExperiment={expRunning}
          pollInterval={2000}
        />
      );
    });

    expect(apiSpy).toHaveBeenCalledTimes(1);

    // Advance 2 seconds -> should poll second time and receive expDone
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });
    expect(apiSpy).toHaveBeenCalledTimes(2);

    // Verify status is now 'done'
    const statusBadge = screen.getByTestId('status-badge');
    expect(statusBadge).toHaveTextContent('done');

    // Advance another 2000ms and 4000ms -> polling MUST have stopped, call count remains 2
    await act(async () => {
      vi.advanceTimersByTime(4000);
    });
    expect(apiSpy).toHaveBeenCalledTimes(2);
  });

  // Test 3: null metrics render 'not available'
  it('renders not available when metrics are null, and renders JSON when present', () => {
    const expWithNullMetrics = {
      id: 'exp-303',
      method: 'unreduced',
      status: 'queued',
      progress: 0,
      metrics: null,
    };

    const { rerender } = render(
      <ExperimentDetail
        experimentId="exp-303"
        token="test-token"
        initialExperiment={expWithNullMetrics}
      />
    );

    const emptyMetricsEl = screen.getByTestId('metrics-not-available');
    expect(emptyMetricsEl).toHaveTextContent('not available');
    expect(screen.queryByTestId('metrics-json')).not.toBeInTheDocument();

    // Rerender with real metrics
    const expWithMetrics = {
      ...expWithNullMetrics,
      status: 'done',
      progress: 100,
      metrics: { accuracy: 0.95, reduction: 0.8 },
    };

    rerender(
      <ExperimentDetail
        experimentId="exp-303"
        token="test-token"
        initialExperiment={expWithMetrics}
      />
    );

    const metricsJsonEl = screen.getByTestId('metrics-json');
    expect(metricsJsonEl).toBeInTheDocument();
    expect(metricsJsonEl.textContent).toContain('"accuracy": 0.95');
    expect(metricsJsonEl.textContent).toContain('"reduction": 0.8');
    expect(screen.queryByTestId('metrics-not-available')).not.toBeInTheDocument();
  });
});
