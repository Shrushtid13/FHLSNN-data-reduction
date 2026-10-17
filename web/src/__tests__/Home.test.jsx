import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Home } from '../pages/Home.jsx';

describe('Home Component Tests', () => {
  it('renders headline, navigation, and features', () => {
    const handleNavigate = vi.fn();
    render(<Home onNavigateToAuth={handleNavigate} />);

    expect(screen.getByText('FHLSNN Platform')).toBeInTheDocument();
    expect(screen.getByText(/Local Sparse Neural Networks/i)).toBeInTheDocument();
    expect(screen.getByText('Non-Blocking Tabular Parsing')).toBeInTheDocument();
    expect(screen.getByText('Local Hyperplane Partitioning')).toBeInTheDocument();
  });

  it('navigates to sign in when clicking Sign In button', () => {
    const handleNavigate = vi.fn();
    render(<Home onNavigateToAuth={handleNavigate} />);

    const signInBtn = screen.getByTestId('home-signin-btn');
    fireEvent.click(signInBtn);

    expect(handleNavigate).toHaveBeenCalledWith('signin');
  });

  it('navigates to register when clicking Register button', () => {
    const handleNavigate = vi.fn();
    render(<Home onNavigateToAuth={handleNavigate} />);

    const registerBtn = screen.getByTestId('home-register-btn');
    fireEvent.click(registerBtn);

    expect(handleNavigate).toHaveBeenCalledWith('signup');
  });
});
