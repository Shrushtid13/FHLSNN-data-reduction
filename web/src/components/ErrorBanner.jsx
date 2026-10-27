import React from 'react';

export function ErrorBanner({ message, error, onDismiss, style = {} }) {
  const text = message || (error instanceof Error ? error.message : error) || 'An unexpected error occurred.';

  if (!text) return null;

  return (
    <div
      role="alert"
      className="error-banner"
      style={{
        background: '#fee2e2',
        color: '#991b1b',
        border: '1px solid #fecaca',
        borderRadius: '10px',
        padding: '12px 16px',
        fontSize: '14px',
        fontWeight: 600,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '16px',
        ...style,
      }}
      data-testid="error-banner"
    >
      <span>{text}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#991b1b',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '16px',
          }}
          aria-label="Dismiss error"
        >
          &times;
        </button>
      )}
    </div>
  );
}

export default ErrorBanner;
