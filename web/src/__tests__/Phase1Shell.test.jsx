import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Stepper } from '../components/Stepper.jsx';
import { StatusPill } from '../components/StatusPill.jsx';
import { ProgressBar } from '../components/ProgressBar.jsx';

describe('Phase 1 Shell Components', () => {
  describe('Stepper Component', () => {
    it('renders all 4 workflow steps', () => {
      render(<Stepper activeStep={1} />);

      expect(screen.getByText('1 Datasets')).toBeInTheDocument();
      expect(screen.getByText('2 Configure')).toBeInTheDocument();
      expect(screen.getByText('3 Processing')).toBeInTheDocument();
      expect(screen.getByText('4 Results')).toBeInTheDocument();
    });

    it('sets the active class and aria-current on the active step', () => {
      const { rerender } = render(<Stepper activeStep={1} />);
      expect(screen.getByTestId('step-1')).toHaveClass('on');
      expect(screen.getByTestId('step-1')).toHaveAttribute('aria-current', 'step');
      expect(screen.getByTestId('step-2')).not.toHaveClass('on');

      rerender(<Stepper activeStep={2} />);
      expect(screen.getByTestId('step-2')).toHaveClass('on');
      expect(screen.getByTestId('step-2')).toHaveAttribute('aria-current', 'step');
      expect(screen.getByTestId('step-1')).not.toHaveClass('on');

      rerender(<Stepper activeStep={3} />);
      expect(screen.getByTestId('step-3')).toHaveClass('on');

      rerender(<Stepper activeStep={4} />);
      expect(screen.getByTestId('step-4')).toHaveClass('on');
    });
  });

  describe('StatusPill Component', () => {
    it('renders appropriate text and class for success/done/profiled', () => {
      const { rerender } = render(<StatusPill status="done" label="Done" />);
      const pill = screen.getByTestId('status-pill');
      expect(pill).toHaveTextContent('Done');
      expect(pill).toHaveClass('pill-success');

      rerender(<StatusPill status="Profiled" />);
      expect(screen.getByTestId('status-pill')).toHaveClass('pill-success');
    });

    it('renders appropriate class for running status', () => {
      render(<StatusPill status="running" label="Running" />);
      const pill = screen.getByTestId('status-pill');
      expect(pill).toHaveTextContent('Running');
      expect(pill).toHaveClass('pill-running');
    });

    it('renders appropriate class for queued/waiting status', () => {
      render(<StatusPill status="queued" label="Waiting" />);
      const pill = screen.getByTestId('status-pill');
      expect(pill).toHaveTextContent('Waiting');
      expect(pill).toHaveClass('pill-waiting');
    });

    it('renders appropriate class for failed/error status', () => {
      render(<StatusPill status="failed" label="Failed" />);
      const pill = screen.getByTestId('status-pill');
      expect(pill).toHaveTextContent('Failed');
      expect(pill).toHaveClass('pill-failed');
    });
  });

  describe('ProgressBar Component', () => {
    it('renders with role="progressbar" and correct aria attributes', () => {
      render(<ProgressBar progress={62} label="Training progress" />);
      const bar = screen.getByRole('progressbar', { name: 'Training progress' });

      expect(bar).toBeInTheDocument();
      expect(bar).toHaveAttribute('aria-valuenow', '62');
      expect(bar).toHaveAttribute('aria-valuemin', '0');
      expect(bar).toHaveAttribute('aria-valuemax', '100');
    });

    it('sets the fill width according to the progress value', () => {
      render(<ProgressBar progress={62} />);
      const fill = screen.getByTestId('progress-bar-fill');
      expect(fill).toHaveStyle({ width: '62%' });
    });

    it('clamps negative values to 0% and values above 100 to 100%', () => {
      const { rerender } = render(<ProgressBar progress={-10} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
      expect(screen.getByTestId('progress-bar-fill')).toHaveStyle({ width: '0%' });

      rerender(<ProgressBar progress={150} />);
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
      expect(screen.getByTestId('progress-bar-fill')).toHaveStyle({ width: '100%' });
    });
  });
});
