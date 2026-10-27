import React from 'react';

export function PerClassTable({ perClass }) {
  if (!perClass || !Array.isArray(perClass) || perClass.length === 0) {
    return (
      <section className="card" style={{ flex: '1 1 300px' }}>
        <h2>Patterns kept per class</h2>
        <p className="m" data-testid="per-class-not-available">not available</p>
      </section>
    );
  }

  return (
    <section className="card" style={{ flex: '1 1 300px' }}>
      <h2>Patterns kept per class</h2>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }} data-testid="per-class-table">
          <thead>
            <tr>
              <th style={{ textAlign: 'left', color: 'var(--text-muted)', padding: '10px 8px' }}>Class</th>
              <th style={{ textAlign: 'left', color: 'var(--text-muted)', padding: '10px 8px' }}>Before</th>
              <th style={{ textAlign: 'left', color: 'var(--text-muted)', padding: '10px 8px' }}>Kept</th>
              <th style={{ textAlign: 'left', color: 'var(--text-muted)', padding: '10px 8px' }}>Share kept</th>
            </tr>
          </thead>
          <tbody>
            {perClass.map((row, idx) => {
              const before = Number(row.before) || 0;
              const kept = Number(row.kept) || 0;
              const shareKept = before > 0 ? `${((kept / before) * 100).toFixed(0)}%` : '0%';

              return (
                <tr key={row.label || idx}>
                  <td style={{ padding: '13px 8px', borderTop: '1px solid var(--border-subtle)', fontWeight: 600 }}>
                    {row.label ?? 'not available'}
                  </td>
                  <td style={{ padding: '13px 8px', borderTop: '1px solid var(--border-subtle)' }}>
                    {row.before ?? 'not available'}
                  </td>
                  <td style={{ padding: '13px 8px', borderTop: '1px solid var(--border-subtle)' }}>
                    {row.kept ?? 'not available'}
                  </td>
                  <td style={{ padding: '13px 8px', borderTop: '1px solid var(--border-subtle)' }}>
                    {shareKept}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
