import React, { useState } from 'react';
import { supabase } from '../supabase.js';

export function Login({ onAuthSuccess, onBack, initialMode = 'signin' }) {
  const [mode, setMode] = useState(initialMode); // 'signin' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
      } else {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        setInfoMsg('Registration successful! Please check your email or sign in.');
        if (data.session && onAuthSuccess) {
          onAuthSuccess(data.session);
        }
      }
    } catch (err) {
      setErrorMsg(err.message || `Failed to ${mode === 'signin' ? 'sign in' : 'register'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        {onBack && (
          <button
            type="button"
            className="back-home-btn"
            onClick={onBack}
            data-testid="back-to-home-btn"
          >
            &larr; Back to Home
          </button>
        )}

        <div className="login-header">
          <div className="login-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
              <polyline points="10 17 15 12 10 7"></polyline>
              <line x1="15" y1="12" x2="3" y2="12"></line>
            </svg>
          </div>
          <h2>{mode === 'signin' ? 'Sign In to FHLSNN' : 'Create an Account'}</h2>
          <p className="login-subtitle">
            {mode === 'signin'
              ? 'Enter your credentials to access your datasets & experiments'
              : 'Register your email to start training local sparse neural networks'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tab-switch">
          <button
            type="button"
            className={`auth-tab ${mode === 'signin' ? 'active' : ''}`}
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
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => {
              setMode('signup');
              setErrorMsg(null);
              setInfoMsg(null);
            }}
          >
            Register
          </button>
        </div>

        {errorMsg && <div className="alert alert-danger" role="alert">{errorMsg}</div>}
        {infoMsg && <div className="alert alert-success">{infoMsg}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="researcher@university.edu"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
            />
          </div>

          <button
            type="submit"
            className="btn btn-auth-submit"
            disabled={loading}
          >
            {loading ? 'Processing...' : mode === 'signin' ? 'Sign In' : 'Register Account'}
          </button>
        </form>

        <div className="auth-footer-toggle">
          {mode === 'signin' ? (
            <p>
              Don't have an account yet?{' '}
              <button
                type="button"
                className="btn-link"
                onClick={() => {
                  setMode('signup');
                  setErrorMsg(null);
                  setInfoMsg(null);
                }}
              >
                Register now
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                className="btn-link"
                onClick={() => {
                  setMode('signin');
                  setErrorMsg(null);
                  setInfoMsg(null);
                }}
              >
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Login;
