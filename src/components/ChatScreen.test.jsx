import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ChatScreen } from './ChatScreen';

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
      this.ondataavailable({ data: new Blob(['audio'], { type: 'audio/webm' }) });
    }
    if (this.onstop) {
      this.onstop();
    }
  }
}

describe('ChatScreen Component', () => {
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

  it('valid transcript produces both user and assistant chat bubbles', async () => {
    const onNextMock = vi.fn();

    // Mock fetch for POST /chat
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'sess_123',
        next_question: 'What is your current occupation?',
        status: 'in_progress',
      }),
    });

    render(<ChatScreen onNext={onNextMock} textFallbackMode={true} />);

    const input = screen.getByPlaceholderText(/Type your response here/i);
    const sendBtn = screen.getByRole('button', { name: /Send/i });

    // Send user message in text fallback mode
    await userEvent.type(input, 'Namaste, I am a mason');
    await userEvent.click(sendBtn);

    // Verify user chat bubble appears
    expect(screen.getByText('Namaste, I am a mason')).toBeInTheDocument();

    // Verify /chat endpoint was called with session_id and message
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/chat',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            session_id: expect.stringMatching(/^sess_/),
            message: 'Namaste, I am a mason',
          }),
        })
      );

      // Verify assistant chat bubble appears
      expect(screen.getByText('What is your current occupation?')).toBeInTheDocument();
    });
  });

  it('null transcript shows retry-prompt without calling /chat', async () => {
    const onNextMock = vi.fn();
    global.fetch = vi.fn();

    // Mock STT returning no speech (data.error = "no_speech_detected")
    // When MicButton stops recording, fetch for /transcribe returns no_speech_detected
    let fetchCallCount = 0;
    global.fetch = vi.fn().mockImplementation(async (url) => {
      fetchCallCount++;
      if (url === 'http://localhost:8000/transcribe') {
        return {
          ok: true,
          json: async () => ({ text: '', error: 'no_speech_detected' }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    render(<ChatScreen onNext={onNextMock} textFallbackMode={false} />);

    // Press mic button to start and stop
    const startMicBtn = screen.getByRole('button', { name: /Start Recording/i });
    await fireEvent.click(startMicBtn);

    const stopMicBtn = screen.getByRole('button', { name: /Stop Recording/i });
    await fireEvent.click(stopMicBtn);

    // Verify inline retry prompt appears
    await waitFor(() => {
      expect(screen.getByText(/Didn't catch that — try again/i)).toBeInTheDocument();
    });

    // Verify /chat was NEVER called (only /transcribe was called)
    const chatCalls = global.fetch.mock.calls.filter((call) => call[0] === 'http://localhost:8000/chat');
    expect(chatCalls.length).toBe(0);
  });

  it('failed /chat call shows Retry button, and clicking it resends the same message', async () => {
    const onNextMock = vi.fn();

    let attempt = 0;
    global.fetch = vi.fn().mockImplementation(async (url) => {
      if (url === 'http://localhost:8000/chat') {
        attempt++;
        if (attempt === 1) {
          throw new Error('Network error');
        }
        return {
          ok: true,
          json: async () => ({
            session_id: 'sess_123',
            next_question: 'How many years of experience do you have?',
            status: 'in_progress',
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    render(<ChatScreen onNext={onNextMock} textFallbackMode={true} />);

    const input = screen.getByPlaceholderText(/Type your response here/i);
    const sendBtn = screen.getByRole('button', { name: /Send/i });

    await userEvent.type(input, 'I do electric work');
    await userEvent.click(sendBtn);

    // Verify failed fetch error card and Retry button appear
    await waitFor(() => {
      expect(screen.getByText(/Failed to send message/i)).toBeInTheDocument();
      expect(screen.getByTestId('retry-button')).toBeInTheDocument();
    });

    // Click Retry button
    const retryBtn = screen.getByTestId('retry-button');
    await fireEvent.click(retryBtn);

    // Verify second /chat call succeeds and assistant response renders
    await waitFor(() => {
      expect(screen.getByText('How many years of experience do you have?')).toBeInTheDocument();
      expect(screen.queryByText(/Failed to send message/i)).not.toBeInTheDocument();
    });

    const chatCalls = global.fetch.mock.calls.filter((call) => call[0] === 'http://localhost:8000/chat');
    expect(chatCalls.length).toBe(2);
    expect(JSON.parse(chatCalls[0][1].body).message).toBe('I do electric work');
    expect(JSON.parse(chatCalls[1][1].body).message).toBe('I do electric work');
  });

  it('status: "complete" passes profile up to onNext', async () => {
    const onNextMock = vi.fn();
    const mockProfile = { occupation: 'Painter', experience_years: 5 };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'sess_123',
        next_question: 'Thank you! We have compiled your profile.',
        status: 'complete',
        profile: mockProfile,
      }),
    });

    render(<ChatScreen onNext={onNextMock} textFallbackMode={true} />);

    const input = screen.getByPlaceholderText(/Type your response here/i);
    const sendBtn = screen.getByRole('button', { name: /Send/i });

    await userEvent.type(input, 'Jaipur Rajasthan');
    await userEvent.click(sendBtn);

    await waitFor(() => {
      expect(onNextMock).toHaveBeenCalledWith(mockProfile);
    });
  });
});

