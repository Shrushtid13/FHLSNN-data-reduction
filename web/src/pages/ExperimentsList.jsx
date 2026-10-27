import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../api.js';
import { StatusPill } from '../components/StatusPill.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { ErrorBanner } from '../components/ErrorBanner.jsx';

export function ExperimentsList({ token }) {
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState([]);
  const [datasetMap, setDatasetMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        setErrorMsg(null);

        const [expList, dsList] = await Promise.all([
          apiFetch('/experiments', token),
          apiFetch('/datasets', token).catch(() => []),
        ]);

        if (!isMounted) return;

        const dsMap = {};
        if (Array.isArray(dsList)) {
          dsList.forEach((d) => {
            dsMap[d.id] = d.name;
          });
        }
        setDatasetMap(dsMap);

        const sorted = Array.isArray(expList)
          ? [...expList].sort(
              (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
            )
          : [];
        setExperiments(sorted);
      } catch (err) {
        if (isMounted) {
          setErrorMsg('Failed to load experiments: ' + err.message);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    if (token) {
      loadData();
    }

    return () => {
      isMounted = false;
    };
  }, [token]);

  // Client-side filtering
  const filteredExperiments = experiments.filter((exp) => {
    const dsName = exp.dataset_name || datasetMap[exp.dataset_id] || '';
    const matchesSearch =
      searchTerm.trim() === '' ||
      exp.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dsName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      exp.method?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'All' || exp.status?.toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesStatus;
  });

  const formatDate = (isoStr) => {
    if (!isoStr) return 'not available';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return 'not available';
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoStr;
    }
  };

  const formatMethod = (method) => {
    if (!method) return 'not available';
    const map = {
      unreduced: 'Unreduced baseline',
      m1: 'M1 boundary filter',
      m3: 'M3 pruning',
      hybrid: 'Hybrid',
    };
    return map[method] || method;
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem 0', textAlign: 'center' }}>
        <p className="m" style={{ fontSize: '15px' }}>Loading experiments...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Header Row */}
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Experiments</h1>
        <button
          type="button"
          className="btn"
          onClick={() => navigate('/experiments/new')}
          data-testid="new-experiment-btn"
        >
          New experiment
        </button>
      </div>

      {errorMsg && <ErrorBanner message={errorMsg} onDismiss={() => setErrorMsg(null)} />}

      {/* Filter Card */}
      <section className="card" data-testid="experiments-filter-card">
        <div className="row" style={{ alignItems: 'flex-end', gap: '14px' }}>
          <label htmlFor="search-experiments-input">
            Search
            <input
              id="search-experiments-input"
              type="text"
              placeholder="Search by ID, dataset, method..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="search-experiments-input"
            />
          </label>

          <label htmlFor="status-filter-select">
            Status
            <select
              id="status-filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              data-testid="status-filter-select"
            >
              <option value="All">All statuses</option>
              <option value="queued">Queued</option>
              <option value="running">Running</option>
              <option value="done">Done</option>
              <option value="failed">Failed</option>
            </select>
          </label>
        </div>
      </section>

      {/* Experiments Table Card */}
      {experiments.length === 0 ? (
        <EmptyState
          title="No experiments found"
          message="Run your first reduction experiment to compare accuracy, segment counts, and vector savings."
          actionText="New experiment"
          onAction={() => navigate('/experiments/new')}
        />
      ) : filteredExperiments.length === 0 ? (
        <section className="card" style={{ textAlign: 'center', padding: '2.5rem' }}>
          <p className="m" style={{ fontSize: '15px' }}>
            No experiments match your filter criteria.
          </p>
        </section>
      ) : (
        <section className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table
              style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}
              data-testid="experiments-table"
            >
              <thead>
                <tr style={{ background: '#f8f9fe' }}>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    ID
                  </th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    Dataset
                  </th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    Method
                  </th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    Status
                  </th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    Progress
                  </th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    Created
                  </th>
                  <th style={{ textAlign: 'right', padding: '12px 16px', color: 'var(--text-muted)' }}>
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredExperiments.map((exp) => {
                  const dsName =
                    exp.dataset_name || datasetMap[exp.dataset_id] || 'Unknown';
                  const shortId = exp.id ? exp.id.slice(0, 8) : 'not available';
                  const progressVal =
                    exp.progress !== null && exp.progress !== undefined
                      ? `${exp.progress}%`
                      : exp.status === 'done'
                      ? '100%'
                      : '0%';

                  return (
                    <tr
                      key={exp.id}
                      style={{ cursor: 'pointer', transition: 'background 0.1s ease' }}
                      onClick={() => navigate(`/experiments/${exp.id}`)}
                      data-testid={`experiment-row-${exp.id}`}
                    >
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                          fontFamily: 'monospace',
                          fontWeight: 600,
                        }}
                        title={exp.id}
                      >
                        {shortId}
                      </td>
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                          fontWeight: 600,
                        }}
                      >
                        {dsName}
                      </td>
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                        }}
                      >
                        {formatMethod(exp.method)}
                      </td>
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                        }}
                      >
                        <StatusPill status={exp.status} />
                      </td>
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                        }}
                      >
                        {progressVal}
                      </td>
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {formatDate(exp.created_at)}
                      </td>
                      <td
                        style={{
                          padding: '14px 16px',
                          borderTop: '1px solid var(--border-subtle)',
                          textAlign: 'right',
                        }}
                      >
                        <button
                          type="button"
                          className="btn g"
                          style={{ padding: '6px 14px', fontSize: '13px' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/experiments/${exp.id}`);
                          }}
                          data-testid={`view-btn-${exp.id}`}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
