import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import App, { SCREENS } from './App';

describe('SkillSaathi Screen Manager & Consent Flow', () => {
  const originalMediaDevices = navigator.mediaDevices;

  afterEach(() => {
    // Restore original navigator.mediaDevices
    Object.defineProperty(navigator, 'mediaDevices', {
      value: originalMediaDevices,
      configurable: true,
      writable: true,
    });
  });

  it('renders consent screen initially and Start navigates to Chat', () => {
    render(<App />);

    // Consent screen renders notice text
    expect(screen.getByText(/Consent & Privacy Notice/i)).toBeInTheDocument();
    
    // Start button exists
    const startButton = screen.getByRole('button', { name: /Start/i });
    expect(startButton).toBeInTheDocument();

    // Click Start -> navigates to Chat screen
    fireEvent.click(startButton);

    expect(screen.getByText(/SkillSaathi Assistant/i)).toBeInTheDocument();
    expect(screen.getByText(/Conversation will appear here/i)).toBeInTheDocument();
  });

  it('sets textFallbackMode without throwing when navigator.mediaDevices is undefined', () => {
    // Mock navigator.mediaDevices as undefined
    Object.defineProperty(navigator, 'mediaDevices', {
      value: undefined,
      configurable: true,
      writable: true,
    });

    expect(() => {
      render(<App />);
    }).not.toThrow();

    // Verify textFallbackMode flag indicator is set in App
    expect(screen.getByTestId('fallback-banner')).toBeInTheDocument();
    expect(screen.getByText(/Text Fallback Mode Active/i)).toBeInTheDocument();
  });

  it('cycles through screens: Consent -> Chat -> Confirm -> Recommendations', () => {
    render(<App />);

    // 1. Consent -> Start -> Chat
    fireEvent.click(screen.getByRole('button', { name: /Start/i }));
    expect(screen.getByText(/SkillSaathi Assistant/i)).toBeInTheDocument();

    // 2. Chat -> Continue -> Confirm
    fireEvent.click(screen.getByRole('button', { name: /Continue to Confirmation/i }));
    expect(screen.getByText(/Confirm Your Profile/i)).toBeInTheDocument();

    // 3. Confirm -> Recommendations
    fireEvent.click(screen.getByRole('button', { name: /View Recommendations/i }));
    expect(screen.getByText(/Recommended Programs/i)).toBeInTheDocument();

    // 4. Recommendations -> Start Over -> Consent
    fireEvent.click(screen.getByRole('button', { name: /Start Over/i }));
    expect(screen.getByText(/Consent & Privacy Notice/i)).toBeInTheDocument();
  });
});

