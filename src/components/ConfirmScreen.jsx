import React from 'react';

export function ConfirmScreen({ onNext, onBack }) {
  return (
    <div className="screen confirm-screen">
      <header className="screen-header">
        <h2>Confirm Your Profile</h2>
      </header>

      <main className="confirm-content">
        <p className="summary-notice">
          Please review the details we gathered before viewing skilling recommendations.
        </p>

        <div className="summary-card">
          <p><em>Profile details summary will appear here.</em></p>
        </div>

        <div className="button-group">
          <button className="btn btn-secondary btn-large" onClick={onBack}>
            Back to Chat
          </button>
          <button className="btn btn-primary btn-large" onClick={onNext}>
            View Recommendations
          </button>
        </div>
      </main>
    </div>
  );
}

