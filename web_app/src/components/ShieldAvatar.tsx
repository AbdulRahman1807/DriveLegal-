'use client';

import dynamic from 'next/dynamic';
import Image from 'next/image';
import { Component, useCallback, useEffect, useState, type ReactNode } from 'react';
import styles from './ShieldAvatar.module.css';

const ShieldModel3D = dynamic(() => import('./ShieldModel3D'), {
  ssr: false,
  loading: () => <div className={styles.modelLoading} aria-hidden />,
});

const DRAG_HINT_KEY = 'drivelegal-shield-drag-hint-dismissed';

type ShieldAvatarProps = {
  size?: 'hero' | 'compact' | 'auth';
  isTalking?: boolean;
  isListening?: boolean;
  showDragHint?: boolean;
  isThinking?: boolean;
};

const SIZES = {
  hero: { w: 120, h: 130, className: styles.hero },
  compact: { w: 64, h: 70, className: styles.compact },
  auth: { w: 220, h: 240, className: styles.auth },
} as const;

class ModelErrorBoundary extends Component<
  { fallback: ReactNode; children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { fallback: ReactNode; children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

export default function ShieldAvatar({
  size = 'hero',
  showDragHint = false,
  isTalking = false,
  isListening = false,
  isThinking = false,
}: ShieldAvatarProps) {
  const dim = SIZES[size];
  const [dragHintVisible, setDragHintVisible] = useState(false);

  useEffect(() => {
    if (!showDragHint) return;
    const dismissed = sessionStorage.getItem(DRAG_HINT_KEY);
    setDragHintVisible(!dismissed);
  }, [showDragHint]);

  const dismissDragHint = useCallback(() => {
    setDragHintVisible(false);
    sessionStorage.setItem(DRAG_HINT_KEY, '1');
  }, []);

  const handleDragStart = useCallback(() => {
    dismissDragHint();
  }, [dismissDragHint]);

  const fallback = (
    <Image
      src="/shield-mascot.png"
      alt="Shield — DriveLegal AI assistant"
      width={dim.w}
      height={dim.h}
      className={styles.image}
      priority
    />
  );

  return (
    <div className={`${styles.avatarStack} ${showDragHint ? styles.avatarStackWithHint : ''}`}>
      <div className={`${styles.wrap} ${dim.className}`}>
        <ModelErrorBoundary fallback={fallback}>
          <ShieldModel3D size={size} onDragStart={handleDragStart} isTalking={isTalking} isListening={isListening} isThinking={isThinking} />
        </ModelErrorBoundary>
      </div>

      {showDragHint && dragHintVisible && (
        <div className={styles.dragHint} role="status">
          <p className={styles.dragHintText}>
            <span className={styles.dragHintIcon} aria-hidden>
              ↻
            </span>
            Drag Shield to look around
          </p>
          <button
            type="button"
            className={styles.dragHintClose}
            onClick={dismissDragHint}
            aria-label="Dismiss hint"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
