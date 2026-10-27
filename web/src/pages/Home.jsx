import React from 'react';
import '../index.css';

export function Home({ onNavigateToAuth }) {
  return (
    <div className="home-container">
      {/* Top Navigation Bar */}
      <header className="home-navbar">
        <div className="home-brand">
          <div className="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
          </div>
          <span>FHLSNN Platform</span>
        </div>

        <nav className="home-nav-links">
          <a href="#overview">Overview</a>
          <a href="#features">Architecture</a>
          <a href="#workflow">Workflow</a>
          <a href="#security">Security</a>
        </nav>

        <div className="home-auth-actions">
          <button
            className="btn btn-home-secondary"
            onClick={() => onNavigateToAuth('signin')}
            data-testid="home-signin-btn"
          >
            Sign In
          </button>
          <button
            className="btn btn-home-primary"
            onClick={() => onNavigateToAuth('signup')}
            data-testid="home-register-btn"
          >
            Register
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="home-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-pulse"></span>
            Final Year Project • High-Dimensional Tabular Classification
          </div>
          <h1 className="hero-headline">
            Fast Hyperplane-based <br />
            <span className="gradient-text">Local Sparse Neural Networks</span>
          </h1>
          <p className="hero-lead">
            An interpretable and scalable machine learning platform for tabular datasets.
            Train, benchmark, and evaluate local hyperplane partition models with deterministic
            seeds and real-time execution telemetry.
          </p>
          <div className="hero-cta-group">
            <button
              className="btn btn-hero-primary"
              onClick={() => onNavigateToAuth('signin')}
            >
              Sign In to Platform
              <span className="btn-arrow">&rarr;</span>
            </button>
            <button
              className="btn btn-hero-secondary"
              onClick={() => onNavigateToAuth('signup')}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Hero Visual Card */}
        <div className="hero-visual">
          <div className="terminal-card">
            <div className="terminal-header">
              <span className="terminal-dot dot-red"></span>
              <span className="terminal-dot dot-yellow"></span>
              <span className="terminal-dot dot-green"></span>
              <span className="terminal-title">fhlsnn-pipeline.sh</span>
            </div>
            <pre className="terminal-body">
              <code>
                <span className="t-comment"># Ingest dataset & validate schema</span>{'\n'}
                <span className="t-cmd">$ api-post /datasets</span> file=churn_50k.csv{'\n'}
                <span className="t-success">[OK] 50,000 rows x 120 features (zero missing)</span>{'\n\n'}
                <span className="t-comment"># Queue experiment with Hybrid reducer</span>{'\n'}
                <span className="t-cmd">$ api-post /experiments</span> method=hybrid seed=42{'\n'}
                <span className="t-info">[QUEUED] job_id: 032b4347-81ec-4a7b-a25e</span>{'\n'}
                <span className="t-progress">Progress: [====================] 100%</span>{'\n'}
                <span className="t-success">[DONE] Status: done | Metrics: recorded</span>
              </code>
            </pre>
          </div>
        </div>
      </section>

      {/* Metrics Strip */}
      <section className="home-stats-strip">
        <div className="stat-item">
          <div className="stat-number">4</div>
          <div className="stat-label">Reducer Architectures (Unreduced, M1, M3, Hybrid)</div>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <div className="stat-number">50,000</div>
          <div className="stat-label">Max Tabular Rows Supported</div>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <div className="stat-number">100%</div>
          <div className="stat-label">Row Level Security (RLS) Isolation</div>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <div className="stat-number">&lt; 5s</div>
          <div className="stat-label">Redis Async Queue Turnaround</div>
        </div>
      </section>

      {/* Core Features Grid */}
      <section id="features" className="home-section">
        <div className="section-header">
          <span className="section-tag">CAPABILITIES</span>
          <h2>Engineered for Precision & Scalability</h2>
          <p>A dual-service architecture designed for fast iteration, safety, and reproducible ML research.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon icon-blue-1">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
              </svg>
            </div>
            <h3>Non-Blocking Tabular Parsing</h3>
            <p>
              Asynchronous stream parser processes up to 10 MB CSV files with automatic header mapping,
              formula injection sanitization, and strict numeric type validation.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-blue-2">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
              </svg>
            </div>
            <h3>Local Hyperplane Partitioning</h3>
            <p>
              Employs piecewise linear decision cells through sparse hyperplane learning, allowing efficient
              inference and parameter reduction without compromising classification accuracy.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-blue-3">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
              </svg>
            </div>
            <h3>Deterministic Benchmarking</h3>
            <p>
              All experiments are seeded and traced. Store hyperparameters, execution timestamps,
              and verifiable evaluation metrics directly linked to Supabase Postgres rows.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-blue-4">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
            </div>
            <h3>Multi-Tenant RLS Security</h3>
            <p>
              Strict Row Level Security policies isolate datasets and user experiments. Master administrative
              service keys remain isolated from client browsers at all times.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-blue-5">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </div>
            <h3>Live Telemetry & Polling</h3>
            <p>
              FastAPI and Redis background worker continuously report job progress. The UI polls seamlessly
              and updates status from queued to running to completed.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon icon-blue-6">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              </svg>
            </div>
            <h3>Explainability Agent Ready</h3>
            <p>
              Built-in architectural hooks for automated natural language explanations, vector similarity
              lookups via pgvector, and LLM-driven tuning recommendations.
            </p>
          </div>
        </div>
      </section>

      {/* Execution Workflow Section */}
      <section id="workflow" className="home-section workflow-section">
        <div className="section-header">
          <span className="section-tag">STEP-BY-STEP</span>
          <h2>Streamlined Research Workflow</h2>
          <p>From raw CSV data to reproducible local neural network evaluation in four steps.</p>
        </div>

        <div className="workflow-steps">
          <div className="workflow-card">
            <div className="step-badge">01</div>
            <h4>Upload Dataset</h4>
            <p>Upload your CSV file, select the target column, and let the system compute row, feature, and class distributions.</p>
          </div>
          <div className="workflow-arrow">&rarr;</div>
          <div className="workflow-card">
            <div className="step-badge">02</div>
            <h4>Configure Model</h4>
            <p>Select your reduction strategy (Unreduced, M1, M3, or Hybrid), adjust hyperparameters, and set your random seed.</p>
          </div>
          <div className="workflow-arrow">&rarr;</div>
          <div className="workflow-card">
            <div className="step-badge">03</div>
            <h4>Queue & Train</h4>
            <p>Jobs are pushed to the Redis queue and processed asynchronously by the background Python worker.</p>
          </div>
          <div className="workflow-arrow">&rarr;</div>
          <div className="workflow-card">
            <div className="step-badge">04</div>
            <h4>Evaluate Results</h4>
            <p>Inspect real-time execution progress, classification metrics, and verifiable benchmark outputs.</p>
          </div>
        </div>
      </section>

      {/* Call to Action Banner */}
      <section id="security" className="home-cta-banner">
        <div className="cta-inner">
          <h2>Ready to Explore FHLSNN?</h2>
          <p>
            Sign in with your researcher credentials or create a new account to begin training and benchmarking models.
          </p>
          <div className="cta-actions">
            <button
              className="btn btn-cta-primary"
              onClick={() => onNavigateToAuth('signin')}
            >
              Sign In to Your Workspace
            </button>
            <button
              className="btn btn-cta-secondary"
              onClick={() => onNavigateToAuth('signup')}
            >
              Register New Account
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <strong>FHLSNN Research Platform</strong> &copy; {new Date().getFullYear()}
          </div>
          <div className="footer-details">
            Final Year Engineering Project • Express 4 Gateway • FastAPI • Supabase PostgreSQL • Redis
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Home;
