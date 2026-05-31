'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { AuthService, type UserProfile } from './api';

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------
interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  updateProfile: (updates: {
    email?: string;
    language_preference?: string;
    current_password?: string;
    new_password?: string;
  }) => Promise<void>;
  deleteAccount: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Try to restore session on mount
  useEffect(() => {
    (async () => {
      try {
        if (AuthService.isLoggedIn()) {
          let profile = await AuthService.getProfile();
          if (!profile) {
            // Access token may be expired — try refresh
            const refreshed = await AuthService.refresh();
            if (refreshed) {
              profile = await AuthService.getProfile();
            }
          }
          setUser(profile);
        }
      } catch {
        // Silent fail — user will see login page
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await AuthService.login(email, password);
    const profile = await AuthService.getProfile();
    setUser(profile);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await AuthService.register(email, password);
    const profile = await AuthService.getProfile();
    setUser(profile);
  }, []);

  const updateProfile = useCallback(
    async (updates: {
      email?: string;
      language_preference?: string;
      current_password?: string;
      new_password?: string;
    }) => {
      const profile = await AuthService.updateProfile(updates);
      setUser(profile);
    },
    [],
  );

  const deleteAccount = useCallback(async () => {
    await AuthService.deleteAccount();
    setUser(null);
  }, []);

  const logout = useCallback(() => {
    AuthService.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        updateProfile,
        deleteAccount,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
