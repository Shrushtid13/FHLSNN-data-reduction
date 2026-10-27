import React from 'react';

export function MetricCard({ label, value, subtext, delta, style = {} }) {
  return (
    <section className="card metric-card" style={{ flex: '1 1 150px', ...style }}>
      <div className="m">{label}</div>
      <div className="k">{value !== null && value !== undefined ? value : 'not available'}</div>
      {delta ? (
        <div className="m">{delta}</div>
      ) : subtext ? (
        <div className="m">{subtext}</div>
      ) : null}
    </section>
  );
}

export default MetricCard;
