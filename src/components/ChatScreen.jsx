import React, { useState } from 'react';
import { MicButton } from './MicButton';

export function ChatScreen({ onNext, textFallbackMode }) {
  const [messages, setMessages] = useState([]);
  const [showRetryPrompt, setShowRetryPrompt] = useState(false);

  const handleTranscript = (text) => {
    if (text === null) {
      setShowRetryPrompt(true);
    } else {
      setShowRetryPrompt(false);
      setMessages((prev) => [...prev, { role: 'user', text }]);
    }
  };

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

        {showRetryPrompt && (
          <div className="retry-prompt" role="alert">
            No speech detected. Please try speaking again.
          </div>
        )}

        <div className="chat-box">
          {messages.length === 0 ? (
            <p className="placeholder-text">Conversation will appear here...</p>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <strong>{msg.role === 'user' ? 'You' : 'Agent'}:</strong> {msg.text}
              </div>
            ))
          )}
        </div>

        <div className="controls-area">
          <MicButton
            onTranscript={handleTranscript}
            textFallbackMode={textFallbackMode}
          />
        </div>

        <button className="btn btn-primary btn-large nav-btn" onClick={onNext}>
          Continue to Confirmation
        </button>
      </main>
    </div>
  );
}

export default ChatScreen;
