import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { apiFetch } from '../api.js';
import { computeClassBalance } from './Datasets.jsx';
import { ErrorBanner } from '../components/ErrorBanner.jsx';
import { EmptyState } from '../components/EmptyState.jsx';

export function NewExperiment({ token, initialDatasetId, onExperimentCreated }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const datasetQueryParam = searchParams.get('dataset');

  // Form states
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(
    initialDatasetId || datasetQueryParam || ''
  );
  const [method, setMethod] = useState('hybrid'); // 'unreduced' | 'm1' | 'm3' | 'hybrid'
  const [variant, setVariant] = useState('fhlsnn2001'); // 'fhlsnn2001' | 'mfhlsnn2014_midpoint'
  const [keepFraction, setKeepFraction] = useState(0.5);
  const [interiorKeepRate, setInteriorKeepRate] = useState(0.1);
  const [minWins, setMinWins] = useState(1);
  const [seed, setSeed] = useState(42);
  const [tuneHyperparams, setTuneHyperparams] = useState(true);

  // Status & Telemetry states
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // AI Recommendation states
  const [recommendation, setRecommendation] = useState(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [recommendationUnavailable, setRecommendationUnavailable] = useState(false);

  // Load available datasets
  useEffect(() => {
    let isMounted = true;
    async function loadDatasets() {
      try {
        setLoadingDatasets(true);
        setErrorMsg(null);
        const data = await apiFetch('/datasets', token);
        if (!isMounted) return;

        const list = data || [];
        setDatasets(list);

        const targetId = initialDatasetId || datasetQueryParam;
        if (targetId && list.some((d) => d.id === targetId)) {
          setSelectedDatasetId(targetId);
        } else if (list.length > 0 && !selectedDatasetId) {
          setSelectedDatasetId(list[0].id);
        }
      } catch (err) {
        if (isMounted) {
          setErrorMsg('Failed to load datasets: ' + err.message);
        }
      } finally {
        if (isMounted) {
          setLoadingDatasets(false);
        }
      }
    }

    if (token) {
      loadDatasets();
    }

    return () => {
      isMounted = false;
    };
  }, [token, initialDatasetId, datasetQueryParam]);

  // Request AI recommendation whenever selected dataset changes
  useEffect(() => {
    if (!selectedDatasetId || !token) {
      setRecommendation(null);
      setRecommendationUnavailable(false);
      return;
    }

    let isMounted = true;
    setRecommendationLoading(true);
    setRecommendationUnavailable(false);

    apiFetch('/recommend', token, {
      method: 'POST',
      body: { dataset_id: selectedDatasetId },
    })
      .then((data) => {
        if (isMounted) {
          setRecommendation(data);
          setRecommendationLoading(false);
          setRecommendationUnavailable(false);
        }
      })
      .catch(() => {
        // "on 501 or any error show 'Recommendation not available yet' and no button"
        if (isMounted) {
          setRecommendation(null);
          setRecommendationLoading(false);
          setRecommendationUnavailable(true);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [selectedDatasetId, token]);

  // Apply AI Recommendation
  const handleUseRecommendation = () => {
    if (!recommendation) return;

    if (recommendation.method) {
      setMethod(recommendation.method);
    }

    const p = recommendation.params || recommendation.parameters;
    if (p) {
      if (p.variant) setVariant(p.variant);
      if (p.keep_fraction !== undefined) setKeepFraction(Number(p.keep_fraction));
      if (p.interior_keep_rate !== undefined) setInteriorKeepRate(Number(p.interior_keep_rate));
      if (p.min_wins !== undefined) setMinWins(Number(p.min_wins));
      if (p.tune_hyperparams !== undefined) setTuneHyperparams(Boolean(p.tune_hyperparams));
      if (p.seed !== undefined) setSeed(Number(p.seed));
    }
  };

  // Selected dataset summary computation
  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);
  const getDatasetSummary = (d) => {
    if (!d) return 'No dataset selected.';
    const nRows =
      d.n_rows !== null && d.n_rows !== undefined ? `${d.n_rows} rows` : 'not available rows';
    const nFeatures =
      d.n_features !== null && d.n_features !== undefined
        ? `${d.n_features} features`
        : 'not available features';
    const nClasses =
      d.n_classes !== null && d.n_classes !== undefined
        ? `${d.n_classes} classes`
        : 'not available classes';

    const balanceInfo = computeClassBalance(d.class_counts);
    const balanceText =
      balanceInfo.label !== 'not available'
        ? balanceInfo.label.toLowerCase()
        : 'balance not available';
    const profileText = d.profile ? 'Profile computed on upload.' : 'Not profiled.';

    return `${nRows}, ${nFeatures}, ${nClasses}, ${balanceText}. ${profileText}`;
  };

  // Form submission with range and type validation
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!selectedDatasetId) {
      setErrorMsg('Please select a dataset');
      return;
    }

    // Range validation
    if (method === 'm1' || method === 'hybrid') {
      const kf = parseFloat(keepFraction);
      if (isNaN(kf) || kf < 0.2 || kf > 0.9) {
        setErrorMsg('Keep fraction must be a number between 0.2 and 0.9');
        return;
      }

      const ikr = parseFloat(interiorKeepRate);
      if (isNaN(ikr) || ikr < 0.0 || ikr > 1.0) {
        setErrorMsg('Interior keep rate must be a number between 0.0 and 1.0');
        return;
      }
    }

    if (method === 'm3' || method === 'hybrid') {
      const mw = Number(minWins);
      if (isNaN(mw) || !Number.isInteger(mw) || mw < 1) {
        setErrorMsg('Min wins must be an integer of at least 1');
        return;
      }
    }

    const s = Number(seed);
    if (isNaN(s) || !Number.isInteger(s) || s < 0) {
      setErrorMsg('Random seed must be a non-negative integer');
      return;
    }

    // Build payload according to UI Contract
    const params = {
      variant,
      tune_hyperparams: Boolean(tuneHyperparams),
    };

    if (method === 'm1' || method === 'hybrid') {
      params.keep_fraction = parseFloat(keepFraction);
      params.interior_keep_rate = parseFloat(interiorKeepRate);
    }

    if (method === 'm3' || method === 'hybrid') {
      params.min_wins = parseInt(minWins, 10);
    }

    const payload = {
      dataset_id: selectedDatasetId,
      method,
      params,
      seed: parseInt(seed, 10),
    };

    setSubmitting(true);
    try {
      const experiment = await apiFetch('/experiments', token, {
        method: 'POST',
        body: payload,
      });

      if (onExperimentCreated) {
        onExperimentCreated(experiment.id);
      }

      navigate(`/experiments/${experiment.id}`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to start experiment');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingDatasets) {
    return (
      <div style={{ padding: '2rem 0', textAlign: 'center' }}>
        <p className="m" style={{ fontSize: '15px' }}>Loading datasets...</p>
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <EmptyState
        title="No datasets available"
        message="Please upload a dataset before configuring an experiment."
        actionText="Go to Datasets"
        onAction={() => navigate('/datasets')}
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      <h1>Configure experiment</h1>

      {errorMsg && (
        <ErrorBanner message={errorMsg} onDismiss={() => setErrorMsg(null)} />
      )}

      <form noValidate onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {/* Dataset & AI Recommendation Row */}
        <div className="row" style={{ alignItems: 'stretch' }}>
          {/* Dataset Card */}
          <section className="card" style={{ flex: '1 1 320px' }}>
            <h2>Dataset</h2>
            <label htmlFor="exp-dataset-select">
              Selected dataset
              <select
                id="exp-dataset-select"
                value={selectedDatasetId}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                data-testid="dataset-select"
                required
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <p className="m" style={{ marginTop: '12px' }} data-testid="dataset-summary">
              {getDatasetSummary(selectedDataset)}
            </p>
          </section>

          {/* AI Recommendation Card */}
          <section
            className="card"
            style={{
              flex: '2 1 420px',
              background: 'var(--primary-soft)',
            }}
            data-testid="ai-recommendation-card"
          >
            <h2>AI recommendation</h2>
            {recommendationLoading ? (
              <p className="m">Checking recommendation...</p>
            ) : recommendation ? (
              <div>
                <p style={{ margin: '0 0 12px' }}>
                  <b>
                    {recommendation.method
                      ? `${recommendation.method.charAt(0).toUpperCase() + recommendation.method.slice(1)}: `
                      : ''}
                  </b>
                  {recommendation.rationale ||
                    recommendation.explanation ||
                    recommendation.message ||
                    'Optimal configuration suggested.'}
                </p>
                <button
                  type="button"
                  className="btn"
                  onClick={handleUseRecommendation}
                  data-testid="use-recommendation-btn"
                >
                  Use recommendation
                </button>
              </div>
            ) : (
              <p className="m" data-testid="recommendation-unavailable">
                Recommendation not available yet
              </p>
            )}
          </section>
        </div>

        {/* Method Radio Cards */}
        <section className="card">
          <h2>Method</h2>
          <div className="row">
            <label className={`opt ${method === 'unreduced' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="method"
                value="unreduced"
                checked={method === 'unreduced'}
                onChange={() => setMethod('unreduced')}
                data-testid="method-radio-unreduced"
              />
              <b>Unreduced baseline</b>
              <span className="m">Train FHLSNN on all patterns</span>
            </label>

            <label className={`opt ${method === 'm1' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="method"
                value="m1"
                checked={method === 'm1'}
                onChange={() => setMethod('m1')}
                data-testid="method-radio-m1"
              />
              <b>M1 boundary filter</b>
              <span className="m">Drop interior patterns per class</span>
            </label>

            <label className={`opt ${method === 'm3' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="method"
                value="m3"
                checked={method === 'm3'}
                onChange={() => setMethod('m3')}
                data-testid="method-radio-m3"
              />
              <b>M3 pruning</b>
              <span className="m">Prune segments with few validation wins</span>
            </label>

            <label className={`opt ${method === 'hybrid' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="method"
                value="hybrid"
                checked={method === 'hybrid'}
                onChange={() => setMethod('hybrid')}
                data-testid="method-radio-hybrid"
              />
              <b>Hybrid</b>
              <span className="m">M1, train, then M3</span>
            </label>
          </div>
        </section>

        {/* Parameters Section */}
        <section className="card">
          <h2>Parameters</h2>
          <div className="row">
            <label htmlFor="variant-select">
              Model variant
              <select
                id="variant-select"
                value={variant}
                onChange={(e) => setVariant(e.target.value)}
                data-testid="variant-select"
              >
                <option value="fhlsnn2001">FHLSNN 2001</option>
                <option value="mfhlsnn2014_midpoint">MFHLSNN 2014 (midpoint)</option>
              </select>
            </label>

            {(method === 'm1' || method === 'hybrid') && (
              <>
                <label htmlFor="keep-fraction-input">
                  Keep fraction (M1)
                  <input
                    id="keep-fraction-input"
                    type="number"
                    step="0.1"
                    min="0.2"
                    max="0.9"
                    value={keepFraction}
                    onChange={(e) => setKeepFraction(e.target.value)}
                    data-testid="keep-fraction-input"
                  />
                </label>
                <label htmlFor="interior-keep-rate-input">
                  Interior keep rate
                  <input
                    id="interior-keep-rate-input"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={interiorKeepRate}
                    onChange={(e) => setInteriorKeepRate(e.target.value)}
                    data-testid="interior-keep-rate-input"
                  />
                </label>
              </>
            )}

            {(method === 'm3' || method === 'hybrid') && (
              <label htmlFor="min-wins-input">
                Min wins (M3)
                <input
                  id="min-wins-input"
                  type="number"
                  min="1"
                  step="1"
                  value={minWins}
                  onChange={(e) => setMinWins(e.target.value)}
                  data-testid="min-wins-input"
                />
              </label>
            )}

            <label htmlFor="seed-input">
              Random seed
              <input
                id="seed-input"
                type="number"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                data-testid="seed-input"
              />
            </label>
          </div>

          <p className="m" style={{ marginTop: '14px' }}>
            <label
              htmlFor="tune-hyperparams-checkbox"
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
              }}
            >
              <input
                id="tune-hyperparams-checkbox"
                type="checkbox"
                checked={tuneHyperparams}
                onChange={(e) => setTuneHyperparams(e.target.checked)}
                data-testid="tune-checkbox"
              />
              Tune theta and gamma on the validation split (20% of the training data)
            </label>
          </p>
        </section>

        {/* Action Buttons */}
        <div className="row" style={{ justifyContent: 'flex-end', gap: '12px' }}>
          <button
            type="button"
            className="btn g"
            onClick={() => navigate('/datasets')}
            data-testid="back-btn"
          >
            Back
          </button>
          <button
            type="submit"
            className="btn"
            disabled={submitting || datasets.length === 0}
            data-testid="run-experiment-btn"
          >
            {submitting ? 'Starting experiment...' : 'Run experiment'}
          </button>
        </div>
      </form>
    </div>
  );
}
