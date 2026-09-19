import React from 'react';

export function ConsentScreen({ onStart, textFallbackMode }) {
  return (
    <div className="screen consent-screen">
      <header className="screen-header">
        <h1>SkillSaathi</h1>
        <p className="subtitle">Voice & Career Assistance for Rural Workers</p>
      </header>

      <main className="consent-content">
        <div className="notice-card">
          <h2>Consent & Privacy Notice</h2>
          <p>
            Welcome to SkillSaathi. We help you explore skilling programs and career opportunities.
          </p>
          <p>
            By continuing, you agree to allow SkillSaathi to process your spoken audio or text input
            to match your skills with government and vocational programs.
          </p>
          {textFallbackMode && (
            <div className="warning-banner" role="alert">
              <strong>Text Mode Active:</strong> Voice media access is not available on this device/browser. Chat will use text input.
            </div>
          )}
        </div>

        <button className="btn btn-primary btn-large" onClick={onStart}>
          Start
        </button>
      </main>
    </div>
  );
}

