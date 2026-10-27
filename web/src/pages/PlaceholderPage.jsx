import React from 'react';
import { supabase } from '../supabase.js';

export function PlaceholderPage({ title, featureName, isSettings = false }) {
  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch (_) {}
    window.location.href = '/login';
  };

  return (
    <div>
      <h1>{title}</h1>
      <section className="card" style={{ marginTop: '14px', textAlign: 'center', padding: '40px 20px' }}>
        <h2>{featureName || title}</h2>
        <p className="m" style={{ maxWidth: '480px', margin: '0 auto 20px', lineHeight: 1.6 }}>
          This feature is not available yet. It is planned for an upcoming milestone.
        </p>
        {isSettings && (
          <button type="button" className="btn" onClick={handleSignOut} style={{ background: '#c4521d' }}>
            Sign Out
          </button>
        )}
      </section>
    </div>
  );
}

export default PlaceholderPage;
