import React, { useState, useRef } from 'react';

export function MicButton({
  onTranscript,
  textFallbackMode = false,
  apiUrl = 'http://localhost:8000/transcribe',
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [typedText, setTypedText] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleStartRecording = async () => {
    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsLoading(true);
        // Stop audio tracks
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        try {
          const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData,
          });

          const data = await response.json();

          if (data && data.error === 'no_speech_detected') {
            onTranscript?.(null);
          } else if (data && typeof data.text === 'string') {
            onTranscript?.(data.text);
          } else {
            onTranscript?.(null);
          }
        } catch (error) {
          onTranscript?.(null);
        } finally {
          setIsLoading(false);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      onTranscript?.(null);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      handleStopRecording();
    } else {
      handleStartRecording();
    }
  };

  const handleFallbackSubmit = (e) => {
    e.preventDefault();
    if (typedText.trim()) {
      onTranscript?.(typedText.trim());
      setTypedText('');
    }
  };

  if (textFallbackMode) {
    return (
      <form className="fallback-input-form" onSubmit={handleFallbackSubmit}>
        <input
          type="text"
          className="fallback-input"
          value={typedText}
          onChange={(e) => setTypedText(e.target.value)}
          placeholder="Type your response here..."
          aria-label="Text input"
        />
        <button type="submit" className="btn btn-primary btn-large">
          Send
        </button>
      </form>
    );
  }

  return (
    <div className="mic-button-container">
      <button
        type="button"
        className={`btn btn-large mic-btn ${isRecording ? 'recording' : ''} ${isLoading ? 'loading' : ''}`}
        onClick={toggleRecording}
        disabled={isLoading}
        aria-label={isRecording ? 'Stop Recording' : 'Start Recording'}
      >
        {isLoading ? (
          <>
            <span className="spinner" data-testid="spinner" aria-hidden="true"></span>
            Transcribing...
          </>
        ) : isRecording ? (
          <>
            <span className="recording-dot" data-testid="recording-indicator" aria-hidden="true"></span>
            Recording... Press to Stop
          </>
        ) : (
          <>
            <span className="mic-icon" aria-hidden="true">🎙️</span>
            Press to Speak
          </>
        )}
      </button>
    </div>
  );
}

export default MicButton;

