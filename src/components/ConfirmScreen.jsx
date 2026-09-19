import React from 'react';

export function ConfirmScreen({ profile, onNext, onBack }) {
  return (
    <div className="screen confirm-screen">
      <header className="screen-header">
        <h2>Confirm Your Profile</h2>
      </header>

      <main className="confirm-content">
        <p className="summary-notice">
          Please review the details we gathered before viewing skilling recommendations.
        </p>

        <div className="summary-card" data-testid="profile-summary">
          {profile && Object.keys(profile).length > 0 ? (
            <ul className="profile-list">
              {Object.entries(profile).map(([key, val]) => (
                <li key={key}>
                  <strong>{key.replace(/_/g, ' ')}:</strong> {String(val)}
                </li>
              ))}
            </ul>
          ) : (
            <p><em>Profile details summary will appear here.</em></p>
          )}
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

export default ConfirmScreen;
