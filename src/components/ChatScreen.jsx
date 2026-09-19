import React from 'react';

export function ChatScreen({ onNext, textFallbackMode }) {
  return (
    <div className="screen chat-screen">
      <header className="screen-header">
        <h2>SkillSaathi Assistant</h2>
        <span className="badge">
          {textFallbackMode ? 'Text Mode' : 'Voice Mode'}
        </span>
      </header>

      <main className="chat-content">
        <div className="chat-status">
          {textFallbackMode ? (
            <p>Voice recording is disabled. Please type your responses below.</p>
          ) : (
            <p>Tap the microphone button to start speaking.</p>
          )}
        </div>

        <div className="chat-placeholder">
          <p className="placeholder-text">Conversation will appear here...</p>
        </div>

        <button className="btn btn-primary btn-large" onClick={onNext}>
          Continue to Confirmation
        </button>
      </main>
    </div>
  );
}

