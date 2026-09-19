import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import RecommendationsScreen, { DEFAULT_MOCK_PROGRAMS } from './RecommendationsScreen';

describe('RecommendationsScreen Component', () => {
  it('renders 3 mock programs as 3 program cards by default', () => {
    render(<RecommendationsScreen />);

    const cards = screen.getAllByTestId('program-card');
    expect(cards).toHaveLength(3);

    // Verify program names are rendered
    expect(screen.getByText(/Assistant Mason \(Construction\)/i)).toBeInTheDocument();
    expect(screen.getByText(/General Carpenter Training/i)).toBeInTheDocument();
    expect(screen.getByText(/Plumbing & Pipefitting Technician/i)).toBeInTheDocument();

    // Verify scheme and NSQF levels render
    expect(screen.getByText(/PMKVY/i)).toBeInTheDocument();
    expect(screen.getByText(/Level 3/i)).toBeInTheDocument();
  });

  it('renders custom programs array as cards', () => {
    const customPrograms = [
      {
        id: 'c-1',
        name: 'Electrician Apprentice',
        scheme: 'NAPS',
        nsqf_level: 'Level 4',
        duration: '12 Months',
        reasoning: 'Matches electrical wiring experience.',
      },
      {
        id: 'c-2',
        name: 'Solar Panel Installer',
        scheme: 'Suryamitra',
        nsqf_level: 'Level 4',
        duration: '3 Months',
        reasoning: 'High growth renewable energy career path.',
      },
    ];

    render(<RecommendationsScreen programs={customPrograms} />);

    const cards = screen.getAllByTestId('program-card');
    expect(cards).toHaveLength(2);
    expect(screen.getByText(/Electrician Apprentice/i)).toBeInTheDocument();
    expect(screen.getByText(/Solar Panel Installer/i)).toBeInTheDocument();
  });

  it('relaxed_filters note renders when present, absent when not', () => {
    const { rerender } = render(<RecommendationsScreen />);

    // Absent when not present
    expect(screen.queryByTestId('relaxed-filters-note')).not.toBeInTheDocument();

    // Present when relaxedFiltersNote prop is provided
    rerender(
      <RecommendationsScreen
        relaxedFiltersNote="Location requirement was expanded to nearby districts within 50km."
      />
    );

    const note = screen.getByTestId('relaxed-filters-note');
    expect(note).toBeInTheDocument();
    expect(note).toHaveTextContent('Location requirement was expanded to nearby districts within 50km.');

    // Also supports relaxed_filters prop alias
    rerender(
      <RecommendationsScreen
        relaxed_filters="Age requirement was relaxed for informal sector workers."
      />
    );

    expect(screen.getByTestId('relaxed-filters-note')).toHaveTextContent(
      'Age requirement was relaxed for informal sector workers.'
    );
  });

  it('renders optional audio player when audioUrl/audio_url is present', () => {
    const { rerender } = render(<RecommendationsScreen />);

    expect(screen.queryByTestId('audio-player')).not.toBeInTheDocument();

    rerender(
      <RecommendationsScreen audioUrl="https://example.com/audio/summary.mp3" />
    );

    const audioPlayer = screen.getByTestId('audio-player');
    expect(audioPlayer).toBeInTheDocument();
    expect(audioPlayer).toHaveAttribute('src', 'https://example.com/audio/summary.mp3');
  });

  it('empty array renders the no-match fallback message and back to Chat button', async () => {
    const onBackToChatMock = vi.fn();
    const user = userEvent.setup();

    render(<RecommendationsScreen programs={[]} onBackToChat={onBackToChatMock} />);

    // No program cards rendered
    expect(screen.queryByTestId('program-card')).not.toBeInTheDocument();

    // Fallback message rendered
    expect(screen.getByTestId('no-match-fallback')).toBeInTheDocument();
    expect(screen.getByText(/No matching programs found yet/i)).toBeInTheDocument();

    // Back to Chat button rendered
    const backBtn = screen.getByTestId('back-to-chat-btn');
    expect(backBtn).toBeInTheDocument();

    await user.click(backBtn);
    expect(onBackToChatMock).toHaveBeenCalledTimes(1);
  });
});

