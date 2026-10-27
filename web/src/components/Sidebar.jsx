import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';

export function Sidebar() {
  const location = useLocation();
  const navItems = [
    { label: 'Datasets', to: '/datasets' },
    { label: 'New experiment', to: '/experiments/new' },
    { label: 'Experiments', to: '/experiments' },
    { label: 'Benchmarks', to: '/benchmarks' },
    { label: 'AI recommendations', to: '/recommendations' },
    { label: 'Settings', to: '/settings' },
  ];

  return (
    <nav className="side" aria-label="Main Navigation">
      <b>FHLSNN Reduce</b>
      {navItems.map((item) => {
        const isExperimentsMatch =
          item.to === '/experiments' &&
          location.pathname !== '/experiments/new' &&
          (location.pathname === '/experiments' ||
            location.pathname.startsWith('/experiments/') ||
            location.pathname === '/dev/sample-result');

        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive || isExperimentsMatch ? 'on' : '')}
            end={item.to === '/experiments'}
          >
            {item.label}
          </NavLink>
        );
      })}

      <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
        <button
          type="button"
          onClick={async () => {
            try {
              const { supabase } = await import('../supabase.js');
              await supabase.auth.signOut();
            } catch {}
            localStorage.clear();
            window.location.href = '/login';
          }}
          style={{
            width: '100%',
            padding: '10px 12px',
            background: 'rgba(255, 255, 255, 0.12)',
            border: 'none',
            borderRadius: '10px',
            color: '#ffffff',
            fontFamily: 'inherit',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
            textAlign: 'center',
            transition: 'background 0.15s ease',
          }}
          onMouseOver={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.22)')}
          onMouseOut={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)')}
          data-testid="sidebar-signout-btn"
        >
          Sign Out
        </button>
      </div>
    </nav>
  );
}

export default Sidebar;
