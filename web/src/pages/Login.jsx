import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabase.js';

export function Login({ session, onAuthSuccess, onSignOut }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState('signin'); // 'signin' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [infoMsg, setInfoMsg] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setInfoMsg(null);

    try {
      if (mode === 'signin') {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        if (onAuthSuccess && data.session) {
          onAuthSuccess(data.session);
        }
        navigate('/datasets');
      } else {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        setInfoMsg('Registration successful! Please check your email for a confirmation link, or sign in.');
        if (data.session && onAuthSuccess) {
          onAuthSuccess(data.session);
          navigate('/datasets');
        }
      }
    } catch (err) {
      const msg = err.message || '';
      if (msg.toLowerCase().includes('failed to fetch')) {
        setErrorMsg(
          'Unable to reach remote Supabase authentication server (free project may be paused). Click "⚡ Dev Preview" below for instant local access.'
        );
      } else {
        setErrorMsg(msg || `Failed to ${mode === 'signin' ? 'sign in' : 'register'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // Instant local dev preview bypass
  const handleDevBypass = () => {
    const mockSession = {
      access_token: 'dev-preview-token-' + Date.now(),
      user: {
        id: 'dev-user-001',
        email: email || 'researcher@fhlsnn.edu',
        created_at: new Date().toISOString(),
      },
    };
    if (onAuthSuccess) {
      onAuthSuccess(mockSession);
    }
    navigate('/datasets');
  };

  return (
    <div className="app">
      {/* Cohesive Purple/Blurple Sidebar matching 01-datasets.html */}
      <nav className="side" aria-label="Main Navigation">
        <b>FHLSNN Reduce</b>
        <span
          className="on"
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            background: '#ffffff',
            color: '#3a46dc',
            fontWeight: 800,
            fontSize: '14px',
            display: 'block',
          }}
        >
          Authentication
        </span>
        <span
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            color: '#e3e6ff',
            fontSize: '14px',
            fontWeight: 600,
            opacity: 0.65,
            display: 'block',
          }}
        >
          Datasets
        </span>
        <span
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            color: '#e3e6ff',
            fontSize: '14px',
            fontWeight: 600,
            opacity: 0.65,
            display: 'block',
          }}
        >
          New experiment
        </span>
        <span
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            color: '#e3e6ff',
            fontSize: '14px',
            fontWeight: 600,
            opacity: 0.65,
            display: 'block',
          }}
        >
          Experiments
        </span>
        <span
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            color: '#e3e6ff',
            fontSize: '14px',
            fontWeight: 600,
            opacity: 0.65,
            display: 'block',
          }}
        >
          Benchmarks
        </span>
        <span
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            color: '#e3e6ff',
            fontSize: '14px',
            fontWeight: 600,
            opacity: 0.65,
            display: 'block',
          }}
        >
          AI recommendations
        </span>
        <span
          style={{
            padding: '11px 12px',
            borderRadius: '10px',
            color: '#e3e6ff',
            fontSize: '14px',
            fontWeight: 600,
            opacity: 0.65,
            display: 'block',
          }}
        >
          Settings
        </span>

        <div style={{ marginTop: 'auto', padding: '12px 10px', color: '#e3e6ff', fontSize: '12px', opacity: 0.85, lineHeight: 1.5 }}>
          <div><b>FHLSNN Core</b></div>
          <div style={{ fontSize: '11px', marginTop: '2px' }}>Fast Hyperplane-based Local Sparse Neural Networks</div>
          <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4ade80', display: 'inline-block' }}></span>
            <span>Platform Online</span>
          </div>
        </div>
      </nav>

      {/* Main Area */}
      <main className="main">
        {/* TopBar matching design mockups */}
        <div className="top">
          <span>
            Workspace / <b>Authentication & Access</b>
          </span>
          <div className="steps">
            <span
              className={mode === 'signin' ? 'on' : ''}
              style={{ cursor: 'pointer' }}
              onClick={() => setMode('signin')}
            >
              1 Sign In
            </span>
            <span
              className={mode === 'signup' ? 'on' : ''}
              style={{ cursor: 'pointer' }}
              onClick={() => setMode('signup')}
            >
              2 Register
            </span>
            <span>3 Workspace</span>
            <span>4 Benchmarks</span>
          </div>
        </div>

        {/* Header Row */}
        <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>FHLSNN Research Portal</h1>
            <p className="m" style={{ marginTop: '4px' }}>
              Sign in to run boundary filtering (M1), pruning (M3), and local hyperplane training.
            </p>
          </div>
          <div className="row" style={{ gap: '10px', alignItems: 'center' }}>
            <span className="pill">v1.0 Production Ready</span>
            {session && (
              <button
                type="button"
                className="btn g"
                onClick={onSignOut}
                title="Clear current session"
              >
                Sign Out ({session.user?.email || 'Researcher'})
              </button>
            )}
          </div>
        </div>

        {/* Existing Session Notification if logged in */}
        {session && (
          <section className="card" style={{ background: '#e6e9ff', border: '1px solid #c8d1fc' }}>
            <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <b>Active Session Detected</b>
                <p className="m" style={{ color: '#2b36b8', marginTop: '2px' }}>
                  Currently signed in as <b>{session.user?.email || 'Active Researcher'}</b>.
                </p>
              </div>
              <div className="row" style={{ gap: '10px' }}>
                <button type="button" className="btn" onClick={() => navigate('/datasets')}>
                  Go to Datasets &rarr;
                </button>
                {onSignOut && (
                  <button type="button" className="btn g" onClick={onSignOut}>
                    Sign Out & Switch Account
                  </button>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Dual-Column Section matching 02-configure.html */}
        <div className="row" style={{ alignItems: 'stretch' }}>
          {/* Left Column: Auth Form Card */}
          <section className="card" style={{ flex: '1 1 340px' }}>
            <h2>{mode === 'signin' ? 'Researcher Sign In' : 'Create Researcher Account'}</h2>

            {/* Mode Switcher Tabs */}
            <div className="row" style={{ gap: '8px', marginBottom: '18px' }}>
              <button
                type="button"
                className={`btn ${mode === 'signin' ? '' : 'g'}`}
                style={{ flex: 1, padding: '9px 12px', fontSize: '13px' }}
                onClick={() => {
                  setMode('signin');
                  setErrorMsg(null);
                  setInfoMsg(null);
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`btn ${mode === 'signup' ? '' : 'g'}`}
                style={{ flex: 1, padding: '9px 12px', fontSize: '13px' }}
                onClick={() => {
                  setMode('signup');
                  setErrorMsg(null);
                  setInfoMsg(null);
                }}
              >
                Register
              </button>
            </div>

            {errorMsg && (
              <div
                role="alert"
                style={{
                  background: '#fee2e2',
                  color: '#991b1b',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  fontSize: '13px',
                  fontWeight: 600,
                  marginBottom: '16px',
                  lineHeight: 1.5,
                }}
              >
                ⚠️ {errorMsg}
              </div>
            )}

            {infoMsg && (
              <div
                style={{
                  background: '#dff5e7',
                  color: '#13683a',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  fontSize: '13px',
                  fontWeight: 600,
                  marginBottom: '16px',
                }}
              >
                ✓ {infoMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <label>
                Email address
                <input
                  id="login-email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="researcher@university.edu"
                  required
                  autoComplete="email"
                />
              </label>

              <label>
                Password
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <input
                    id="login-password-input"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                    style={{ width: '100%', paddingRight: '52px' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: '12px',
                      background: 'transparent',
                      border: 'none',
                      color: '#566091',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </label>

              <button
                type="submit"
                className="btn"
                disabled={loading}
                data-testid="auth-submit-btn"
                style={{ width: '100%', marginTop: '6px' }}
              >
                {loading
                  ? 'Connecting...'
                  : mode === 'signin'
                  ? 'Sign in to platform'
                  : 'Create account'}
              </button>
            </form>

            {/* Quick Access Dev Section */}
            <div
              style={{
                marginTop: '20px',
                paddingTop: '16px',
                borderTop: '1px solid #eceffc',
              }}
            >
              <div className="m" style={{ fontWeight: 700, marginBottom: '10px', color: '#1b2145' }}>
                Instant Access:
              </div>
              <div className="row" style={{ gap: '10px' }}>
                <button
                  type="button"
                  className="btn g"
                  style={{ flex: 1 }}
                  onClick={handleDevBypass}
                  data-testid="dev-mock-login-btn"
                >
                  ⚡ Dev Preview (Instant)
                </button>
                <button
                  type="button"
                  className="btn g"
                  style={{ flex: 1 }}
                  onClick={() => navigate('/dev/sample-result')}
                >
                  📊 View Sample Results
                </button>
              </div>
              <p className="m" style={{ fontSize: '11px', marginTop: '8px' }}>
                Bypasses cloud auth timeouts for rapid evaluation and local demonstration.
              </p>
            </div>
          </section>

          {/* Right Column: Platform Showcase Card (Soft Blurple matching 02-configure.html) */}
          <section className="card" style={{ flex: '1.2 1 420px', background: '#e6e9ff' }}>
            <h2 style={{ color: '#1b2145' }}>FHLSNN Pattern Reduction Engine</h2>
            <p style={{ margin: '0 0 16px', lineHeight: 1.6, color: '#2b36b8', fontSize: '14px' }}>
              <b>High-Dimensional Tabular Sparsification:</b> Combines boundary pattern filtering (M1) and segment pruning (M3) with local hyperplane neural classification.
            </p>

            {/* Visual Hyperplane SVG Diagram */}
            <div
              style={{
                background: '#ffffff',
                borderRadius: '12px',
                padding: '14px',
                marginBottom: '16px',
                border: '1px solid #d5daf5',
              }}
            >
              <div className="m" style={{ fontWeight: 700, marginBottom: '8px', color: '#1b2145' }}>
                Local Hyperplane Partitioning (2D Projection)
              </div>
              <svg viewBox="0 0 360 140" style={{ width: '100%', height: 'auto' }} role="img" aria-label="Hyperplane partition preview">
                {/* Background grid */}
                <rect width="360" height="140" rx="8" fill="#f8fafc" />
                <line x1="20" y1="120" x2="340" y2="120" stroke="#d5daf5" strokeWidth="1" />
                <line x1="20" y1="20" x2="20" y2="120" stroke="#d5daf5" strokeWidth="1" />
                
                {/* Decision Hyperplane Boundaries */}
                <line x1="80" y1="20" x2="160" y2="120" stroke="#3a46dc" strokeWidth="2" strokeDasharray="4 3" />
                <line x1="200" y1="20" x2="280" y2="120" stroke="#3a46dc" strokeWidth="2" strokeDasharray="4 3" />
                
                {/* Class 1 (Royal Blurple) - Kept vs Pruned */}
                <circle cx="50" cy="40" r="5" fill="#3a46dc" />
                <circle cx="65" cy="65" r="5" fill="#3a46dc" />
                <circle cx="85" cy="90" r="5" fill="#3a46dc" />
                <circle cx="40" cy="80" r="4" fill="#3a46dc" opacity="0.25" />
                
                {/* Class 2 (Rust Orange) - Kept vs Pruned */}
                <circle cx="140" cy="45" r="5" fill="#c4521d" />
                <circle cx="165" cy="70" r="5" fill="#c4521d" />
                <circle cx="190" cy="95" r="5" fill="#c4521d" />
                <circle cx="160" cy="40" r="4" fill="#c4521d" opacity="0.25" />
                
                {/* Class 3 (Teal Green) - Kept vs Pruned */}
                <circle cx="250" cy="40" r="5" fill="#0b7a5a" />
                <circle cx="275" cy="65" r="5" fill="#0b7a5a" />
                <circle cx="300" cy="85" r="5" fill="#0b7a5a" />
                <circle cx="310" cy="45" r="4" fill="#0b7a5a" opacity="0.25" />

                {/* Legend */}
                <text x="30" y="133" fontSize="10" fill="#566091">Solid points: Retained boundary prototypes</text>
                <text x="230" y="133" fontSize="10" fill="#566091">Faded: Pruned interior patterns</text>
              </svg>
            </div>

            {/* Architecture Highlights */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ background: '#ffffff', borderRadius: '10px', padding: '10px 12px', border: '1px solid #d5daf5' }}>
                <b style={{ fontSize: '13px', color: '#3a46dc' }}>M1 Boundary Filter</b>
                <p className="m" style={{ fontSize: '12px', margin: '4px 0 0' }}>
                  Filters interior patterns to concentrate prototypes along class margins.
                </p>
              </div>
              <div style={{ background: '#ffffff', borderRadius: '10px', padding: '10px 12px', border: '1px solid #d5daf5' }}>
                <b style={{ fontSize: '13px', color: '#3a46dc' }}>M3 Validation Pruning</b>
                <p className="m" style={{ fontSize: '12px', margin: '4px 0 0' }}>
                  Removes redundant segments that contribute minimal validation wins.
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Bottom Section: Standard Benchmark Dataset Cards (matching 04-results.html KPI cards) */}
        <div className="row" style={{ alignItems: 'stretch' }}>
          <section className="card" style={{ flex: '1 1 150px' }}>
            <div className="m">Iris Benchmark</div>
            <div className="k">50.0%</div>
            <div className="m">+0.1 pp vs unreduced</div>
          </section>
          <section className="card" style={{ flex: '1 1 150px' }}>
            <div className="m">Wine Benchmark</div>
            <div className="k">46.2%</div>
            <div className="m">97.2% test accuracy</div>
          </section>
          <section className="card" style={{ flex: '1 1 150px' }}>
            <div className="m">Breast Cancer</div>
            <div className="k">53.8%</div>
            <div className="m">30 features reduced</div>
          </section>
          <section className="card" style={{ flex: '1 1 150px' }}>
            <div className="m">Pendigits</div>
            <div className="k">48.5%</div>
            <div className="m">10,992 patterns</div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Login;
