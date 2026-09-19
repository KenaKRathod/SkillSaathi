import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import RecommendationsScreen, { DEFAULT_MOCK_PROGRAMS } from './RecommendationsScreen';

describe('RecommendationsScreen Component', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('on mount, POSTs confirmed category + profile to /recommend and renders real cards on success', async () => {
    const mockProfile = { occupation: 'Electrician', experience_years: 3 };
    const mockCategory = { primary_category: 'Electrical & Solar' };
    const mockRealPrograms = [
      {
        id: 'real-1',
        name: 'Solar Panel Maintenance Technician',
        scheme: 'PMKVY 4.0',
        nsqf_level: 'Level 4',
        duration: '3 Months',
        reasoning: 'Direct match for your 3 years of electrical experience.',
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        programs: mockRealPrograms,
        relaxed_filters: 'Expanded radius to 30km.',
        audio_url: 'https://example.com/audio/rec.mp3',
      }),
    });

    render(
      <RecommendationsScreen
        profile={mockProfile}
        categoryResult={mockCategory}
      />
    );

    // Initial loading indicator is displayed
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

    // Verify POST request payload to /recommend
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/recommend',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            category_result: mockCategory,
            profile: mockProfile,
          }),
        })
      );

      // Verify real program card is rendered
      expect(screen.getByText('Solar Panel Maintenance Technician')).toBeInTheDocument();
      expect(screen.getByText(/PMKVY 4.0/i)).toBeInTheDocument();
      expect(screen.getByTestId('relaxed-filters-note')).toHaveTextContent('Expanded radius to 30km.');
      expect(screen.getByTestId('audio-player')).toHaveAttribute('src', 'https://example.com/audio/rec.mp3');
    });
  });

  it('failed fetch shows Retry button, and clicking it re-sends the request', async () => {
    let attempt = 0;
    global.fetch = vi.fn().mockImplementation(async () => {
      attempt++;
      if (attempt === 1) {
        throw new Error('Network error');
      }
      return {
        ok: true,
        json: async () => ({
          programs: [
            {
              id: 'retried-1',
              name: 'Certified Mason Helper',
              scheme: 'NAPS',
              nsqf_level: 'Level 3',
              duration: '2 Months',
              reasoning: 'Retried fetch recommendation.',
            },
          ],
        }),
      };
    });

    render(<RecommendationsScreen profile={{ occupation: 'Mason' }} />);

    // Wait for failed fetch error card and Retry button
    await waitFor(() => {
      expect(screen.getByTestId('fetch-error-card')).toBeInTheDocument();
      expect(screen.getByTestId('retry-recommend-btn')).toBeInTheDocument();
    });

    // Click Retry button
    const retryBtn = screen.getByTestId('retry-recommend-btn');
    await fireEvent.click(retryBtn);

    // Verify second request succeeds and card is rendered
    await waitFor(() => {
      expect(screen.getByText('Certified Mason Helper')).toBeInTheDocument();
      expect(screen.queryByTestId('fetch-error-card')).not.toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('renders 3 mock programs when skipFetch={true} or when programs prop is passed', () => {
    render(<RecommendationsScreen skipFetch={true} />);

    const cards = screen.getAllByTestId('program-card');
    expect(cards).toHaveLength(3);
    expect(screen.getByText(/Assistant Mason \(Construction\)/i)).toBeInTheDocument();
  });

  it('relaxed_filters note renders when present in prop/response, absent when not', () => {
    const { rerender } = render(
      <RecommendationsScreen skipFetch={true} />
    );

    expect(screen.queryByTestId('relaxed-filters-note')).not.toBeInTheDocument();

    rerender(
      <RecommendationsScreen
        skipFetch={true}
        relaxedFiltersNote="Location requirement was expanded to nearby districts within 50km."
      />
    );

    const note = screen.getByTestId('relaxed-filters-note');
    expect(note).toBeInTheDocument();
    expect(note).toHaveTextContent('Location requirement was expanded to nearby districts within 50km.');
  });

  it('empty array renders the no-match fallback message and back to Chat button', async () => {
    const onBackToChatMock = vi.fn();
    const user = userEvent.setup();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        programs: [],
      }),
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
