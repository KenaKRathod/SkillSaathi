import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MicButton } from './MicButton';

class MockMediaRecorder {
  constructor(stream) {
    this.stream = stream;
    this.state = 'inactive';
    this.ondataavailable = null;
    this.onstop = null;
  }

  start() {
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    if (this.ondataavailable) {
      this.ondataavailable({ data: new Blob(['dummy audio content'], { type: 'audio/webm' }) });
    }
    if (this.onstop) {
      this.onstop();
    }
  }
}

describe('MicButton Component', () => {
  const originalFetch = global.fetch;
  const originalMediaDevices = navigator.mediaDevices;
  const originalMediaRecorder = global.MediaRecorder;

  beforeEach(() => {
    global.MediaRecorder = MockMediaRecorder;
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [{ stop: vi.fn() }],
        }),
      },
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    global.MediaRecorder = originalMediaRecorder;
    Object.defineProperty(navigator, 'mediaDevices', {
      value: originalMediaDevices,
      configurable: true,
      writable: true,
    });
    vi.restoreAllMocks();
  });

  it('successful transcribe calls onTranscript with returned text', async () => {
    const onTranscriptMock = vi.fn();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ text: 'Namaste, I am a painter from Jaipur' }),
    });

    render(<MicButton onTranscript={onTranscriptMock} textFallbackMode={false} />);

    const button = screen.getByRole('button', { name: /Start Recording/i });
    expect(button).toBeInTheDocument();

    // 1. Press to start recording
    await fireEvent.click(button);
    expect(screen.getByTestId('recording-indicator')).toBeInTheDocument();

    // 2. Press again to stop recording and trigger upload
    const stopButton = screen.getByRole('button', { name: /Stop Recording/i });
    await fireEvent.click(stopButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/transcribe',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
      expect(onTranscriptMock).toHaveBeenCalledWith('Namaste, I am a painter from Jaipur');
    });
  });

  it('no_speech_detected response calls onTranscript with null', async () => {
    const onTranscriptMock = vi.fn();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ text: '', error: 'no_speech_detected' }),
    });

    render(<MicButton onTranscript={onTranscriptMock} textFallbackMode={false} />);

    const button = screen.getByRole('button', { name: /Start Recording/i });
    await fireEvent.click(button);

    const stopButton = screen.getByRole('button', { name: /Stop Recording/i });
    await fireEvent.click(stopButton);

    await waitFor(() => {
      expect(onTranscriptMock).toHaveBeenCalledWith(null);
    });
  });

  it('textFallbackMode renders text input instead of mic button and calls onTranscript with typed text', async () => {
    const onTranscriptMock = vi.fn();
    const user = userEvent.setup();

    render(<MicButton onTranscript={onTranscriptMock} textFallbackMode={true} />);

    // Mic button should not be present
    expect(screen.queryByRole('button', { name: /Start Recording/i })).not.toBeInTheDocument();

    // Text input and submit button should be present
    const input = screen.getByPlaceholderText(/Type your response here/i);
    const submitBtn = screen.getByRole('button', { name: /Send/i });

    expect(input).toBeInTheDocument();
    expect(submitBtn).toBeInTheDocument();

    // Type text and submit form
    await user.type(input, 'I have 5 years experience in carpentry');
    await user.click(submitBtn);

    expect(onTranscriptMock).toHaveBeenCalledWith('I have 5 years experience in carpentry');
  });
});

