import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Datasets, computeClassBalance } from '../pages/Datasets.jsx';
import * as apiModule from '../api.js';

const mockDatasetsList = [
  {
    id: 'd-1',
    name: 'Iris',
    n_rows: 150,
    n_features: 4,
    n_classes: 3,
    class_counts: { Setosa: 50, Versicolor: 50, Virginica: 50 },
    profile: { sample: true },
    source: 'benchmark',
  },
  {
    id: 'd-2',
    name: 'Wine',
    n_rows: 178,
    n_features: 13,
    n_classes: 3,
    class_counts: { Class1: 59, Class2: 71, Class3: 48 }, // 71/48 = ~1.479 -> Balanced
    profile: { sample: true },
    source: 'benchmark',
  },
  {
    id: 'd-3',
    name: 'Breast Cancer',
    n_rows: 569,
    n_features: 30,
    n_classes: 2,
    class_counts: { Benign: 357, Malignant: 212 }, // 357/212 = ~1.68 -> Mildly imbalanced
    profile: null,
    source: 'benchmark',
  },
  {
    id: 'd-4',
    name: 'Credit Card Fraud',
    n_rows: 25000,
    n_features: 28,
    n_classes: 2,
    class_counts: { Normal: 24500, Fraud: 500 }, // 24500/500 = 49 -> Imbalanced
    profile: { sample: true },
    source: 'user',
  },
];

describe('Phase 2: Datasets Screen & Balance Rules', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('computeClassBalance() helper', () => {
    it('returns "Balanced" when ratio is below 1.5', () => {
      // 50 / 50 = 1.0
      expect(computeClassBalance({ a: 50, b: 50 }).label).toBe('Balanced');
      // 140 / 100 = 1.4 (< 1.5)
      expect(computeClassBalance({ a: 140, b: 100 }).label).toBe('Balanced');
    });

    it('returns "Mildly imbalanced" when ratio is between 1.5 and 3.0 inclusive', () => {
      // 150 / 100 = 1.5
      expect(computeClassBalance({ a: 150, b: 100 }).label).toBe('Mildly imbalanced');
      // 200 / 100 = 2.0
      expect(computeClassBalance({ a: 200, b: 100 }).label).toBe('Mildly imbalanced');
      // 300 / 100 = 3.0
      expect(computeClassBalance({ a: 300, b: 100 }).label).toBe('Mildly imbalanced');
    });

    it('returns "Imbalanced" when ratio is strictly above 3.0', () => {
      // 310 / 100 = 3.1 (> 3)
      expect(computeClassBalance({ a: 310, b: 100 }).label).toBe('Imbalanced');
      // 1000 / 50 = 20
      expect(computeClassBalance({ a: 1000, b: 50 }).label).toBe('Imbalanced');
    });

    it('handles single-class, empty, or missing counts gracefully', () => {
      expect(computeClassBalance({ a: 100 }).label).toBe('Balanced');
      expect(computeClassBalance(null).label).toBe('not available');
      expect(computeClassBalance({}).label).toBe('not available');
    });
  });

  describe('Datasets Component Filtering and Actions', () => {
    it('renders datasets table with balance labels and status pills', async () => {
      vi.spyOn(apiModule, 'apiFetch').mockResolvedValue(mockDatasetsList);

      render(
        <BrowserRouter>
          <Datasets token="test-token" />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Iris')).toBeInTheDocument();
        expect(screen.getByText('Wine')).toBeInTheDocument();
        expect(screen.getByText('Credit Card Fraud')).toBeInTheDocument();
      });

      // Verify Class balance display
      expect(screen.getByTestId('balance-d-1')).toHaveTextContent('Balanced');
      expect(screen.getByTestId('balance-d-3')).toHaveTextContent('Mildly imbalanced');
      expect(screen.getByTestId('balance-d-4')).toHaveTextContent('Imbalanced');

      // Verify Source column is rendered since datasets include source
      expect(screen.getByRole('columnheader', { name: 'Source' })).toBeInTheDocument();
    });

    it('filters datasets by name search', async () => {
      vi.spyOn(apiModule, 'apiFetch').mockResolvedValue(mockDatasetsList);

      render(
        <BrowserRouter>
          <Datasets token="test-token" />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Iris')).toBeInTheDocument();
      });

      const searchInput = screen.getByTestId('name-search-input');
      fireEvent.change(searchInput, { target: { value: 'wine' } });

      expect(screen.getByText('Wine')).toBeInTheDocument();
      expect(screen.queryByText('Iris')).not.toBeInTheDocument();
      expect(screen.queryByText('Credit Card Fraud')).not.toBeInTheDocument();
    });

    it('filters datasets by row size', async () => {
      vi.spyOn(apiModule, 'apiFetch').mockResolvedValue(mockDatasetsList);

      render(
        <BrowserRouter>
          <Datasets token="test-token" />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Iris')).toBeInTheDocument();
      });

      const sizeSelect = screen.getByTestId('size-filter-select');

      // Under 1,000 rows
      fireEvent.change(sizeSelect, { target: { value: 'under_1000' } });
      expect(screen.getByText('Iris')).toBeInTheDocument();
      expect(screen.getByText('Wine')).toBeInTheDocument();
      expect(screen.getByText('Breast Cancer')).toBeInTheDocument();
      expect(screen.queryByText('Credit Card Fraud')).not.toBeInTheDocument();

      // Over 10,000 rows
      fireEvent.change(sizeSelect, { target: { value: 'over_10000' } });
      expect(screen.queryByText('Iris')).not.toBeInTheDocument();
      expect(screen.queryByText('Wine')).not.toBeInTheDocument();
      expect(screen.getByText('Credit Card Fraud')).toBeInTheDocument();
    });

    it('filters datasets by source (Benchmark vs My uploads)', async () => {
      vi.spyOn(apiModule, 'apiFetch').mockResolvedValue(mockDatasetsList);

      render(
        <BrowserRouter>
          <Datasets token="test-token" />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Iris')).toBeInTheDocument();
      });

      const sourceSelect = screen.getByTestId('source-filter-select');

      // Benchmark only
      fireEvent.change(sourceSelect, { target: { value: 'Benchmark' } });
      expect(screen.getByText('Iris')).toBeInTheDocument();
      expect(screen.queryByText('Credit Card Fraud')).not.toBeInTheDocument();

      // My uploads only
      fireEvent.change(sourceSelect, { target: { value: 'My uploads' } });
      expect(screen.queryByText('Iris')).not.toBeInTheDocument();
      expect(screen.getByText('Credit Card Fraud')).toBeInTheDocument();
    });

    it('navigates / calls callback on Reduce button click', async () => {
      vi.spyOn(apiModule, 'apiFetch').mockResolvedValue(mockDatasetsList);
      const handleSelect = vi.fn();

      render(
        <BrowserRouter>
          <Datasets token="test-token" onSelectDatasetForExperiment={handleSelect} />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('reduce-btn-d-1')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('reduce-btn-d-1'));
      expect(handleSelect).toHaveBeenCalledWith('d-1');
    });
  });
});
