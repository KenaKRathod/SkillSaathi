import React, { useState, useEffect } from 'react';
import { ConsentScreen } from './components/ConsentScreen';
import { ChatScreen } from './components/ChatScreen';
import { ConfirmScreen } from './components/ConfirmScreen';
import { RecommendationsScreen } from './components/RecommendationsScreen';
import './App.css';

export const SCREENS = {
  CONSENT: 'Consent',
  CHAT: 'Chat',
  CONFIRM: 'Confirm',
  RECOMMENDATIONS: 'Recommendations',
};

export function App() {
  const [currentScreen, setCurrentScreen] = useState(SCREENS.CONSENT);
  const [textFallbackMode, setTextFallbackMode] = useState(false);

  useEffect(() => {
    // Fallback: If navigator.mediaDevices is undefined, set global textFallbackMode flag in state without crashing
    const isMediaDevicesAvailable =
      typeof navigator !== 'undefined' &&
      navigator !== null &&
      Boolean(navigator.mediaDevices);

    if (!isMediaDevicesAvailable) {
      setTextFallbackMode(true);
    }
  }, []);

  return (
    <div className="app-container" data-text-fallback={textFallbackMode}>
      {textFallbackMode && (
        <div className="fallback-banner" data-testid="fallback-banner">
          Text Fallback Mode Active (No Audio Device Detected)
        </div>
      )}

      {currentScreen === SCREENS.CONSENT && (
        <ConsentScreen
          onStart={() => setCurrentScreen(SCREENS.CHAT)}
          textFallbackMode={textFallbackMode}
        />
      )}

      {currentScreen === SCREENS.CHAT && (
        <ChatScreen
          onNext={() => setCurrentScreen(SCREENS.CONFIRM)}
          textFallbackMode={textFallbackMode}
        />
      )}

      {currentScreen === SCREENS.CONFIRM && (
        <ConfirmScreen
          onNext={() => setCurrentScreen(SCREENS.RECOMMENDATIONS)}
          onBack={() => setCurrentScreen(SCREENS.CHAT)}
        />
      )}

      {currentScreen === SCREENS.RECOMMENDATIONS && (
        <RecommendationsScreen
          onRestart={() => setCurrentScreen(SCREENS.CONSENT)}
        />
      )}
    </div>
  );
}

export default App;

