import React from 'react';

export function PcaScatter({ pca }) {
  if (!pca || !pca.points || pca.points.length === 0) {
    return (
      <section className="card" style={{ flex: '1 1 360px' }}>
        <h2>Before and after (PCA, 2 components)</h2>
        <p className="m" data-testid="pca-not-available">not available</p>
      </section>
    );
  }

  const points = pca.points;
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const spanX = maxX - minX || 1;
  const spanY = maxY - minY || 1;

  // SVG dimensions
  const w = 200;
  const h = 160;
  const pad = 24;

  const mapX = (x) => pad + ((x - minX) / spanX) * (w - 2 * pad);
  const mapY = (y) => pad + (1 - (y - minY) / spanY) * (h - 2 * pad);

  // Distinct class labels and colors
  const labels = Array.from(new Set(points.map((p) => p.label || 'Default')));
  const palette = ['#3a46dc', '#c4521d', '#0b7a5a', '#8b5cf6', '#d97706'];
  const colorMap = {};
  labels.forEach((l, i) => {
    colorMap[l] = palette[i % palette.length];
  });

  return (
    <section className="card" style={{ flex: '1 1 360px' }}>
      <h2>Before and after (PCA, 2 components)</h2>
      <div className="row">
        {/* Panel 1: Original (all points full opacity) */}
        <svg
          viewBox={`0 0 ${w} ${h}`}
          role="img"
          aria-label="Original data projection"
          style={{ flex: '1 1 150px', width: '150px', height: 'auto' }}
          data-testid="pca-before-svg"
        >
          <rect width={w} height={h} rx="10" fill="#f4f6ff" />
          {points.map((p, idx) => (
            <circle
              key={`pca-all-${idx}`}
              cx={mapX(p.x)}
              cy={mapY(p.y)}
              r="6"
              fill={colorMap[p.label || 'Default']}
              opacity="1"
            />
          ))}
        </svg>

        {/* Panel 2: After reduction (removed points faded) */}
        <svg
          viewBox={`0 0 ${w} ${h}`}
          role="img"
          aria-label="After reduction projection"
          style={{ flex: '1 1 150px', width: '150px', height: 'auto' }}
          data-testid="pca-after-svg"
        >
          <rect width={w} height={h} rx="10" fill="#f4f6ff" />
          {points.map((p, idx) => (
            <circle
              key={`pca-after-${idx}`}
              cx={mapX(p.x)}
              cy={mapY(p.y)}
              r="6"
              fill={colorMap[p.label || 'Default']}
              opacity={p.kept ? '1' : '0.2'}
            />
          ))}
        </svg>
      </div>

      <div className="m" style={{ marginTop: '12px' }}>
        Blue, orange and teal are the three classes. Faded points were removed.
      </div>
    </section>
  );
}
