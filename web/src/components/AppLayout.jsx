import React, { createContext, useContext, useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar.jsx';
import { TopBar } from './TopBar.jsx';

export const LayoutContext = createContext({
  activeStep: 1,
  setActiveStep: () => {},
  breadcrumb: 'Datasets',
  setBreadcrumb: () => {},
});

export function useLayout() {
  return useContext(LayoutContext);
}

export function AppLayout({ children, activeStepProp, breadcrumbProp }) {
  const location = useLocation();

  // Derive default activeStep and breadcrumb from route if not provided via props
  const getRouteDefaults = (path) => {
    if (path.startsWith('/datasets')) {
      return { step: 1, crumb: 'Datasets' };
    }
    if (path.startsWith('/experiments/new')) {
      return { step: 2, crumb: 'New experiment' };
    }
    if (path.startsWith('/experiments')) {
      return { step: 3, crumb: 'Experiments' };
    }
    if (path.startsWith('/benchmarks')) {
      return { step: 1, crumb: 'Benchmarks' };
    }
    if (path.startsWith('/recommendations')) {
      return { step: 2, crumb: 'AI recommendations' };
    }
    if (path.startsWith('/settings')) {
      return { step: 1, crumb: 'Settings' };
    }
    if (path.startsWith('/dev/sample-result')) {
      return { step: 4, crumb: 'Experiments' };
    }
    return { step: 1, crumb: 'Workspace' };
  };

  const defaults = getRouteDefaults(location.pathname);
  const [activeStep, setActiveStep] = useState(activeStepProp || defaults.step);
  const [breadcrumb, setBreadcrumb] = useState(breadcrumbProp || defaults.crumb);

  useEffect(() => {
    const nextDefaults = getRouteDefaults(location.pathname);
    setActiveStep(nextDefaults.step);
    setBreadcrumb(nextDefaults.crumb);
  }, [location.pathname]);

  // Synchronize when route changes if not overridden by page
  const currentStep = activeStepProp !== undefined ? activeStepProp : activeStep;
  const currentBreadcrumb = breadcrumbProp !== undefined ? breadcrumbProp : breadcrumb;

  return (
    <LayoutContext.Provider value={{ activeStep: currentStep, setActiveStep, breadcrumb: currentBreadcrumb, setBreadcrumb }}>
      <div className="app">
        <Sidebar />
        <main className="main">
          <TopBar breadcrumb={currentBreadcrumb} activeStep={currentStep} />
          {children || <Outlet />}
        </main>
      </div>
    </LayoutContext.Provider>
  );
}

export default AppLayout;
