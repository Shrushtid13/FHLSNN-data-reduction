import React from 'react';

export function AccuracyReductionChart({ curve }) {
  if (!curve || !curve.series || curve.series.length === 0) {
    return (
      <section className="card" style={{ flex: '1 1 360px' }}>
        <h2>Accuracy vs reduction</h2>
        <p className="m" data-testid="curve-not-available">not available</p>
      </section>
    );
  }

  // Collect all points to calculate bounding box
  const allPoints = curve.series.flatMap((s) => s.points || []);
  if (allPoints.length === 0) {
    return (
      <section className="card" style={{ flex: '1 1 360px' }}>
        <h2>Accuracy vs reduction</h2>
        <p className="m" data-testid="curve-not-available">not available</p>
      </section>
    );
  }

  // Normalized bounds
  const xValues = allPoints.map((p) => (p.x > 1 ? p.x / 100 : p.x));
  const yValues = allPoints.map((p) => (p.y > 1 ? p.y / 100 : p.y));

  const minX = 0;
  const maxX = 1.0;
  const rawMinY = Math.min(...yValues);
  const rawMaxY = Math.max(...yValues);
  const minY = Math.max(0, Math.floor(rawMinY * 10) / 10 - 0.1);
  const maxY = Math.min(1.0, Math.ceil(rawMaxY * 10) / 10 + 0.05);

  const svgWidth = 380;
  const svgHeight = 220;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 40;

  const plotW = svgWidth - padLeft - padRight;
  const plotH = svgHeight - padTop - padBottom;

  const scaleX = (x) => {
    const val = x > 1 ? x / 100 : x;
    return padLeft + ((val - minX) / (maxX - minX || 1)) * plotW;
  };

  const scaleY = (y) => {
    const val = y > 1 ? y / 100 : y;
    return padTop + plotH - ((val - minY) / (maxY - minY || 1)) * plotH;
  };

  // Distinct colors and dash styles
  const defaultColors = ['#3a46dc', '#c4521d', '#0b7a5a', '#1b2145'];
  const defaultDashes = {
    solid: 'none',
    dashed: '6 4',
    dotted: '2 3',
  };

  // Compute 4 Y-ticks
  const yTicks = [minY, minY + (maxY - minY) * 0.5, maxY];
  // Compute 5 X-ticks
  const xTicks = [0, 0.25, 0.5, 0.75, 1.0];

  return (
    <section className="card" style={{ flex: '1 1 360px' }}>
      <h2>Accuracy vs reduction</h2>
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        role="img"
        aria-label="Accuracy vs reduction chart"
        style={{ width: '100%', height: 'auto', overflow: 'visible' }}
        data-testid="accuracy-reduction-svg"
      >
        {/* Grid lines */}
        {yTicks.map((tick, i) => (
          <line
            key={`y-grid-${i}`}
            x1={padLeft}
            y1={scaleY(tick)}
            x2={svgWidth - padRight}
            y2={scaleY(tick)}
            stroke="#eceffc"
            strokeDasharray="2 2"
          />
        ))}

        {/* Axes */}
        <line
          x1={padLeft}
          y1={padTop + plotH}
          x2={svgWidth - padRight}
          y2={padTop + plotH}
          stroke="#566091"
        />
        <line
          x1={padLeft}
          y1={padTop}
          x2={padLeft}
          y2={padTop + plotH}
          stroke="#566091"
        />

        {/* Y Axis Ticks & Labels */}
        {yTicks.map((tick, i) => (
          <g key={`y-tick-${i}`}>
            <line
              x1={padLeft - 4}
              y1={scaleY(tick)}
              x2={padLeft}
              y2={scaleY(tick)}
              stroke="#566091"
            />
            <text
              x={padLeft - 6}
              y={scaleY(tick) + 3}
              fontSize="10"
              fill="#566091"
              textAnchor="end"
            >
              {(tick * 100).toFixed(0)}%
            </text>
          </g>
        ))}

        {/* X Axis Ticks & Labels */}
        {xTicks.map((tick, i) => (
          <g key={`x-tick-${i}`}>
            <line
              x1={scaleX(tick)}
              y1={padTop + plotH}
              x2={scaleX(tick)}
              y2={padTop + plotH + 4}
              stroke="#566091"
            />
            <text
              x={scaleX(tick)}
              y={padTop + plotH + 16}
              fontSize="10"
              fill="#566091"
              textAnchor="middle"
            >
              {(tick * 100).toFixed(0)}%
            </text>
          </g>
        ))}

        {/* Axis titles */}
        <text
          x={padLeft + plotW / 2}
          y={svgHeight - 6}
          fontSize="11"
          fill="#566091"
          textAnchor="middle"
          fontWeight="600"
        >
          Reduction vs raw (%)
        </text>
        <text
          x={12}
          y={padTop + plotH / 2}
          fontSize="11"
          fill="#566091"
          transform={`rotate(-90 12 ${padTop + plotH / 2})`}
          textAnchor="middle"
          fontWeight="600"
        >
          Accuracy (%)
        </text>

        {/* Series Lines and Points */}
        {curve.series.map((s, idx) => {
          const color = defaultColors[idx % defaultColors.length];
          const dash = defaultDashes[s.style] || 'none';
          const points = s.points || [];
          const pointsStr = points
            .map((p) => `${scaleX(p.x)},${scaleY(p.y)}`)
            .join(' ');

          return (
            <g key={`series-${idx}`}>
              <polyline
                fill="none"
                stroke={color}
                strokeWidth="3"
                strokeDasharray={dash}
                points={pointsStr}
              />
              {points.map((p, pIdx) => (
                <circle
                  key={`pt-${idx}-${pIdx}`}
                  cx={scaleX(p.x)}
                  cy={scaleY(p.y)}
                  r="3.5"
                  fill={color}
                />
              ))}
            </g>
          );
        })}

        {/* Unreduced Baseline Dot (x = 0) */}
        {allPoints.length > 0 && (
          <circle
            cx={scaleX(0)}
            cy={scaleY(allPoints[0].y)}
            r="5"
            fill="#1b2145"
            data-testid="unreduced-dot"
          />
        )}
      </svg>

      {/* Caption matching Design Mockup 04 */}
      <div className="m" style={{ marginTop: '12px' }}>
        Solid blue: Hybrid (this run). Dashed orange: random subsampling. Black dot: unreduced.
      </div>
    </section>
  );
}
