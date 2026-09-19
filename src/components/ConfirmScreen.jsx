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

export function ConfirmScreen({
  profile,
  onNext,
  onConfirm,
  onBack,
  mapSkillsApiUrl = 'http://localhost:8000/map-skills',
}) {
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
  const [followUpQuestion, setFollowUpQuestion] = useState('');
  const [followUpAnswer, setFollowUpAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (key, value) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const submitProfile = async (payload, answerValue) => {
    const requestPayload = answerValue === undefined ? payload : { ...payload, answer: answerValue };

    if (typeof fetch !== 'function') {
      console.log('Confirmed profile:', payload);
      if (onConfirm) {
        onConfirm(payload);
      } else if (onNext) {
        onNext(payload);
      }
      return;
    }

    setIsSubmitting(true);
    try {
      console.log('Confirmed profile:', payload);
      if (onConfirm) {
        onConfirm(payload);
      }

      const response = await fetch(mapSkillsApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) {
        throw new Error(`Map skills API error with status ${response.status}`);
      }

      const result = await response.json();

      if (result?.status === 'needs_clarification') {
        setFollowUpQuestion(result.question || 'Please provide a bit more detail.');
        setFollowUpAnswer('');
        return;
      }

      onNext?.(result || payload);
    } catch (error) {
      console.error('Map skills request failed:', error);
      onNext?.(payload);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirm = (e) => {
    e?.preventDefault();
    if (followUpQuestion) {
      return;
    }
    submitProfile(formData);
  };

  const handleFollowUpSubmit = (e) => {
    e?.preventDefault();
    if (!followUpAnswer.trim()) {
      return;
    }
    submitProfile(formData, followUpAnswer.trim());
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

          {followUpQuestion && (
            <div className="field-group follow-up-group">
              <label htmlFor="follow-up-answer" className="field-label">
                {followUpQuestion}
              </label>
              <input
                id="follow-up-answer"
                type="text"
                className="field-input"
                value={followUpAnswer}
                onChange={(e) => setFollowUpAnswer(e.target.value)}
                aria-label={followUpQuestion}
              />
              <button
                type="button"
                className="btn btn-primary btn-large"
                onClick={handleFollowUpSubmit}
                disabled={isSubmitting || !followUpAnswer.trim()}
              >
                Submit Answer
              </button>
            </div>
          )}

          {!followUpQuestion && (
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
              <button type="submit" className="btn btn-primary btn-large" disabled={isSubmitting}>
                Confirm
              </button>
            </div>
          )}
        </form>
      </main>
    </div>
  );
}

export default ConfirmScreen;
