import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import {
  ExperimentDetail,
  formatDelta,
  generateExperimentCsv,
} from '../pages/ExperimentDetail.jsx';
import * as apiModule from '../api.js';

describe('Phase 4: Experiment Processing & Results View', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('formatDelta helper', () => {
    it('formats positive delta with + and pp vs unreduced', () => {
      expect(formatDelta(0.957, 0.956)).toBe('+0.1 pp vs unreduced');
    });

    it('formats negative delta with - and pp vs unreduced', () => {
      expect(formatDelta(0.92, 0.95)).toBe('-3.0 pp vs unreduced');
    });

    it('returns null when either current or reference is missing', () => {
      expect(formatDelta(null, 0.95)).toBeNull();
      expect(formatDelta(0.95, null)).toBeNull();
      expect(formatDelta(undefined, 0.95)).toBeNull();
    });
  });

  describe('generateExperimentCsv helper', () => {
    it('builds CSV content correctly from metrics, reference and per_class', () => {
      const exp = {
        id: 'exp-test-csv',
        metrics: {
          accuracy: 0.957,
          macro_f1: 0.956,
          stored_vectors: 48,
          reduction_vs_raw: 0.5,
          n_segments: 24,
          zero_mem_frac: 0.0,
          n_fit: 96,
          n_val: 24,
          n_test: 30,
          best_theta: 0.4,
          best_gamma: 0.25,
          reference: {
            accuracy: 0.956,
            macro_f1: 0.955,
            stored_vectors: 96,
            n_segments: 48,
          },
        },
        facts: {
          per_class: [
            { label: 'Setosa', before: 32, kept: 16 },
            { label: 'Versicolor', before: 32, kept: 16 },
          ],
        },
      };

      const csv = generateExperimentCsv(exp);
      expect(csv).toContain('Metric,Value,Reference');
      expect(csv).toContain('Accuracy,95.7%,95.6%');
      expect(csv).toContain('Stored vectors,48,96');
      expect(csv).toContain('Reduction vs raw,50.0%,not available');
      expect(csv).toContain('Class,Before,Kept,Share Kept');
      expect(csv).toContain('Setosa,32,16,50%');
      expect(csv).toContain('Versicolor,32,16,50%');
    });
  });

  describe('Polling behavior', () => {
    it('stops polling when status becomes done', async () => {
      const runningExp = {
        id: 'exp-p1',
        method: 'hybrid',
        status: 'running',
        progress: 40,
      };

      const doneExp = {
        id: 'exp-p1',
        method: 'hybrid',
        status: 'done',
        progress: 100,
        metrics: { accuracy: 0.95 },
      };

      const apiSpy = vi.spyOn(apiModule, 'apiFetch');
      apiSpy.mockResolvedValueOnce(runningExp).mockResolvedValueOnce(doneExp);

      await act(async () => {
        render(
          <MemoryRouter>
            <ExperimentDetail
              experimentId="exp-p1"
              token="test-token"
              initialExperiment={runningExp}
              pollInterval={2000}
            />
          </MemoryRouter>
        );
      });

      expect(apiSpy).toHaveBeenCalledTimes(1);

      // Advance by 2 seconds -> should fetch doneExp and stop
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });
      expect(apiSpy).toHaveBeenCalledTimes(2);

      // Advance further -> no more calls
      await act(async () => {
        vi.advanceTimersByTime(6000);
      });
      expect(apiSpy).toHaveBeenCalledTimes(2);
    });

    it('stops polling when status becomes failed', async () => {
      const runningExp = {
        id: 'exp-p2',
        method: 'm3',
        status: 'running',
        progress: 25,
      };

      const failedExp = {
        id: 'exp-p2',
        method: 'm3',
        status: 'failed',
        error: 'CUDA out of memory error during segment expansion',
      };

      const apiSpy = vi.spyOn(apiModule, 'apiFetch');
      apiSpy.mockResolvedValueOnce(runningExp).mockResolvedValueOnce(failedExp);

      await act(async () => {
        render(
          <MemoryRouter>
            <ExperimentDetail
              experimentId="exp-p2"
              token="test-token"
              initialExperiment={runningExp}
              pollInterval={2000}
            />
          </MemoryRouter>
        );
      });

      expect(apiSpy).toHaveBeenCalledTimes(1);

      // Advance by 2s -> reaches failedExp
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });
      expect(apiSpy).toHaveBeenCalledTimes(2);

      // Advance further -> polling has stopped
      await act(async () => {
        vi.advanceTimersByTime(4000);
      });
      expect(apiSpy).toHaveBeenCalledTimes(2);

      // Failed view is rendered
      expect(screen.getByTestId('failed-view')).toBeInTheDocument();
      expect(screen.getByTestId('failed-error-text')).toHaveTextContent(
        'CUDA out of memory error during segment expansion'
      );
      expect(screen.getByTestId('back-to-configure-btn')).toBeInTheDocument();
    });
  });

  describe('Processing view details', () => {
    it('renders stages list from facts.stage and live logs', () => {
      const processingExp = {
        id: 'exp-proc',
        method: 'hybrid',
        status: 'running',
        progress: 60,
        facts: {
          stage: 'tune',
          log: ['log line 1', 'log line 2', 'best so far: theta 0.4, gamma 0.25'],
        },
      };

      render(
        <MemoryRouter>
          <ExperimentDetail
            experimentId="exp-proc"
            token="test-token"
            initialExperiment={processingExp}
          />
        </MemoryRouter>
      );

      // Cancel button disabled with title tooltip
      const cancelBtn = screen.getByTestId('cancel-run-btn');
      expect(cancelBtn).toBeDisabled();
      expect(cancelBtn).toHaveAttribute('title', 'Cancel is not available yet');

      // View results button disabled
      expect(screen.getByTestId('view-results-btn')).toBeDisabled();

      // Stages checked
      expect(screen.getByText('1. Profile dataset')).toBeInTheDocument();
      expect(screen.getByText('3. Tune theta and gamma')).toBeInTheDocument();

      // Log lines
      const logEl = screen.getByTestId('live-log');
      expect(logEl).toHaveTextContent('best so far: theta 0.4, gamma 0.25');
    });

    it('renders fallback single row Working when facts.stage is missing', () => {
      const processingExp = {
        id: 'exp-proc-nostage',
        method: 'm1',
        status: 'running',
        progress: 15,
        facts: {
          log: [],
        },
      };

      render(
        <MemoryRouter>
          <ExperimentDetail
            experimentId="exp-proc-nostage"
            token="test-token"
            initialExperiment={processingExp}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Working')).toBeInTheDocument();
      expect(screen.getByTestId('empty-log')).toHaveTextContent('No log lines yet');
    });
  });

  describe('Results view sections and missing data handling', () => {
    it('renders not available when chart, PCA, table, and explanation data are missing', () => {
      const doneExpMissingData = {
        id: 'exp-done-empty',
        method: 'hybrid',
        status: 'done',
        progress: 100,
        metrics: null,
        facts: null,
      };

      render(
        <MemoryRouter>
          <ExperimentDetail
            experimentId="exp-done-empty"
            token="test-token"
            initialExperiment={doneExpMissingData}
          />
        </MemoryRouter>
      );

      // Metric cards container has not available values
      const cards = screen.getByTestId('metric-cards-container');
      expect(cards).toHaveTextContent('not available');

      // Individual sections show not available
      expect(screen.getByTestId('curve-not-available')).toHaveTextContent('not available');
      expect(screen.getByTestId('pca-not-available')).toHaveTextContent('not available');
      expect(screen.getByTestId('per-class-not-available')).toHaveTextContent('not available');
      expect(screen.getByTestId('explanation-not-available')).toHaveTextContent('not available');
    });

    it('renders all results visualizations when full data is present', () => {
      const completeExp = {
        id: 'exp-done-full',
        dataset_name: 'Iris',
        method: 'hybrid',
        seed: 42,
        status: 'done',
        progress: 100,
        metrics: {
          accuracy: 0.957,
          macro_f1: 0.956,
          stored_vectors: 48,
          reduction_vs_raw: 0.5,
          n_segments: 24,
          zero_mem_frac: 0.0,
          n_fit: 96,
          n_val: 24,
          n_test: 30,
          reference: {
            accuracy: 0.956,
            macro_f1: 0.955,
            stored_vectors: 96,
            n_segments: 48,
          },
        },
        facts: {
          curve: {
            series: [
              {
                name: 'Hybrid',
                style: 'solid',
                points: [
                  { x: 0, y: 0.957 },
                  { x: 0.5, y: 0.957 },
                ],
              },
            ],
          },
          pca: {
            points: [
              { x: -2.68, y: 0.32, label: 'Setosa', kept: true },
              { x: 1.25, y: -0.45, label: 'Versicolor', kept: false },
            ],
          },
          per_class: [
            { label: 'Setosa', before: 32, kept: 16 },
            { label: 'Versicolor', before: 32, kept: 16 },
          ],
          explanation: {
            text: 'Hybrid kept 48 of 96 training patterns (50.0%).',
          },
        },
      };

      render(
        <MemoryRouter>
          <ExperimentDetail
            experimentId="exp-done-full"
            token="test-token"
            initialExperiment={completeExp}
          />
        </MemoryRouter>
      );

      // Verify SVG chart and scatter rendered
      expect(screen.getByTestId('accuracy-reduction-svg')).toBeInTheDocument();
      expect(screen.getByTestId('pca-before-svg')).toBeInTheDocument();
      expect(screen.getByTestId('pca-after-svg')).toBeInTheDocument();

      // Verify Table rendered
      expect(screen.getByTestId('per-class-table')).toBeInTheDocument();
      expect(screen.getByRole('cell', { name: 'Setosa' })).toBeInTheDocument();

      // Verify Explanation text and metadata
      expect(screen.getByTestId('explanation-text')).toHaveTextContent(
        'Hybrid kept 48 of 96 training patterns (50.0%).'
      );
      expect(screen.getByTestId('explanation-metadata')).toHaveTextContent(
        'Seed 42. Fit 96, validation 24, test 30.'
      );
    });
  });
});
