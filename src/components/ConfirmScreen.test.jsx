import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import ConfirmScreen, { DEFAULT_MOCK_PROFILE, PROFILE_FIELDS } from './ConfirmScreen';

describe('ConfirmScreen Component', () => {
  let consoleSpy;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  it('renders all 7 fields with correct initial values when default mock profile is used', () => {
    render(<ConfirmScreen />);

    PROFILE_FIELDS.forEach(({ key, label }) => {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
      const input = screen.getByTestId(`input-${key}`);
      expect(input).toHaveValue(DEFAULT_MOCK_PROFILE[key]);
    });
  });

  it('editing a field updates its displayed value', async () => {
    const user = userEvent.setup();
    render(<ConfirmScreen />);

    const occupationInput = screen.getByTestId('input-occupation');
    expect(occupationInput).toHaveValue('Mason / Bricklayer');

    await user.clear(occupationInput);
    await user.type(occupationInput, 'Senior Carpenter');

    expect(occupationInput).toHaveValue('Senior Carpenter');
  });

  it('renders "Not specified" for a profile object missing one field while remaining editable', async () => {
    const user = userEvent.setup();
    const partialProfile = {
      occupation: 'Plumber',
      years_experience: '2 years',
      // tools_used is missing
      education: '10th Pass',
      district: 'Delhi',
      wage_goal: '20000/month',
      mobility: 'Local only',
    };

    render(<ConfirmScreen profile={partialProfile} />);

    // tools_used is missing from partialProfile, so it should render "Not specified"
    const missingInput = screen.getByTestId('input-tools_used');
    expect(missingInput).toHaveValue('Not specified');

    // Specified fields should have their passed values
    expect(screen.getByTestId('input-occupation')).toHaveValue('Plumber');

    // Missing field input remains editable
    await user.clear(missingInput);
    await user.type(missingInput, 'Pipe Wrench');
    expect(missingInput).toHaveValue('Pipe Wrench');
  });

  it('clicking Confirm logs the final profile and calls onNext/onConfirm', async () => {
    const onConfirmMock = vi.fn();
    const user = userEvent.setup();

    render(<ConfirmScreen onConfirm={onConfirmMock} />);

    const occupationInput = screen.getByTestId('input-occupation');
    await user.clear(occupationInput);
    await user.type(occupationInput, 'Electrician');

    const confirmButton = screen.getByRole('button', { name: /Confirm/i });
    await user.click(confirmButton);

    expect(consoleSpy).toHaveBeenCalledWith(
      'Confirmed profile:',
      expect.objectContaining({
        occupation: 'Electrician',
        years_experience: '4 years',
      })
    );

    expect(onConfirmMock).toHaveBeenCalledWith(
      expect.objectContaining({
        occupation: 'Electrician',
      })
    );
  });
});

