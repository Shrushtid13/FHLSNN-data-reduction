import React, { useState, useEffect } from 'react';
import { supabase } from './supabase.js';
import { Home } from './pages/Home.jsx';
import { Login } from './pages/Login.jsx';
import { Datasets } from './pages/Datasets.jsx';
import { NewExperiment } from './pages/NewExperiment.jsx';
import { ExperimentDetail } from './pages/ExperimentDetail.jsx';

export function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unauthPage, setUnauthPage] = useState('home'); // 'home' | 'login'
  const [authMode, setAuthMode] = useState('signin'); // 'signin' | 'signup'
  const [activePage, setActivePage] = useState('datasets'); // 'home' | 'datasets' | 'new_experiment' | 'experiment_detail'
  const [selectedExperimentId, setSelectedExperimentId] = useState(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setUnauthPage('home');
    setActivePage('datasets');
  };

  const navigateToExperiment = (expId) => {
    setSelectedExperimentId(expId);
    setActivePage('experiment_detail');
  };

  const navigateToNewExperimentWithDataset = (datasetId) => {
    setSelectedDatasetId(datasetId);
    setActivePage('new_experiment');
  };

  if (loading) {
    return (
      <div className="app-loading-screen">
        <div className="spinner"></div>
        <p>Loading FHLSNN Platform...</p>
      </div>
    );
  }

  // Unauthenticated State: Showcase Homepage or Login/Register Form
  if (!session) {
    if (unauthPage === 'home') {
      return (
        <Home
          onNavigateToAuth={(mode) => {
            setAuthMode(mode || 'signin');
            setUnauthPage('login');
          }}
        />
      );
    }

    return (
      <Login
        initialMode={authMode}
        onBack={() => setUnauthPage('home')}
        onAuthSuccess={(sess) => {
          setSession(sess);
          setActivePage('datasets');
        }}
      />
    );
  }

  const token = session.access_token;

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="nav-brand" onClick={() => setActivePage('datasets')} style={{ cursor: 'pointer' }}>
          <div className="brand-icon small">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
          </div>
          <span>FHLSNN Platform</span>
        </div>

        <div className="nav-links">
          <span className="user-email-pill">
            {session.user?.email}
          </span>
          <button
            className={`nav-btn ${activePage === 'home' ? 'active' : ''}`}
            onClick={() => setActivePage('home')}
          >
            Overview
          </button>
          <button
            className={`nav-btn ${activePage === 'datasets' ? 'active' : ''}`}
            onClick={() => setActivePage('datasets')}
          >
            Datasets
          </button>
          <button
            className={`nav-btn ${activePage === 'new_experiment' ? 'active' : ''}`}
            onClick={() => {
              setSelectedDatasetId(null);
              setActivePage('new_experiment');
            }}
          >
            New Experiment
          </button>
          <button className="nav-btn btn-signout" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main Authenticated Content */}
      {activePage === 'home' ? (
        <Home onNavigateToAuth={() => setActivePage('datasets')} />
      ) : (
        <main className="container">
          {activePage === 'datasets' && (
            <Datasets
              token={token}
              onSelectDatasetForExperiment={navigateToNewExperimentWithDataset}
            />
          )}

          {activePage === 'new_experiment' && (
            <NewExperiment
              token={token}
              initialDatasetId={selectedDatasetId}
              onExperimentCreated={navigateToExperiment}
            />
          )}

          {activePage === 'experiment_detail' && (
            <ExperimentDetail
              experimentId={selectedExperimentId}
              token={token}
              onBack={() => setActivePage('datasets')}
            />
          )}
        </main>
      )}
    </div>
  );
}

export default App;
