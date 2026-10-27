import React from 'react';

export function EmptyState({ title = 'No data available', message = 'There are no items to display at this time.', actionText, onAction, style = {} }) {
  return (
    <section className="card empty-state" style={{ textAlign: 'center', padding: '40px 20px', ...style }}>
      <h2 style={{ marginBottom: '8px' }}>{title}</h2>
      <p className="m" style={{ maxWidth: '420px', margin: '0 auto 16px', lineHeight: 1.6 }}>
        {message}
      </p>
      {actionText && onAction && (
        <button type="button" className="btn" onClick={onAction}>
          {actionText}
        </button>
      )}
    </section>
  );
}

export default EmptyState;
