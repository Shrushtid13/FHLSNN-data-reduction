import React from 'react';

export function ExplanationCard({ explanation, seed, nFit, nVal, nTest }) {
  const text = explanation?.text || (typeof explanation === 'string' ? explanation : null);

  if (!text) {
    return (
      <section className="card" style={{ flex: '2 1 420px' }}>
        <h2>Explanation</h2>
        <p className="m" data-testid="explanation-not-available">not available</p>
      </section>
    );
  }

  const sVal = seed !== null && seed !== undefined ? seed : 'not available';
  const fitVal = nFit !== null && nFit !== undefined ? nFit : 'not available';
  const valVal = nVal !== null && nVal !== undefined ? nVal : 'not available';
  const testVal = nTest !== null && nTest !== undefined ? nTest : 'not available';

  const metadataLine = `Seed ${sVal}. Fit ${fitVal}, validation ${valVal}, test ${testVal}.`;

  return (
    <section className="card" style={{ flex: '2 1 420px' }}>
      <h2>Explanation</h2>
      <p style={{ margin: '0 0 10px', lineHeight: 1.6 }} data-testid="explanation-text">
        {text}
      </p>
      <div className="m" data-testid="explanation-metadata">
        {metadataLine}
      </div>
    </section>
  );
}
