import React, { useState } from 'react';

export const PROFILE_FIELDS = [
  { key: 'occupation', label: 'Occupation' },
  { key: 'years_experience', label: 'Years of Experience' },
  { key: 'tools_used', label: 'Tools Used' },
  { key: 'education', label: 'Education' },
  { key: 'district', label: 'District' },
  { key: 'wage_goal', label: 'Wage Goal' },
  { key: 'mobility', label: 'Mobility' },
];

export const DEFAULT_MOCK_PROFILE = {
  occupation: 'Mason / Bricklayer',
  years_experience: '4 years',
  tools_used: 'Trowel, Plumb Line, Cement Mixer',
  education: '8th Pass',
  district: 'Jaipur, Rajasthan',
  wage_goal: '18000/month',
  mobility: 'Yes (within state)',
};

export function ConfirmScreen({ profile, onNext, onConfirm, onBack }) {
  const [formData, setFormData] = useState(() => {
    const source = profile || DEFAULT_MOCK_PROFILE;
    const initial = {};
    PROFILE_FIELDS.forEach(({ key }) => {
      const val = source[key];
      if (val !== undefined && val !== null && String(val).trim() !== '') {
        initial[key] = String(val);
      } else {
        initial[key] = 'Not specified';
      }
    });
    return initial;
  });

  const handleChange = (key, value) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleConfirm = (e) => {
    e?.preventDefault();
    console.log('Confirmed profile:', formData);
    if (onConfirm) {
      onConfirm(formData);
    } else if (onNext) {
      onNext(formData);
    }
  };

  return (
    <div className="screen confirm-screen">
      <header className="screen-header">
        <h2>Confirm Your Profile</h2>
        <p className="subtitle">Review and edit your profile details below</p>
      </header>

      <main className="confirm-content">
        <form className="profile-form" onSubmit={handleConfirm}>
          <div className="fields-container">
            {PROFILE_FIELDS.map(({ key, label }) => (
              <div className="field-group" key={key}>
                <label htmlFor={`field-${key}`} className="field-label">
                  {label}
                </label>
                <input
                  id={`field-${key}`}
                  name={key}
                  type="text"
                  className="field-input"
                  value={formData[key]}
                  onChange={(e) => handleChange(key, e.target.value)}
                  data-testid={`input-${key}`}
                />
              </div>
            ))}
          </div>

          <div className="button-group">
            {onBack && (
              <button
                type="button"
                className="btn btn-secondary btn-large"
                onClick={onBack}
              >
                Back to Chat
              </button>
            )}
            <button type="submit" className="btn btn-primary btn-large">
              Confirm
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

export default ConfirmScreen;
