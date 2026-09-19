import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import RecommendationsScreen from './RecommendationsScreen';

describe('RecommendationsScreen Component - Task-20 Audio Playback Wiring', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('audio_available: true from /tts POST renders an audio player', async () => {
    const mockPrograms = [
      {
        id: 'p1',
        name: 'Plumbing Specialist',
        scheme: 'PMKVY',
        nsqf_level: 'Level 3',
        duration: '3 Months',
        reasoning: 'Matches plumbing experience in Jaipur.',
      },
    ];

    global.fetch = vi.fn().mockImplementation(async (url, options) => {
      if (url === 'http://localhost:8000/recommend') {
        return {
          ok: true,
          json: async () => ({
            programs: mockPrograms,
          }),
        };
      }
      if (url === 'http://localhost:8000/tts') {
        // Verify payload sent to /tts
        const body = JSON.parse(options.body);
        expect(body.text).toBe('Matches plumbing experience in Jaipur.');
        return {
          ok: true,
          json: async () => ({
            audio_available: true,
            audio_url: 'http://localhost:8000/audio/generated.mp3',
          }),
        };
      }
      return { ok: false };
    });

    render(<RecommendationsScreen profile={{ occupation: 'Plumber' }} />);

    await waitFor(() => {
      expect(screen.getByTestId('audio-player-container')).toBeInTheDocument();
      const audioPlayer = screen.getByTestId('audio-player');
      expect(audioPlayer).toBeInTheDocument();
      expect(audioPlayer).toHaveAttribute('src', 'http://localhost:8000/audio/generated.mp3');
    });
  });

  it('audio_available: false from /tts POST renders no audio player', async () => {
    const mockPrograms = [
      {
        id: 'p1',
        name: 'Solar Installer',
        scheme: 'NAPS',
        nsqf_level: 'Level 4',
        duration: '4 Months',
        reasoning: 'Solar installation training.',
      },
    ];

    global.fetch = vi.fn().mockImplementation(async (url) => {
      if (url === 'http://localhost:8000/recommend') {
        return {
          ok: true,
          json: async () => ({
            programs: mockPrograms,
          }),
        };
      }
      if (url === 'http://localhost:8000/tts') {
        return {
          ok: true,
          json: async () => ({
            audio_available: false,
          }),
        };
      }
      return { ok: false };
    });

    render(<RecommendationsScreen profile={{ occupation: 'Solar Helper' }} />);

    await waitFor(() => {
      expect(screen.getByText('Solar Installer')).toBeInTheDocument();
    });

    // Audio player must NOT be rendered when audio_available is false
    expect(screen.queryByTestId('audio-player-container')).not.toBeInTheDocument();
    expect(screen.queryByTestId('audio-player')).not.toBeInTheDocument();
  });

  it('missing audio_available field in /tts response renders no audio player', async () => {
    const mockPrograms = [
      {
        id: 'p1',
        name: 'Electrician',
        scheme: 'PMKVY',
        nsqf_level: 'Level 4',
        duration: '6 Months',
        reasoning: 'Electrical training.',
      },
    ];

    global.fetch = vi.fn().mockImplementation(async (url) => {
      if (url === 'http://localhost:8000/recommend') {
        return {
          ok: true,
          json: async () => ({
            programs: mockPrograms,
          }),
        };
      }
      if (url === 'http://localhost:8000/tts') {
        // missing audio_available field
        return {
          ok: true,
          json: async () => ({}),
        };
      }
      return { ok: false };
    });

    render(<RecommendationsScreen profile={{ occupation: 'Electrician' }} />);

    await waitFor(() => {
      expect(screen.getByText('Electrician')).toBeInTheDocument();
    });

    // Audio player must NOT be rendered when audio_available field is missing
    expect(screen.queryByTestId('audio-player-container')).not.toBeInTheDocument();
    expect(screen.queryByTestId('audio-player')).not.toBeInTheDocument();
  });

  it('failed fetch for /recommend shows Retry button', async () => {
    global.fetch = vi.fn().mockImplementation(async (url) => {
      if (url === 'http://localhost:8000/recommend') {
        throw new Error('Network error');
      }
      return { ok: true, json: async () => ({}) };
    });

    render(<RecommendationsScreen profile={{ occupation: 'Welder' }} />);

    await waitFor(() => {
      expect(screen.getByTestId('fetch-error-card')).toBeInTheDocument();
      expect(screen.getByTestId('retry-recommend-btn')).toBeInTheDocument();
    });
  });

  it('empty array renders the no-match fallback message and back to Chat button', async () => {
    const onBackToChatMock = vi.fn();
    const user = userEvent.setup();

    global.fetch = vi.fn().mockImplementation(async (url) => {
      if (url === 'http://localhost:8000/recommend') {
        return {
          ok: true,
          json: async () => ({ programs: [] }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    render(<RecommendationsScreen onBackToChat={onBackToChatMock} />);

    await waitFor(() => {
      expect(screen.getByTestId('no-match-fallback')).toBeInTheDocument();
      expect(screen.getByText(/No matching programs found yet/i)).toBeInTheDocument();
    });

    const backBtn = screen.getByTestId('back-to-chat-btn');
    await user.click(backBtn);
    expect(onBackToChatMock).toHaveBeenCalledTimes(1);
  });
});
