import React from 'react';

export function StatusPill({ status = 'queued', label, className = '', style = {} }) {
  const norm = String(status).toLowerCase();

  let variantClass = '';
  let defaultLabel = status;

  if (norm === 'done' || norm === 'profiled') {
    variantClass = 'pill-success';
  } else if (norm === 'running') {
    variantClass = 'pill-running';
  } else if (norm === 'failed' || norm === 'error') {
    variantClass = 'pill-failed';
  } else {
    // queued, waiting, not profiled, default
    variantClass = 'pill-waiting';
  }

  const displayText = label !== undefined ? label : defaultLabel;

  return (
    <span
      className={`pill ${variantClass} ${className}`.trim()}
      style={style}
      data-testid="status-pill"
      data-status={norm}
    >
      {displayText}
    </span>
  );
}

export default StatusPill;
