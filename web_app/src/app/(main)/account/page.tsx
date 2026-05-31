'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/services/AuthContext';
import styles from '../main.module.css';

export default function AccountPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, updateProfile, deleteAccount, logout } =
    useAuth();

  const [email, setEmail] = useState('');
  const [language, setLanguage] = useState('en');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (user) {
      setEmail(user.email);
      setLanguage(user.language_preference);
    }
  }, [user]);

  if (isLoading || !user) {
    return (
      <div className={styles.loadingWrap}>
        <div className={styles.typing}>
          <div className={styles.typingDot} />
          <div className={styles.typingDot} />
          <div className={styles.typingDot} />
        </div>
      </div>
    );
  }

  const onSave = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setBusy(true);
    try {
      const updates: Parameters<typeof updateProfile>[0] = {
        email: email !== user.email ? email : undefined,
        language_preference: language,
      };
      if (newPassword) {
        updates.current_password = currentPassword;
        updates.new_password = newPassword;
      }
      await updateProfile(updates);
      setMessage('Profile saved successfully.');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Update failed.');
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async () => {
    if (!confirm('Deactivate your account? You will not be able to sign in again.')) {
      return;
    }
    setBusy(true);
    try {
      await deleteAccount();
      logout();
      router.replace('/login');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Delete failed.');
      setBusy(false);
    }
  };

  return (
    <>
      <header className={styles.topBar}>
        <div className={styles.topAccent} aria-hidden />
        <div className={styles.brand}>
          <span className={styles.brandKicker}>Account settings</span>
          <h1 className={styles.brandTitle}>DriveLegal</h1>
        </div>
        <button className={styles.iconBtn} type="button" onClick={() => router.push('/')}>
          Back to chat
        </button>
      </header>

      <div className={styles.accountWrap}>
        <div className={styles.accountCard}>
          <h2>Your account</h2>
          <p className={styles.accountMeta}>
            User ID <code>{user.id}</code>
          </p>
          {message && <p className={styles.accountSuccess}>{message}</p>}
          {error && <p className={styles.accountError}>{error}</p>}
          <form onSubmit={onSave} className={styles.accountForm}>
            <label>
              Email
              <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
            </label>
            <label>
              Language
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
              </select>
            </label>
            <label>
              Current password (only if changing password)
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
              />
            </label>
            <label>
              New password
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={8}
                autoComplete="new-password"
              />
            </label>
            <button type="submit" className={styles.accountSubmit} disabled={busy}>
              Save changes
            </button>
          </form>
          <button type="button" className={styles.accountDelete} onClick={onDelete} disabled={busy}>
            Deactivate account
          </button>
        </div>
      </div>
    </>
  );
}
