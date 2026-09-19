import React from 'react';

export function RecommendationsScreen({ onRestart }) {
  return (
    <div className="screen recommendations-screen">
      <header className="screen-header">
        <h2>Recommended Programs</h2>
      </header>

      <main className="recommendations-content">
        <p className="intro">Based on your skills and goals, here are top matching programs:</p>

        <div className="recommendation-cards">
          <div className="card">
            <h3>PMKVY Vocational Training</h3>
            <p>Short-term training for skill certification and career advancement.</p>
          </div>
        </div>

        <button className="btn btn-outline btn-large" onClick={onRestart}>
          Start Over
        </button>
      </main>
    </div>
  );
}

