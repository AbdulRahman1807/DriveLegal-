'use client';

import { useEffect, useMemo, useState } from 'react';
import ShieldAvatar from './ShieldAvatar';
import styles from './ShieldMascot.module.css';

const WELCOME =
  "Hi! I'm Shield — your AI Road Law Assistant. Ask me anything about traffic laws and fines, or tap the mic to speak!";

type ShieldMascotProps = {
  variant?: 'hero' | 'compact';
  userName?: string;
  speech?: string;
  isTalking?: boolean;
  isListening?: boolean;
  typewriter?: boolean;
  isThinking?: boolean;
};

function HeroWelcome({ userName }: { userName: string }) {
  return (
    <div className={styles.heroWelcome}>
      <p className={styles.heroGreeting}>
        Hi {userName}
      </p>
      <p className={styles.heroLead}>I can help with:</p>
      <ul className={styles.heroList}>
        <li>Traffic Laws</li>
        <li>Fine Calculation</li>
        <li>Required Documents</li>
        <li>Challan Explanations</li>
      </ul>
      <p className={styles.heroPrompt}>What would you like to know?</p>
    </div>
  );
}

export default function ShieldMascot({
  variant = 'compact',
  userName,
  speech = WELCOME,
  isTalking = false,
  isListening = false,
  typewriter = false,
  isThinking = false,
}: ShieldMascotProps) {
  const [displayed, setDisplayed] = useState(speech);
  const isHero = variant === 'hero';
  const showHeroWelcome = isHero && !isTalking && !isListening;

  useEffect(() => {
    if (showHeroWelcome || !typewriter) {
      setDisplayed(speech);
      return;
    }

    setDisplayed('');
    let i = 0;
    const timer = window.setInterval(() => {
      i += 1;
      setDisplayed(speech.slice(0, i));
      if (i >= speech.length) {
        window.clearInterval(timer);
      }
    }, 18);

    return () => window.clearInterval(timer);
  }, [speech, typewriter, showHeroWelcome]);

  const bubbleContent = useMemo(() => {
    if (showHeroWelcome && userName) {
      return <HeroWelcome userName={userName} />;
    }

    const text = displayed || WELCOME;
    if (text.startsWith("Hi! I'm Shield")) {
      return (
        <>
          Hi! I&apos;m <span className={styles.speechName}>Shield</span>
          {text.slice("Hi! I'm Shield".length)}
        </>
      );
    }
    return text;
  }, [displayed, showHeroWelcome, userName]);

  const figure = (
    <ShieldAvatar
      size={isHero ? 'hero' : 'compact'}
      isTalking={isTalking}
      isListening={isListening}
      isThinking={isThinking}
    />
  );

  const bubble = (
    <div className={styles.speechBubble} key={showHeroWelcome ? 'hero' : speech.slice(0, 40)}>
      <div className={styles.speechText}>
        {bubbleContent}
        {typewriter && !showHeroWelcome && displayed.length < speech.length && (
          <span className={styles.speechCursor} aria-hidden />
        )}
      </div>
    </div>
  );

  return (
    <aside
      className={`${styles.mascotWrap} ${isHero ? styles.hero : styles.compact} ${isTalking ? styles.talking : ''} ${isListening ? styles.listening : ''}`}
      aria-label="Shield mascot assistant"
    >
      {isHero ? (
        <>
          {bubble}
          {figure}
        </>
      ) : (
        <>
          {figure}
          {bubble}
        </>
      )}
    </aside>
  );
}

export { WELCOME as SHIELD_WELCOME };
