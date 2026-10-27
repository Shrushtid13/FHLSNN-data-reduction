import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../api.js';
import { StatusPill } from '../components/StatusPill.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { ErrorBanner } from '../components/ErrorBanner.jsx';

/**
 * Calculates class balance from class_counts:
 * ratio = max(counts) / min(counts)
 * - below 1.5: "Balanced"
 * - 1.5 to 3: "Mildly imbalanced"
 * - above 3: "Imbalanced"
 */
export function computeClassBalance(classCounts) {
  if (!classCounts || typeof classCounts !== 'object') {
    return { label: 'not available', ratio: null };
  }
  const counts = Object.values(classCounts).map(Number).filter((n) => !isNaN(n) && n > 0);
  if (counts.length === 0) {
    return { label: 'not available', ratio: null };
  }
  if (counts.length === 1) {
    return { label: 'Balanced', ratio: 1.0 };
  }
  const max = Math.max(...counts);
  const min = Math.min(...counts);
  if (min === 0) {
    return { label: 'Imbalanced', ratio: Infinity };
  }
  const ratio = max / min;
  let label = 'Balanced';
  if (ratio > 3) {
    label = 'Imbalanced';
  } else if (ratio >= 1.5) {
    label = 'Mildly imbalanced';
  }
  return { label, ratio };
}

export function Datasets({ token, onSelectDatasetForExperiment }) {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Client-side Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [sizeFilter, setSizeFilter] = useState('All'); // 'All' | 'under_1000' | 'over_10000'
  const [sourceFilter, setSourceFilter] = useState('All'); // 'All' | 'Benchmark' | 'My uploads'

  // Selected row checkboxes
  const [selectedIds, setSelectedIds] = useState([]);

  // Upload Modal State
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [name, setName] = useState('');
  const [headers, setHeaders] = useState([]);
  const [targetColumn, setTargetColumn] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const fetchDatasets = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await apiFetch('/datasets', token);
      setDatasets(data || []);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDatasets();
    }
  }, [token]);

  // Determine if any dataset contains the optional 'source' column
  const hasSourceColumn = datasets.some((d) => d && (d.source !== undefined && d.source !== null));

  // Client-side filtered list
  const filteredDatasets = datasets.filter((dataset) => {
    // Name filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      if (!dataset.name?.toLowerCase().includes(term)) {
        return false;
      }
    }

    // Size filter
    if (sizeFilter === 'under_1000') {
      if (dataset.n_rows == null || dataset.n_rows >= 1000) return false;
    } else if (sizeFilter === 'over_10000') {
      if (dataset.n_rows == null || dataset.n_rows <= 10000) return false;
    }

    // Source filter
    if (sourceFilter !== 'All') {
      const isBenchmark = dataset.source === 'benchmark';
      if (sourceFilter === 'Benchmark' && !isBenchmark) return false;
      if (sourceFilter === 'My uploads' && isBenchmark) return false;
    }

    return true;
  });

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === filteredDatasets.length && filteredDatasets.length > 0) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredDatasets.map((d) => d.id));
    }
  };

  const handleReduce = (datasetId) => {
    if (onSelectDatasetForExperiment) {
      onSelectDatasetForExperiment(datasetId);
    }
    navigate(`/experiments/new?dataset=${datasetId}`);
  };

  // Upload Form Handlers
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setUploadError(null);
    setFile(selectedFile);
    setHeaders([]);
    setTargetColumn('');

    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      setUploadError('Selected file must be a .csv file');
      return;
    }

    if (!name) {
      setName(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const text = evt.target.result;
        const firstLine = text.split(/\r\n|\n|\r/)[0];
        if (firstLine) {
          const cols = firstLine
            .split(',')
            .map((c) => c.replace(/^["']|["']$/g, '').trim())
            .filter(Boolean);
          setHeaders(cols);
          if (cols.length > 0) {
            const defaultTarget = cols.includes('target') ? 'target' : cols[cols.length - 1];
            setTargetColumn(defaultTarget);
          }
        }
      } catch (err) {
        setUploadError(`Could not parse CSV header: ${err.message}`);
      }
    };
    reader.readAsText(selectedFile.slice(0, 1024 * 32));
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadError('Please select a CSV file');
      return;
    }
    if (!targetColumn) {
      setUploadError('Please specify or pick a target column');
      return;
    }

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('target_column', targetColumn);

    try {
      await apiFetch('/datasets', token, {
        method: 'POST',
        body: formData,
      });

      // Reset form and close dialog
      setFile(null);
      setName('');
      setHeaders([]);
      setTargetColumn('');
      setIsUploadOpen(false);

      // Refresh datasets
      await fetchDatasets();
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      {/* Header with Title and Upload action */}
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: '16px' }}>
        <h1>Datasets</h1>
        <button
          type="button"
          className="btn"
          onClick={() => setIsUploadOpen(true)}
          data-testid="upload-dataset-btn"
        >
          Upload dataset
        </button>
      </div>

      {errorMsg && <ErrorBanner message={errorMsg} />}

      {/* Filter Card */}
      <section className="card" style={{ marginBottom: '18px' }}>
        <div className="row">
          <label>
            Search
            <input
              placeholder="Search by name"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="name-search-input"
            />
          </label>

          <label>
            Source
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              data-testid="source-filter-select"
            >
              <option value="All">All</option>
              <option value="Benchmark">Benchmark</option>
              <option value="My uploads">My uploads</option>
            </select>
          </label>

          <label>
            Size
            <select
              value={sizeFilter}
              onChange={(e) => setSizeFilter(e.target.value)}
              data-testid="size-filter-select"
            >
              <option value="All">All</option>
              <option value="under_1000">Under 1,000 rows</option>
              <option value="over_10000">Over 10,000 rows</option>
            </select>
          </label>

          <button
            type="button"
            className="btn"
            onClick={() => {}}
            data-testid="search-filter-btn"
          >
            Search
          </button>
        </div>
      </section>

      {/* Datasets Table Card */}
      <section className="card">
        <h2>Your datasets</h2>

        {loading ? (
          <p className="m">Loading datasets...</p>
        ) : filteredDatasets.length === 0 ? (
          <EmptyState
            title="No datasets found"
            message={
              datasets.length === 0
                ? "You haven't uploaded any datasets yet. Click 'Upload dataset' to get started."
                : 'No datasets match your search or filter criteria.'
            }
            actionText="Upload dataset"
            onAction={() => setIsUploadOpen(true)}
          />
        ) : (
          <>
            <div className="table-box">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: '40px' }}>
                      <input
                        type="checkbox"
                        checked={
                          filteredDatasets.length > 0 &&
                          selectedIds.length === filteredDatasets.length
                        }
                        onChange={toggleSelectAll}
                        aria-label="Select all datasets"
                      />
                    </th>
                    <th>Name</th>
                    <th>Rows</th>
                    <th>Features</th>
                    <th>Classes</th>
                    <th>Class balance</th>
                    {hasSourceColumn && <th>Source</th>}
                    <th>Status</th>
                    <th style={{ width: '90px' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDatasets.map((d) => {
                    const { label: balanceLabel, ratio } = computeClassBalance(d.class_counts);
                    const ratioTitle = ratio !== null ? `Ratio: ${ratio.toFixed(2)}` : undefined;
                    const isProfiled = d.profile !== null && d.profile !== undefined;

                    return (
                      <tr key={d.id} data-testid={`dataset-row-${d.id}`}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(d.id)}
                            onChange={() => toggleSelect(d.id)}
                            aria-label={`Select ${d.name}`}
                          />
                        </td>
                        <td>
                          <b>{d.name}</b>
                        </td>
                        <td>
                          {d.n_rows !== null && d.n_rows !== undefined
                            ? d.n_rows.toLocaleString()
                            : 'not available'}
                        </td>
                        <td>
                          {d.n_features !== null && d.n_features !== undefined
                            ? d.n_features
                            : 'not available'}
                        </td>
                        <td>
                          {d.n_classes !== null && d.n_classes !== undefined
                            ? d.n_classes
                            : 'not available'}
                        </td>
                        <td>
                          <span
                            title={ratioTitle}
                            style={{ cursor: ratioTitle ? 'help' : 'default' }}
                            data-testid={`balance-${d.id}`}
                          >
                            {balanceLabel}
                          </span>
                        </td>
                        {hasSourceColumn && (
                          <td>
                            {d.source === 'benchmark' ? 'Benchmark' : 'My uploads'}
                          </td>
                        )}
                        <td>
                          {isProfiled ? (
                            <StatusPill status="Profiled" label="Profiled" />
                          ) : (
                            <StatusPill status="queued" label="Not profiled" />
                          )}
                        </td>
                        <td>
                          <button
                            type="button"
                            className="btn g"
                            onClick={() => handleReduce(d.id)}
                            data-testid={`reduce-btn-${d.id}`}
                          >
                            Reduce
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="m" style={{ marginTop: '14px' }}>
              Showing {filteredDatasets.length} of {datasets.length} datasets
            </p>
          </>
        )}
      </section>

      {/* Upload Dataset Dialog / Modal */}
      {isUploadOpen && (
        <div
          className="modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="upload-dialog-title"
          onClick={(e) => {
            if (e.target === e.currentTarget) setIsUploadOpen(false);
          }}
        >
          <div className="modal-card">
            <h2 id="upload-dialog-title">Upload dataset</h2>

            {uploadError && <ErrorBanner message={uploadError} />}

            <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <label>
                CSV File (Max 10 MB, 20–50k rows)
                <input
                  id="csv-file-input"
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  required
                />
              </label>

              <label>
                Dataset Name
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Iris Flower"
                  required
                />
              </label>

              <label>
                Target Column (Classification Label)
                {headers.length > 0 ? (
                  <select
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    required
                  >
                    {headers.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    placeholder="Pick from header or type target column"
                    required
                  />
                )}
              </label>

              <div className="row" style={{ justifyContent: 'flex-end', marginTop: '10px' }}>
                <button
                  type="button"
                  className="btn g"
                  onClick={() => setIsUploadOpen(false)}
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button type="submit" className="btn" disabled={uploading}>
                  {uploading ? 'Validating & Uploading...' : 'Upload dataset'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Datasets;
