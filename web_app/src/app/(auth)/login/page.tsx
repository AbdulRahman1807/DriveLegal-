'use client';

import { useState, useEffect, useMemo, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/services/AuthContext';
import ShieldAvatar from '@/components/ShieldAvatar';
import DriveLegalSimulator from '@/components/DriveLegalSimulator';
import styles from './auth.module.css';

type AuthMode = 'signup' | 'signin';
type FocusField = 'email' | 'password' | 'none';

export default function LoginPage() {
  const router = useRouter();
  const { login, register, isAuthenticated, isLoading } = useAuth();

  const [mode, setMode] = useState<AuthMode>('signin');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreePolicy, setAgreePolicy] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [focusField, setFocusField] = useState<FocusField>('none');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [roadComment, setRoadComment] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/');
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!roadComment) return undefined;
    const timer = window.setTimeout(() => setRoadComment(null), 4500);
    return () => window.clearTimeout(timer);
  }, [roadComment]);

  const shieldSpeech = useMemo(() => {
    if (focusField === 'email') {
      return 'Enter your registered email.';
    }
    if (focusField === 'password') {
      return mode === 'signup'
        ? 'Use at least 8 characters for a strong password.'
        : 'Your account is protected.';
    }
    if (roadComment) {
      return roadComment;
    }
    if (mode === 'signup') {
      return "Let's get you set up — I'll help with traffic laws from day one.";
    }
    return 'Ready to help you drive legally.';
  }, [focusField, mode, roadComment]);

  if (isLoading || isAuthenticated) {
    return null;
  }

  const switchMode = (next: AuthMode) => {
    setMode(next);
    setPassword('');
    setConfirmPassword('');
    setError('');
    setFocusField('none');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    const isRegister = mode === 'signup';

    if (isRegister) {
      if (!agreePolicy) {
        setError('Please agree to the privacy policy.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
      if (password.length < 8) {
        setError('Password must be at least 8 characters.');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      const trimmedEmail = email.trim();
      if (isRegister) {
        await register(trimmedEmail, password);
      } else {
        await login(trimmedEmail, password);
      }
      router.replace('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSignup = mode === 'signup';

  return (
    <div className={styles.shell}>
      <aside className={styles.heroSide} aria-label="DriveLegal and Shield">
        <div className={styles.heroGlow} aria-hidden />
        <div className={styles.roadSceneWrap}>
          <DriveLegalSimulator variant="hero" />
        </div>

        <div className={styles.heroInner}>
          <div className={styles.heroContent}>
            <p className={styles.heroBrand}>DriveLegal</p>
            <p className={styles.heroTagline}>Know the law before you pay the fine.</p>
            <p className={styles.heroSub}>India&apos;s AI-powered traffic law assistant.</p>

            <div className={styles.heroPitch}>
              <p className={styles.heroQuote}>Ready to help you drive legally.</p>
              <ul className={styles.heroList}>
                <li>Know your rights.</li>
                <li>Know your fines.</li>
                <li>Drive safely.</li>
              </ul>
            </div>
          </div>

          <div className={styles.mascotBlock}>
            <div className={styles.mascotWrap}>
              <ShieldAvatar
                size="auth"
                isTalking={focusField !== 'none' || Boolean(roadComment)}
                showDragHint
              />
            </div>
            <div className={styles.speechBubble} key={roadComment ?? shieldSpeech}>
              <p>
                <span className={styles.speechName}>Shield</span>
                {roadComment && roadComment.includes('. ') ? (
                  <>
                    {' — '}
                    {roadComment.split('. ')[0]}.
                    <span className={styles.speechSub}>
                      {roadComment.split('. ').slice(1).join('. ')}
                    </span>
                  </>
                ) : (
                  <> — {shieldSpeech}</>
                )}
              </p>
            </div>
          </div>
        </div>
      </aside>

      <main className={styles.formSide}>
        <div className={styles.formCard}>
          <div className={styles.modeTabs}>
            <button
              type="button"
              className={`${styles.modeTab} ${!isSignup ? styles.modeTabActive : ''}`}
              onClick={() => switchMode('signin')}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`${styles.modeTab} ${isSignup ? styles.modeTabActive : ''}`}
              onClick={() => switchMode('signup')}
            >
              Sign Up
            </button>
          </div>

          <h2 className={styles.formHeading}>
            {isSignup ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className={styles.formLead}>
            Shield is ready to assist you with traffic laws, challans, vehicle documents,
            and road safety guidance.
          </p>

          {error && <div className={styles.error}>{error}</div>}

          <form className={styles.formFields} onSubmit={handleSubmit}>
            {isSignup && (
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel} htmlFor="fullName">
                  Full Name
                </label>
                <input
                  id="fullName"
                  type="text"
                  className={styles.fieldInput}
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                />
              </div>
            )}

            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel} htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                className={styles.fieldInput}
                placeholder="you@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={() => setFocusField('email')}
                onBlur={() => setFocusField('none')}
                required
                autoComplete="email"
              />
            </div>

            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel} htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className={styles.fieldInput}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => setFocusField('password')}
                onBlur={() => setFocusField('none')}
                required
                minLength={isSignup ? 8 : undefined}
                autoComplete={isSignup ? 'new-password' : 'current-password'}
              />
            </div>

            {isSignup && (
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel} htmlFor="confirmPassword">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  className={styles.fieldInput}
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  onFocus={() => setFocusField('password')}
                  onBlur={() => setFocusField('none')}
                  required
                  autoComplete="new-password"
                />
              </div>
            )}

            {isSignup ? (
              <label className={styles.checkboxRow}>
                <input
                  type="checkbox"
                  checked={agreePolicy}
                  onChange={(e) => setAgreePolicy(e.target.checked)}
                />
                I agree to the privacy policy and terms of use
              </label>
            ) : (
              <div className={styles.rememberRow}>
                <label>
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  Remember me
                </label>
                <span className={styles.forgotLink}>Forgot password?</span>
              </div>
            )}

            <button type="submit" className={styles.submitBtn} disabled={isSubmitting}>
              {isSubmitting ? (
                <span className={styles.spinner} />
              ) : isSignup ? (
                'Create Account'
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className={styles.switchText}>
            {isSignup ? 'Already have an account? ' : "Don't have an account? "}
            <button
              type="button"
              className={styles.switchLink}
              onClick={() => switchMode(isSignup ? 'signin' : 'signup')}
            >
              {isSignup ? 'Sign in' : 'Sign up'}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}
