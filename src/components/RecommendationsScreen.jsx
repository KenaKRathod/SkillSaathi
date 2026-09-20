import React, { useState, useEffect, useCallback } from 'react';

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
  profile,
  categoryResult,
  category_result,
  programs: initialPrograms,
  relaxedFiltersNote: initialRelaxedNote,
  relaxed_filters: initialRelaxedFilters,
  audioUrl: initialAudioUrl,
  audio_url: initialAudioUrlAlt,
  apiUrl = 'http://localhost:8000/recommend',
  ttsApiUrl = 'http://localhost:8000/tts',
  onRestart,
  onBackToChat,
  skipFetch = false,
}) {
  const [programs, setPrograms] = useState(initialPrograms !== undefined ? initialPrograms : null);
  const [relaxedFiltersNote, setRelaxedFiltersNote] = useState(initialRelaxedNote || initialRelaxedFilters || null);
  const [audioUrl, setAudioUrl] = useState(initialAudioUrl || initialAudioUrlAlt || null);
  const [audioAvailable, setAudioAvailable] = useState(Boolean(initialAudioUrl || initialAudioUrlAlt));
  const [isLoading, setIsLoading] = useState(!skipFetch && initialPrograms === undefined);
  const [fetchError, setFetchError] = useState(false);

  const fetchRecommendations = useCallback(async () => {
    setIsLoading(true);
    setFetchError(false);

    const payloadCategory = categoryResult || category_result || null;
    const payloadProfile = profile || null;

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mapped_categories: payloadCategory,
          profile: payloadProfile,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error with status ${response.status}`);
      }

      const data = await response.json();

      const receivedPrograms = data.results || data.programs || data.recommendations || [];
      const receivedNote = data.relaxed_filters || data.relaxedFiltersNote || null;
      const initialReceivedAudio = data.audio_url || data.audioUrl || null;

      setPrograms(receivedPrograms);
      setRelaxedFiltersNote(receivedNote);

      if (initialReceivedAudio) {
        setAudioUrl(initialReceivedAudio);
        setAudioAvailable(true);
      } else {
        setAudioUrl(null);
        setAudioAvailable(false);
      }

      // Task-20: POST top result's reasoning text to /tts
      if (receivedPrograms && receivedPrograms.length > 0) {
        const topReasoning = receivedPrograms[0].reasoning || receivedPrograms[0].name;
        try {
          const ttsResponse = await fetch(ttsApiUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              text: topReasoning,
            }),
          });

          if (ttsResponse.ok) {
            const contentType = ttsResponse.headers.get('content-type') || '';
            if (contentType.includes('audio/')) {
              // Success: backend returned binary audio
              const audioBlob = await ttsResponse.blob();
              const blobUrl = URL.createObjectURL(audioBlob);
              setAudioAvailable(true);
              setAudioUrl(blobUrl);
            } else {
              // Fallback: backend returned JSON (gTTS failure)
              const ttsData = await ttsResponse.json();
              if (ttsData && ttsData.audio_available === true) {
                setAudioAvailable(true);
                setAudioUrl(ttsData.audio_url || initialReceivedAudio);
              } else {
                setAudioAvailable(false);
                setAudioUrl(null);
              }
            }
          } else {
            setAudioAvailable(false);
            setAudioUrl(null);
          }
        } catch (ttsErr) {
          // If /tts fails or audio_available is false/missing, render no audio element
          setAudioAvailable(false);
          setAudioUrl(null);
        }
      }
    } catch (err) {
      setFetchError(true);
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, ttsApiUrl, categoryResult, category_result, profile]);

  useEffect(() => {
    if (!skipFetch && initialPrograms === undefined) {
      fetchRecommendations();
    }
  }, [fetchRecommendations, initialPrograms, skipFetch]);

  // Sync props if directly passed in unit tests
  useEffect(() => {
    if (initialPrograms !== undefined) {
      setPrograms(initialPrograms);
      setIsLoading(false);
    }
    if (initialRelaxedNote || initialRelaxedFilters) {
      setRelaxedFiltersNote(initialRelaxedNote || initialRelaxedFilters);
    }
    if (initialAudioUrl || initialAudioUrlAlt) {
      setAudioUrl(initialAudioUrl || initialAudioUrlAlt);
      setAudioAvailable(true);
    }
  }, [initialPrograms, initialRelaxedNote, initialRelaxedFilters, initialAudioUrl, initialAudioUrlAlt]);

  const effectivePrograms = programs !== null ? programs : (skipFetch ? DEFAULT_MOCK_PROGRAMS : []);

  if (isLoading) {
    return (
      <div className="screen recommendations-screen">
        <header className="screen-header">
          <h2>Recommended Programs</h2>
          <p className="subtitle">Matching top skilling programs for your profile...</p>
        </header>
        <main className="recommendations-content">
          <div className="loading-container" data-testid="loading-indicator">
            <span className="spinner" aria-hidden="true"></span>
            <p>Finding recommended skilling programs...</p>
          </div>
        </main>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="screen recommendations-screen">
        <header className="screen-header">
          <h2>Recommended Programs</h2>
        </header>

        <main className="recommendations-content">
          <div className="fetch-error-card" role="alert" data-testid="fetch-error-card">
            <span>Failed to load recommendations. Please try again.</span>
            <button
              type="button"
              className="btn btn-secondary btn-retry"
              onClick={fetchRecommendations}
              data-testid="retry-recommend-btn"
            >
              Retry
            </button>
          </div>

          <div className="button-group">
            {onBackToChat && (
              <button
                type="button"
                className="btn btn-secondary btn-large"
                onClick={onBackToChat}
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
        {relaxedFiltersNote && (
          <div className="relaxed-filters-banner" data-testid="relaxed-filters-note" role="note">
            <strong>Filter Note:</strong> {relaxedFiltersNote}
          </div>
        )}

        {audioAvailable && audioUrl && (
          <div className="audio-player-container" data-testid="audio-player-container">
            <p className="audio-player-label">🔊 Spoken Recommendations Summary</p>
            <audio
              controls
              src={audioUrl}
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
