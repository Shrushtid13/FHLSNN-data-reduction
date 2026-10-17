import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api.js';

export function Datasets({ token, onSelectDatasetForExperiment }) {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Upload Form State
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

  // Extract CSV header when file is selected
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

    // Auto-fill dataset name from filename (without .csv)
    if (!name) {
      setName(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }

    // Read first slice of file to extract header line
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
            // Default target column to the last column or 'target'
            const defaultTarget = cols.includes('target') ? 'target' : cols[cols.length - 1];
            setTargetColumn(defaultTarget);
          }
        }
      } catch (err) {
        setUploadError(`Could not parse CSV header: ${err.message}`);
      }
    };
    reader.readAsText(selectedFile.slice(0, 1024 * 32)); // read first 32KB
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

      // Reset form
      setFile(null);
      setName('');
      setHeaders([]);
      setTargetColumn('');
      // Reset input element
      const fileInput = document.getElementById('csv-file-input');
      if (fileInput) fileInput.value = '';

      // Refresh datasets list
      await fetchDatasets();
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      {/* Upload Form Card */}
      <div className="card">
        <h2>Upload New Dataset</h2>
        {uploadError && <div className="alert alert-danger" role="alert">{uploadError}</div>}

        <form onSubmit={handleUploadSubmit}>
          <div className="form-group">
            <label htmlFor="csv-file-input">CSV File (Max 10 MB, 20-50k rows)</label>
            <input
              id="csv-file-input"
              type="file"
              accept=".csv"
              className="form-control"
              onChange={handleFileChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="dataset-name">Dataset Name</label>
            <input
              id="dataset-name"
              type="text"
              className="form-control"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Iris Flower Dataset"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="target-column">Target Column (Classification Label)</label>
            {headers.length > 0 ? (
              <select
                id="target-column"
                className="form-control"
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
                id="target-column"
                type="text"
                className="form-control"
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                placeholder="Upload a CSV to pick from header, or enter column name"
                required
              />
            )}
          </div>

          <button type="submit" className="btn" disabled={uploading}>
            {uploading ? 'Validating & Uploading...' : 'Upload Dataset'}
          </button>
        </form>
      </div>

      {/* Datasets List Card */}
      <div className="card">
        <h2>Your Datasets</h2>
        {errorMsg && <div className="alert alert-danger" role="alert">{errorMsg}</div>}
        {loading ? (
          <p>Loading datasets...</p>
        ) : datasets.length === 0 ? (
          <p>No datasets uploaded yet. Upload your first dataset using the form above.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Target Column</th>
                <th>Rows (n_rows)</th>
                <th>Features (n_features)</th>
                <th>Classes (n_classes)</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.id}>
                  <td><strong>{d.name}</strong></td>
                  <td>{d.target_column || 'not available'}</td>
                  <td>{d.n_rows !== null && d.n_rows !== undefined ? d.n_rows : 'not available'}</td>
                  <td>{d.n_features !== null && d.n_features !== undefined ? d.n_features : 'not available'}</td>
                  <td>{d.n_classes !== null && d.n_classes !== undefined ? d.n_classes : 'not available'}</td>
                  <td>
                    {onSelectDatasetForExperiment && (
                      <button
                        className="btn"
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                        onClick={() => onSelectDatasetForExperiment(d.id)}
                      >
                        New Experiment
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
