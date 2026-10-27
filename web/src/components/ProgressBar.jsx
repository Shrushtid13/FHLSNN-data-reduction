import React from 'react';

export function ProgressBar({ progress = 0, label = 'Overall progress', style = {} }) {
  const num = typeof progress === 'number' ? progress : parseInt(progress, 10) || 0;
  const clamped = Math.max(0, Math.min(100, num));

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      style={{
        height: '14px',
        background: '#e6e9ff',
        borderRadius: '99px',
        overflow: 'hidden',
        width: '100%',
        position: 'relative',
        ...style,
      }}
      data-testid="progress-bar"
    >
      <div
        data-testid="progress-bar-fill"
        style={{
          width: `${clamped}%`,
          height: '100%',
          background: '#3a46dc',
          borderRadius: '99px',
          transition: 'width 0.2s ease-in-out',
        }}
      />
    </div>
  );
}

export default ProgressBar;
