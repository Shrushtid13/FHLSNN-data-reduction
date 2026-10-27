import React from 'react';
import sampleData from '../fixtures/sampleExperiment.json';
import { MetricCard } from '../components/MetricCard.jsx';
import { AccuracyReductionChart } from '../components/AccuracyReductionChart.jsx';
import { PcaScatter } from '../components/PcaScatter.jsx';
import { PerClassTable } from '../components/PerClassTable.jsx';
import { ExplanationCard } from '../components/ExplanationCard.jsx';
import { generateExperimentCsv, formatDelta } from './ExperimentDetail.jsx';

export function SampleResult() {
  if (!import.meta.env.DEV) {
    return (
      <div className="card">
        <h2>Not Found</h2>
        <p className="m">This development route is not available in production.</p>
      </div>
    );
  }

  const { metrics, facts, method } = sampleData;
  const ref = metrics.reference;
  const methodFormatted = method.charAt(0).toUpperCase() + method.slice(1).toLowerCase();

  const handleDownloadCsv = () => {
    const csvContent = generateExperimentCsv(sampleData);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `experiment_${sampleData.id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Permanent warning banner */}
      <div
        role="alert"
        style={{
          background: '#c4521d',
          color: '#ffffff',
          padding: '12px 18px',
          borderRadius: '10px',
          fontWeight: 800,
          textAlign: 'center',
          letterSpacing: '0.04em',
        }}
      >
        SAMPLE DATA, NOT A REAL RUN
      </div>

      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Results: {sampleData.dataset_name}, {methodFormatted}</h1>
        <div className="row" style={{ gap: '12px' }}>
          <button type="button" className="btn g" onClick={handleDownloadCsv}>
            Download CSV
          </button>
          <button type="button" className="btn" onClick={() => window.print()}>
            Export report
          </button>
        </div>
      </div>

      <p className="m" style={{ margin: 0 }}>
        Sample values for layout. The live screen shows stored run values only.
      </p>

      {/* 6 Metric Cards */}
      <div className="row" style={{ alignItems: 'stretch' }}>
        <MetricCard
          label="Accuracy"
          value={`${(metrics.accuracy * 100).toFixed(1)}%`}
          delta={formatDelta(metrics.accuracy, ref.accuracy)}
        />
        <MetricCard
          label="Macro-F1"
          value={`${(metrics.macro_f1 * 100).toFixed(1)}%`}
          delta={formatDelta(metrics.macro_f1, ref.macro_f1)}
        />
        <MetricCard
          label="Stored vectors"
          value={metrics.stored_vectors}
          subtext={`of ${metrics.n_fit} fit patterns`}
        />
        <MetricCard
          label="Reduction"
          value={`${(metrics.reduction_vs_raw * 100).toFixed(1)}%`}
          subtext="vs raw"
        />
        <MetricCard
          label="Segments"
          value={metrics.n_segments}
          subtext={`unreduced: ${ref.n_segments}`}
        />
        <MetricCard
          label="No-match patterns"
          value={`${(metrics.zero_mem_frac * 100).toFixed(1)}%`}
          subtext="all memberships zero"
        />
      </div>

      {/* Charts Row */}
      <div className="row" style={{ alignItems: 'stretch' }}>
        <AccuracyReductionChart curve={facts.curve} />
        <PcaScatter pca={facts.pca} />
      </div>

      {/* Table & Explanation Row */}
      <div className="row" style={{ alignItems: 'stretch' }}>
        <PerClassTable perClass={facts.per_class} />
        <ExplanationCard
          explanation={facts.explanation}
          seed={sampleData.seed}
          nFit={metrics.n_fit}
          nVal={metrics.n_val}
          nTest={metrics.n_test}
        />
      </div>
    </div>
  );
}

export default SampleResult;
