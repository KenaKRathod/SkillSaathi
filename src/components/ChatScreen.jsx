import React, { useState } from 'react';
import { MicButton } from './MicButton';

export function ChatScreen({
  onNext,
  textFallbackMode = false,
  chatApiUrl = 'http://localhost:8000/chat',
}) {
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 11));
  const [messages, setMessages] = useState([]);
  const [noSpeechPrompt, setNoSpeechPrompt] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  const [lastUserMessage, setLastUserMessage] = useState('');
  const [isSending, setIsSending] = useState(false);

  const sendChatMessage = async (messageText) => {
    setIsSending(true);
    setFetchError(false);
    setLastUserMessage(messageText);

    try {
      const response = await fetch(chatApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: messageText,
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat API error with status ${response.status}`);
      }

      const data = await response.json();

      if (data && data.next_question) {
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + Math.random(), role: 'assistant', text: data.next_question },
        ]);
      }

      if (data && data.status === 'complete') {
        onNext?.(data.profile || {});
      }
    } catch (err) {
      setFetchError(true);
    } finally {
      setIsSending(false);
    }
  };

  const handleTranscript = (transcript) => {
    if (transcript === null) {
      setNoSpeechPrompt(true);
      return;
    }

    if (typeof transcript === 'string' && transcript.trim()) {
      setNoSpeechPrompt(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + Math.random(), role: 'user', text: transcript },
      ]);
      sendChatMessage(transcript);
    }
  };

  const handleRetryFetch = () => {
    if (lastUserMessage) {
      sendChatMessage(lastUserMessage);
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

        {noSpeechPrompt && (
          <div className="retry-prompt" role="alert">
            Didn't catch that — try again
          </div>
        )}

        <div className="chat-box" data-testid="chat-box">
          {messages.length === 0 ? (
            <p className="placeholder-text">Conversation will appear here...</p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-bubble ${msg.role}`}
                data-testid={`${msg.role}-bubble`}
              >
                <div className="bubble-sender">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div className="bubble-text">{msg.text}</div>
              </div>
            ))
          )}

          {isSending && (
            <div className="chat-bubble assistant loading-bubble" data-testid="assistant-loading">
              <span className="typing-indicator">Assistant is thinking...</span>
            </div>
          )}
        </div>

        {fetchError && (
          <div className="fetch-error-card" role="alert">
            <span>Failed to send message.</span>
            <button
              type="button"
              className="btn btn-secondary btn-retry"
              onClick={handleRetryFetch}
              data-testid="retry-button"
            >
              Retry
            </button>
          </div>
        )}

        <div className="controls-area">
          <MicButton
            onTranscript={handleTranscript}
            textFallbackMode={textFallbackMode}
          />
        </div>
      </main>
    </div>
  );
}

export default ChatScreen;
