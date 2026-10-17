import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api.js';

export function ExperimentDetail({ experimentId, token, initialExperiment = null, pollInterval = 2000, onBack }) {
  const [experiment, setExperiment] = useState(initialExperiment);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    if (initialExperiment) {
      setExperiment(initialExperiment);
    }
  }, [initialExperiment]);

  useEffect(() => {
    if (!experimentId || !token) return;

    let isMounted = true;
    let intervalId = null;

    const poll = async () => {
      try {
        const data = await apiFetch(`/experiments/${experimentId}`, token);
        if (!isMounted) return;
        setExperiment(data);

        // Stop polling if status is 'done' or 'failed'
        if (data && (data.status === 'done' || data.status === 'failed')) {
          if (intervalId) clearInterval(intervalId);
          setIsPolling(false);
        }
      } catch (err) {
        if (isMounted) setErrorMsg(err.message || 'Error polling experiment');
      }
    };

    // If initial experiment is already terminal, do not start interval
    if (initialExperiment && (initialExperiment.status === 'done' || initialExperiment.status === 'failed')) {
      setIsPolling(false);
      return;
    }

    // Run first check
    poll();

    // Start interval
    intervalId = setInterval(poll, pollInterval);

    // Clean up on unmount
    return () => {
      isMounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [experimentId, token, pollInterval]);

  if (!experiment && !errorMsg) {
    return <div className="card"><p>Loading experiment details...</p></div>;
  }

  const progress = experiment?.progress;
  const status = experiment?.status || 'unknown';
  const metrics = experiment?.metrics;

  return (
    <div className="card" data-testid="experiment-detail-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Experiment Detail</h2>
        {onBack && (
          <button className="btn btn-secondary" onClick={onBack}>
            Back to Datasets
          </button>
        )}
      </div>

      {errorMsg && <div className="alert alert-danger" role="alert">{errorMsg}</div>}

      <div style={{ marginBottom: '1rem' }}>
        <strong>Experiment ID:</strong> <span data-testid="experiment-id">{experiment?.id || experimentId}</span>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <strong>Method:</strong> <span data-testid="experiment-method">{experiment?.method || 'not available'}</span>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <strong>Status:</strong>{' '}
        <span className={`badge badge-${status}`} data-testid="status-badge">
          {status}
        </span>{' '}
        {isPolling && <small style={{ color: '#64748b' }}>(Polling every {pollInterval / 1000}s...)</small>}
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
          <strong>Progress:</strong>
          <span data-testid="progress-value">
            {progress !== null && progress !== undefined ? `${progress}%` : 'not available'}
          </span>
        </div>
        <div className="progress-bar-container" data-testid="progress-container">
          <div
            className="progress-bar-fill"
            style={{ width: `${progress ?? 0}%` }}
            data-testid="progress-fill"
          >
            {progress !== null && progress !== undefined ? `${progress}%` : ''}
          </div>
        </div>
      </div>

      {/* Error message from runner if failed */}
      {experiment?.error && (
        <div className="alert alert-danger" data-testid="experiment-error">
          <strong>Failure Reason:</strong> {experiment.error}
        </div>
      )}

      {/* Metrics JSON */}
      <div style={{ marginTop: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Metrics</h3>
        <div data-testid="metrics-container">
          {metrics !== null && metrics !== undefined ? (
            <pre className="code-block" data-testid="metrics-json">
              {JSON.stringify(metrics, null, 2)}
            </pre>
          ) : (
            <p data-testid="metrics-not-available" style={{ color: '#64748b', fontStyle: 'italic' }}>
              not available
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
