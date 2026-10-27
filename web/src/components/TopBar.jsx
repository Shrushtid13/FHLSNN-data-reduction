import React from 'react';
import { Stepper } from './Stepper.jsx';

export function TopBar({ breadcrumb = 'Datasets', activeStep = 1 }) {
  return (
    <div className="top">
      <span>
        Workspace / <b>{breadcrumb}</b>
      </span>
      <Stepper activeStep={activeStep} />
    </div>
  );
}

export default TopBar;
