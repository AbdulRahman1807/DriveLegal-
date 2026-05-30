"use client";

import { useState, useRef, useEffect } from 'react';
import { Send, ShieldAlert, BookOpen, AlertTriangle } from 'lucide-react';
import { ApiService, ChatMessage } from '@/services/api';
import { v4 as uuidv4 } from 'uuid';
import TicketUploader from '../components/TicketUploader';
import VoiceInput from '../components/VoiceInput';

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userQuery = input.trim();
    setInput('');
    
    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      id: uuidv4(),
      text: userQuery,
      isUser: true,
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    abortControllerRef.current = new AbortController();

    try {
      // Call Backend
      const botResponse = await ApiService.sendMessage(userQuery, abortControllerRef.current.signal);
      
      setMessages(prev => [...prev, botResponse]);
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        setMessages(prev => [...prev, {
          id: uuidv4(),
          text: "An error occurred.",
          isUser: false
        }]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceInput = (text: string) => {
    setInput(text);
  };

  const handleTicketAnalysis = (generatedPrompt: string) => {
    // We could immediately send it, or populate the input field. 
    // Let's populate the input field so the user can see what's being sent.
    setInput(generatedPrompt);
  };

  return (
    <main className="chat-window glass-panel">
      {messages.length === 0 ? (
        <div style={{ margin: 'auto', textAlign: 'center', opacity: 0.7 }}>
          <ShieldAlert size={48} style={{ margin: '0 auto 1rem', color: 'var(--primary)' }} />
          <h2>Welcome to DriveLegal</h2>
          <p>Ask me anything about Indian Traffic Laws, fines, or driving regulations.</p>
        </div>
      ) : (
        messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.isUser ? 'user' : 'bot'}`}>
            <div className={`message ${msg.isUser ? 'user' : 'bot'}`}>
              <p>{msg.text}</p>
              
              {!msg.isUser && msg.fines && msg.fines.length > 0 && (
                <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', borderLeft: '3px solid var(--secondary)', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--secondary)', fontWeight: 600, marginBottom: '0.5rem' }}>
                    <AlertTriangle size={16} /> Applicable Fines
                  </div>
                  {msg.fines.map((f, i) => (
                    <div key={i} style={{ fontSize: '0.85rem' }}>
                      • {f.violation_name}: ₹{f.total_fine} ({f.jurisdiction_name})
                    </div>
                  ))}
                </div>
              )}

              {!msg.isUser && msg.citations && msg.citations.length > 0 && (
                <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a1a1aa', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                    <BookOpen size={14} /> Legal Citations
                  </div>
                  {msg.citations.map((c, i) => (
                    <div key={i} style={{ fontSize: '0.8rem', color: '#d4d4d8' }}>
                      [{c.act_name} - Section {c.section}]
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))
      )}

      {isLoading && (
        <div className="message-wrapper bot">
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />

      <div className="input-area">
        <div className="flex space-x-3 items-end">
          <TicketUploader onAnalysisComplete={handleTicketAnalysis} />
          <VoiceInput onTranscription={handleVoiceInput} />
          
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Indian traffic laws, fines, or upload a ticket..."
            className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#7FFFD4]/50 resize-none max-h-32"
            rows={input.split('\n').length > 1 ? Math.min(input.split('\n').length, 4) : 1}
          />
          <button 
            className="send-button"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </main>
  );
}
