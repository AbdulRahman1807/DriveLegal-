import { v4 as uuidv4 } from 'uuid';

export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  citations?: Array<{
    act_name: string;
    section: string;
  }>;
  fines?: Array<{
    violation_name: string;
    total_fine: number;
    jurisdiction_name: string;
  }>;
}

export class ApiService {
  private static readonly BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
  private static readonly API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'drivelegal-secret-dev-key';

  static getSessionId(): string {
    if (typeof window === 'undefined') return '';
    let sessionId = localStorage.getItem('drivelegal_session_id');
    if (!sessionId) {
      sessionId = uuidv4();
      localStorage.setItem('drivelegal_session_id', sessionId);
    }
    return sessionId;
  }

  static async sendMessage(query: string, signal?: AbortSignal): Promise<ChatMessage> {
    const sessionId = this.getSessionId();
    
    try {
      const response = await fetch(`${this.BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.API_KEY}`,
        },
        body: JSON.stringify({
          query,
          session_id: sessionId,
        }),
        signal,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        id: uuidv4(),
        text: data.reply,
        isUser: false,
        citations: data.citations,
        fines: data.fines,
      };
    } catch (error: any) {
      return {
        id: uuidv4(),
        text: `Error communicating with the backend: ${error.message}. Please make sure the Python API is running.`,
        isUser: false,
      };
    }
  }
}
