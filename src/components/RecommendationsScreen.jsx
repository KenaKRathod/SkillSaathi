import React from 'react';

export const DEFAULT_MOCK_PROGRAMS = [
  {
    id: 'prog-1',
    name: 'Assistant Mason (Construction)',
    scheme: 'Pradhan Mantri Kaushal Vikas Yojana (PMKVY)',
    nsqf_level: 'Level 3',
    duration: '3 Months (300 Hours)',
    reasoning: 'Matches your 4 years of bricklaying experience and desire for formal NSQF certification in Jaipur.',
  },
  {
    id: 'prog-2',
    name: 'General Carpenter Training',
    scheme: 'Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDU-GKY)',
    nsqf_level: 'Level 4',
    duration: '6 Months (570 Hours)',
    reasoning: 'Complements your construction skills with woodworking tools training and placement support.',
  },
  {
    id: 'prog-3',
    name: 'Plumbing & Pipefitting Technician',
    scheme: 'National Apprenticeship Promotion Scheme (NAPS)',
    nsqf_level: 'Level 3',
    duration: '4 Months (400 Hours)',
    reasoning: 'High demand in your district with paid apprenticeship stipends while learning.',
  },
];

export function RecommendationsScreen({
  programs,
  relaxedFiltersNote,
  relaxed_filters,
  audioUrl,
  audio_url,
  onRestart,
  onBackToChat,
}) {
  const effectivePrograms = programs !== undefined ? programs : DEFAULT_MOCK_PROGRAMS;
  const effectiveRelaxedNote = relaxedFiltersNote || relaxed_filters || null;
  const effectiveAudioUrl = audioUrl || audio_url || null;

  if (!effectivePrograms || effectivePrograms.length === 0) {
    return (
      <div className="screen recommendations-screen">
        <header className="screen-header">
          <h2>Recommended Programs</h2>
        </header>

        <main className="recommendations-content">
          <div className="no-match-card" data-testid="no-match-fallback">
            <h3>No matching programs found yet</h3>
            <p>
              We could not find matching programs based on your current profile criteria.
              Please return to chat to refine your information.
            </p>
          </div>

          <button
            type="button"
            className="btn btn-primary btn-large"
            onClick={onBackToChat || onRestart}
            data-testid="back-to-chat-btn"
          >
            Back to Chat
          </button>
        </main>
      </div>
    );
  }

  return (
    <div className="screen recommendations-screen">
      <header className="screen-header">
        <h2>Recommended Programs</h2>
        <p className="subtitle">Top skilling programs matched for your profile</p>
      </header>

      <main className="recommendations-content">
        {effectiveRelaxedNote && (
          <div className="relaxed-filters-banner" data-testid="relaxed-filters-note" role="note">
            <strong>Filter Note:</strong> {effectiveRelaxedNote}
          </div>
        )}

        {effectiveAudioUrl && (
          <div className="audio-player-container" data-testid="audio-player-container">
            <p className="audio-player-label">🔊 Spoken Recommendations Summary</p>
            <audio
              controls
              src={effectiveAudioUrl}
              className="audio-player"
              data-testid="audio-player"
            >
              Your browser does not support the audio element.
            </audio>
          </div>
        )}

        <div className="recommendation-cards" data-testid="program-cards-list">
          {effectivePrograms.map((prog, index) => (
            <div className="card program-card" key={prog.id || index} data-testid="program-card">
              <div className="card-header-tags">
                <span className="scheme-badge">{prog.scheme}</span>
                <span className="nsqf-tag">{prog.nsqf_level}</span>
              </div>
              <h3 className="program-title">{prog.name}</h3>
              <p className="duration-info">
                <strong>Duration:</strong> {prog.duration}
              </p>
              <div className="reasoning-box">
                <strong>Why this matches:</strong>
                <p>{prog.reasoning}</p>
              </div>
              {prog.audio_url && !effectiveAudioUrl && (
                <div className="card-audio-player">
                  <audio controls src={prog.audio_url} data-testid={`card-audio-${index}`} />
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="button-group">
          {onBackToChat && (
            <button
              type="button"
              className="btn btn-secondary btn-large"
              onClick={onBackToChat}
              data-testid="nav-back-to-chat-btn"
            >
              Back to Chat
            </button>
          )}
          <button
            type="button"
            className="btn btn-outline btn-large"
            onClick={onRestart}
          >
            Start Over
          </button>
        </div>
      </main>
    </div>
  );
}

export default RecommendationsScreen;
