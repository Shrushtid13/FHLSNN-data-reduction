import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api.js';

const DEFAULT_PARAMS = {
  theta: 0.5,
  gamma: 1.0,
};

export function NewExperiment({ token, initialDatasetId, onExperimentCreated }) {
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(initialDatasetId || '');
  const [method, setMethod] = useState('hybrid');
  const [paramsJson, setParamsJson] = useState(JSON.stringify(DEFAULT_PARAMS, null, 2));
  const [seed, setSeed] = useState(42);
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    async function loadDatasets() {
      try {
        const data = await apiFetch('/datasets', token);
        setDatasets(data || []);
        if (!selectedDatasetId && data && data.length > 0) {
          setSelectedDatasetId(data[0].id);
        }
      } catch (err) {
        setErrorMsg('Failed to load datasets: ' + err.message);
      } finally {
        setLoadingDatasets(false);
      }
    }
    if (token) {
      loadDatasets();
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!selectedDatasetId) {
      setErrorMsg('Please select a dataset');
      return;
    }

    let parsedParams = {};
    try {
      parsedParams = paramsJson.trim() ? JSON.parse(paramsJson) : {};
    } catch (err) {
      setErrorMsg('Params must be valid JSON: ' + err.message);
      return;
    }

    setSubmitting(true);
    try {
      const experiment = await apiFetch('/experiments', token, {
        method: 'POST',
        body: {
          dataset_id: selectedDatasetId,
          method,
          params: parsedParams,
          seed: parseInt(seed, 10) || 42,
        },
      });

      if (onExperimentCreated) {
        onExperimentCreated(experiment.id);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to create experiment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '650px', margin: '2rem auto' }}>
      <h2>Configure New Experiment</h2>
      {errorMsg && <div className="alert alert-danger" role="alert">{errorMsg}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="exp-dataset-select">Dataset</label>
          {loadingDatasets ? (
            <p>Loading datasets...</p>
          ) : datasets.length === 0 ? (
            <p>No datasets available. Please upload a dataset first.</p>
          ) : (
            <select
              id="exp-dataset-select"
              className="form-control"
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              required
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.n_rows || 0} rows, {d.n_features || 0} features)
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="exp-method-select">Reduction Method</label>
          <select
            id="exp-method-select"
            className="form-control"
            value={method}
            onChange={(e) => setMethod(e.target.value)}
          >
            <option value="unreduced">Unreduced (Full Training Set)</option>
            <option value="m1">M1 (Pre-filtering / Boundary Selection)</option>
            <option value="m3">M3 (Post-pruning)</option>
            <option value="hybrid">Hybrid (M1 + M3 Combined)</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="exp-params-json">Parameters (JSON format)</label>
          <textarea
            id="exp-params-json"
            rows={5}
            className="form-control"
            value={paramsJson}
            onChange={(e) => setParamsJson(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="exp-seed-input">Random Seed</label>
          <input
            id="exp-seed-input"
            type="number"
            className="form-control"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="btn"
          disabled={submitting || datasets.length === 0}
        >
          {submitting ? 'Queuing Experiment...' : 'Launch Experiment'}
        </button>
      </form>
    </div>
  );
}
