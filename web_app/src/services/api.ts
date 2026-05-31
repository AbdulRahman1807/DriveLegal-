import { v4 as uuidv4 } from 'uuid';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  isError?: boolean;
  citations?: Citation[];
  fines?: Array<{
    violation_name: string;
    total_fine: number;
    jurisdiction_name: string;
  }>;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Citation {
  id?: string;
  act_name: string;
  section: string;
  clause?: string;
  relevance_score?: number;
  brief?: string;
  chapter?: string;
  source_url?: string;
  full_text?: string;
}

export interface LegalSectionDetail {
  id: string;
  act_name: string;
  section_number: string;
  chapter?: string;
  clause?: string;
  explanation_text?: string;
  full_text: string;
  source_url?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  language_preference: string;
  is_active: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Token helpers (localStorage)
// ---------------------------------------------------------------------------
const TOKEN_KEYS = {
  access: 'drivelegal_access_token',
  refresh: 'drivelegal_refresh_token',
} as const;

function getStoredToken(key: keyof typeof TOKEN_KEYS): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEYS[key]);
}

function storeTokens(tokens: TokenResponse) {
  localStorage.setItem(TOKEN_KEYS.access, tokens.access_token);
  localStorage.setItem(TOKEN_KEYS.refresh, tokens.refresh_token);
}

function clearTokens() {
  localStorage.removeItem(TOKEN_KEYS.access);
  localStorage.removeItem(TOKEN_KEYS.refresh);
  localStorage.removeItem('drivelegal_session_id');
}

function parseApiError(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) =>
        typeof item === 'object' && item && 'msg' in item
          ? String((item as { msg: string }).msg)
          : String(item),
      )
      .join(', ');
  }
  return fallback;
}

export const SHIELD_UNAVAILABLE =
  '⚠️ Shield is temporarily unavailable. Please try again in a few moments.';

export function sanitizeBotReply(text: string): string {
  if (
    /error occurred|LLM provider|communicating with the backend|Server error|Session expired/i.test(
      text,
    )
  ) {
    return SHIELD_UNAVAILABLE;
  }
  return text;
}

// ---------------------------------------------------------------------------
// Auth Service
// ---------------------------------------------------------------------------
export class AuthService {
  private static readonly BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

  static async register(
    email: string,
    password: string,
    language_preference = 'en',
  ): Promise<TokenResponse> {
    const res = await fetch(`${this.BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, language_preference }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(parseApiError(body, `Registration failed (${res.status})`));
    }

    const tokens: TokenResponse = await res.json();
    storeTokens(tokens);
    return tokens;
  }

  static async login(email: string, password: string): Promise<TokenResponse> {
    const res = await fetch(`${this.BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(parseApiError(body, `Login failed (${res.status})`));
    }

    const tokens: TokenResponse = await res.json();
    storeTokens(tokens);
    return tokens;
  }

  static async refresh(): Promise<TokenResponse | null> {
    const refreshToken = getStoredToken('refresh');
    if (!refreshToken) return null;

    const res = await fetch(`${this.BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      clearTokens();
      return null;
    }

    const tokens: TokenResponse = await res.json();
    storeTokens(tokens);
    return tokens;
  }

  static async getProfile(): Promise<UserProfile | null> {
    const token = getStoredToken('access');
    if (!token) return null;

    const res = await fetch(`${this.BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) return null;
    return res.json();
  }

  static getAccessToken(): string | null {
    return getStoredToken('access');
  }

  static async updateProfile(updates: {
    email?: string;
    language_preference?: string;
    current_password?: string;
    new_password?: string;
  }): Promise<UserProfile> {
    const token = getStoredToken('access');
    if (!token) throw new Error('Not authenticated.');

    const res = await fetch(`${this.BASE_URL}/auth/me`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(parseApiError(body, `Update failed (${res.status})`));
    }
    return res.json();
  }

  static async deleteAccount(): Promise<void> {
    const token = getStoredToken('access');
    if (!token) throw new Error('Not authenticated.');

    const res = await fetch(`${this.BASE_URL}/auth/me`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(parseApiError(body, `Delete failed (${res.status})`));
    }
    clearTokens();
  }

  static logout() {
    clearTokens();
  }

  static isLoggedIn(): boolean {
    return !!getStoredToken('access');
  }
}

// ---------------------------------------------------------------------------
// Chat / API Service
// ---------------------------------------------------------------------------
export class ApiService {
  private static readonly BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

  static getSessionId(): string {
    if (typeof window === 'undefined') return '';
    let sessionId = localStorage.getItem('drivelegal_session_id');
    if (!sessionId) {
      sessionId = uuidv4();
      localStorage.setItem('drivelegal_session_id', sessionId);
    }
    return sessionId;
  }

  static async sendMessage(
    query: string,
    signal?: AbortSignal,
  ): Promise<ChatMessage> {
    const sessionId = this.getSessionId();
    const token = AuthService.getAccessToken();

    try {
      const response = await fetch(`${this.BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query,
          session_id: sessionId,
        }),
        signal,
      });

      if (response.status === 401) {
        // Try refreshing the token once
        const refreshed = await AuthService.refresh();
        if (refreshed) {
          // Retry with new token
          const retryRes = await fetch(`${this.BASE_URL}/chat`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${refreshed.access_token}`,
            },
            body: JSON.stringify({ query, session_id: sessionId }),
            signal,
          });

          if (!retryRes.ok)
            throw new Error(`Server error: ${retryRes.status}`);
          const data = await retryRes.json();
          return {
            id: uuidv4(),
            text: sanitizeBotReply(data.reply),
            isUser: false,
            citations: data.citations,
            fines: data.fines,
          };
        }

        // Refresh also failed — force logout
        AuthService.logout();
        throw new Error('Session expired. Please log in again.');
      }

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      return {
        id: uuidv4(),
        text: sanitizeBotReply(data.reply),
        isUser: false,
        citations: data.citations,
        fines: data.fines,
      };
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw error;
      }
      return {
        id: uuidv4(),
        text: SHIELD_UNAVAILABLE,
        isUser: false,
        isError: true,
      };
    }
  }

  private static authHeaders(): Record<string, string> {
    const token = AuthService.getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  static async getLegalSection(sectionId: string): Promise<LegalSectionDetail> {
    const res = await fetch(`${this.BASE_URL}/legal_sections/${sectionId}`, {
      headers: this.authHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(parseApiError(body, `Section not found (${res.status})`));
    }
    return res.json();
  }

  static async lookupLegalSection(
    actName: string,
    section: string,
  ): Promise<LegalSectionDetail> {
    const params = new URLSearchParams({ act_name: actName, section });
    const res = await fetch(`${this.BASE_URL}/legal_sections/lookup?${params}`, {
      headers: this.authHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(parseApiError(body, `Section not found (${res.status})`));
    }
    return res.json();
  }
}
