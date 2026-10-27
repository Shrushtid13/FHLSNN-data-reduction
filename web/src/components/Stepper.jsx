import React from 'react';

export function Stepper({ activeStep = 1 }) {
  const steps = [
    { step: 1, label: '1 Datasets' },
    { step: 2, label: '2 Configure' },
    { step: 3, label: '3 Processing' },
    { step: 4, label: '4 Results' },
  ];

  return (
    <div className="steps" role="navigation" aria-label="Experiment steps">
      {steps.map((item) => (
        <span
          key={item.step}
          className={activeStep === item.step ? 'on' : ''}
          data-testid={`step-${item.step}`}
          aria-current={activeStep === item.step ? 'step' : undefined}
        >
          {item.label}
        </span>
      ))}
    </div>
  );
}

export default Stepper;
