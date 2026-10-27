import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { supabase } from './supabase.js';
import { AppLayout } from './components/AppLayout.jsx';
import { Login } from './pages/Login.jsx';
import { Datasets } from './pages/Datasets.jsx';
import { NewExperiment } from './pages/NewExperiment.jsx';
import { ExperimentsList } from './pages/ExperimentsList.jsx';
import { ExperimentDetail } from './pages/ExperimentDetail.jsx';
import { PlaceholderPage } from './pages/PlaceholderPage.jsx';

// DEV-only Sample Result route component
let SampleResultComponent = null;
if (import.meta.env.DEV) {
  const mod = await import('./pages/SampleResult.jsx');
  SampleResultComponent = mod.SampleResult;
}

function RequireAuth({ session, children }) {
  const location = useLocation();

  if (!session) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

export function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      setSession(currentSession);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: 'var(--page-bg)', fontFamily: 'var(--font-family)' }}>
        <p className="m" style={{ fontSize: '16px', fontWeight: 600 }}>Loading FHLSNN Reduce...</p>
      </div>
    );
  }

  const token = session?.access_token;

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch {}
    localStorage.clear();
    setSession(null);
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Public login route */}
        <Route
          path="/login"
          element={
            <Login
              session={session}
              onAuthSuccess={(sess) => setSession(sess)}
              onSignOut={handleSignOut}
            />
          }
        />

        {/* Root redirects to /datasets */}
        <Route path="/" element={<Navigate to="/datasets" replace />} />

        {/* Protected app shell routes */}
        <Route
          element={
            <RequireAuth session={session}>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route path="/datasets" element={<Datasets token={token} />} />
          <Route path="/experiments" element={<ExperimentsList token={token} />} />
          <Route path="/experiments/new" element={<NewExperiment token={token} />} />
          <Route path="/experiments/:id" element={<ExperimentDetail token={token} />} />
          <Route path="/benchmarks" element={<PlaceholderPage title="Benchmarks" featureName="Benchmark Suite" />} />
          <Route path="/recommendations" element={<PlaceholderPage title="AI Recommendations" featureName="Recommendation Agent" />} />
          <Route path="/settings" element={<PlaceholderPage title="Settings" featureName="Platform Settings" isSettings={true} />} />

          {/* DEV-only route */}
          {import.meta.env.DEV && SampleResultComponent && (
            <Route path="/dev/sample-result" element={<SampleResultComponent />} />
          )}
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/datasets" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
