"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Send,
  BookOpen,
  AlertTriangle,
  LogOut,
  Settings,
  MapPin,
  ShieldCheck,
  Lightbulb,
  HardHat,
  FileText,
  Gauge,
  Wine,
} from 'lucide-react';
import { ApiService, ChatMessage, SHIELD_UNAVAILABLE } from '@/services/api';
import { useAuth } from '@/services/AuthContext';
import { v4 as uuidv4 } from 'uuid';
import TicketUploader from '@/components/TicketUploader';
import VoiceInput from '@/components/VoiceInput';
import ShieldMascot from '@/components/ShieldMascot';
import ShieldAvatar from '@/components/ShieldAvatar';
import CitationChip from '@/components/CitationChip';
import DriveLegalSimulator from '@/components/DriveLegalSimulator';
import ChallanCalculator from '@/components/ChallanCalculator';
import styles from './main.module.css';

const QUICK_TOPICS = [
  { Icon: HardHat, label: 'Helmet', query: 'What is the fine for riding without a helmet in India?' },
  { Icon: FileText, label: 'Documents', query: 'What documents should I carry while driving?' },
  { Icon: Gauge, label: 'Speed', query: 'What are the speed limits and fines for overspeeding?' },
  { Icon: Wine, label: 'Alcohol', query: 'What is the penalty for drunk driving under Section 185?' },
] as const;

const POPULAR_QUESTIONS = [
  'What documents should I carry?',
  'Fine for riding without helmet?',
  'Can I use DigiLocker?',
  'What is Section 185?',
] as const;

function firstNameFromEmail(email?: string) {
  if (!email) return 'there';
  const local = email.split('@')[0] ?? 'there';
  return local.charAt(0).toUpperCase() + local.slice(1);
}

function truncateSpeech(text: string, max = 140) {
  const clean = text.replace(/\s+/g, ' ').trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max).trim()}…`;
}

export default function Home() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();

  const [activeView, setActiveView] = useState<'chat' | 'calculator'>('chat');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const userName = firstNameFromEmail(user?.email);
  const hasStartedChat = messages.length > 0;

  const lastBotMessage = useMemo(
    () => [...messages].reverse().find((m) => !m.isUser),
    [messages],
  );

  const mascotSpeech = useMemo(() => {
    if (isListening) return "I'm listening… go ahead and ask your question.";
    if (isLoading) return 'Let me check the Motor Vehicles Act for you…';
    if (lastBotMessage?.text) return truncateSpeech(lastBotMessage.text);
    if (messages.some((m) => m.isUser)) return 'Searching Indian traffic laws…';
    return '';
  }, [isListening, isLoading, lastBotMessage, messages]);

  const mascotTalking = isLoading || isListening || Boolean(lastBotMessage);
  const mascotThinking = isLoading && !isListening;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (hasStartedChat) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, hasStartedChat]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const sendQuery = useCallback(async (userQuery: string) => {
    if (!userQuery.trim() || isLoading) return;
    const trimmed = userQuery.trim();
    setInput('');
    setMessages((prev) => [...prev, { id: uuidv4(), text: trimmed, isUser: true }]);
    setIsLoading(true);
    abortControllerRef.current = new AbortController();
    try {
      const botResponse = await ApiService.sendMessage(
        trimmed,
        abortControllerRef.current.signal,
      );
      setMessages((prev) => [...prev, botResponse]);
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') {
        setMessages((prev) => [
          ...prev,
          { id: uuidv4(), text: SHIELD_UNAVAILABLE, isUser: false, isError: true },
        ]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [isLoading]);

  const handleSend = () => sendQuery(input);

  const handleVoiceTranscription = (text: string) => {
    setInput(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const popularSection = (
    <div className={styles.popularSection}>
      <div className={styles.popularLabel}>
        <Lightbulb size={14} />
        Popular Questions
      </div>
      <div className={styles.popularGrid}>
        {POPULAR_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            className={styles.popularChip}
            onClick={() => sendQuery(q)}
            disabled={isLoading}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );

  const inputBox = (
    <div className={styles.inputDock}>
      <div className={styles.inputRow}>
        <VoiceInput
          variant="prominent"
          onTranscription={handleVoiceTranscription}
          onRecordingChange={setIsListening}
          disabled={isLoading}
        />
        <TicketUploader onAnalysisComplete={(prompt) => setInput(prompt)} />
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Shield anything about traffic laws, fines, or challans…"
          className={styles.textarea}
          rows={input.split('\n').length > 1 ? Math.min(input.split('\n').length, 4) : 1}
        />
        <button
          type="button"
          className={styles.sendBtn}
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );

  if (authLoading || !isAuthenticated) {
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

  return (
    <>
      <header className={styles.locationBar}>
        <span className={styles.locationBrand}>DriveLegal</span>
        <div className={styles.locationMeta}>
          <span className={styles.locationItem}>
            <MapPin size={13} />
            Chennai, Tamil Nadu
          </span>
          <span className={styles.locationDivider} aria-hidden />
          <span className={styles.locationItem}>
            <ShieldCheck size={13} />
            Verified Dataset
          </span>
        </div>
        <div className={styles.locationActions}>
          <div className="flex bg-white/5 rounded-lg p-0.5 mr-2">
            <button
              type="button"
              onClick={() => setActiveView('chat')}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${activeView === 'chat' ? 'bg-[#7FFFD4]/20 text-[#7FFFD4]' : 'text-gray-400 hover:text-white'}`}
            >
              AI Chat
            </button>
            <button
              type="button"
              onClick={() => setActiveView('calculator')}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${activeView === 'calculator' ? 'bg-[#7FFFD4]/20 text-[#7FFFD4]' : 'text-gray-400 hover:text-white'}`}
            >
              Fine Calculator
            </button>
          </div>
          <button className={styles.locationBtn} type="button" onClick={() => router.push('/account')} aria-label="Account">
            <Settings size={16} />
          </button>
          <button
            className={styles.locationBtn}
            type="button"
            onClick={() => {
              logout();
              router.replace('/login');
            }}
            aria-label="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {activeView === 'calculator' ? (
        <div className={styles.main} style={{ padding: '1rem' }}>
          <ChallanCalculator />
        </div>
      ) : null}

      <div className={styles.main} style={{ display: activeView === 'calculator' ? 'none' : undefined }}>
        {!hasStartedChat ? (
          <div className={styles.emptyLayout}>
            <div className={styles.heroCard}>
              <div className={styles.heroLeft}>
                <ShieldAvatar
                  size="hero"
                  isTalking={isListening || isLoading}
                  isListening={isListening}
                  isThinking={mascotThinking}
                />
              </div>
              <div className={styles.heroRight}>
                <h2 className={styles.heroGreeting}>
                  Hi {userName}
                </h2>
                <p className={styles.heroLead}>
                  Ask me about traffic laws, fines, challans and required documents.
                </p>
                <div className={styles.topicGrid}>
                  {QUICK_TOPICS.map((topic) => (
                    <button
                      key={topic.label}
                      type="button"
                      className={styles.topicBtn}
                      onClick={() => sendQuery(topic.query)}
                      disabled={isLoading}
                    >
                      <topic.Icon size={15} strokeWidth={2} aria-hidden />
                      {topic.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {inputBox}
            {popularSection}
          </div>
        ) : (
          <div className={styles.chatView}>
            <ShieldMascot
              variant="compact"
              userName={userName}
              speech={mascotSpeech}
              isTalking={mascotTalking}
              isListening={isListening}
              typewriter={Boolean(lastBotMessage && !isLoading && !isListening && !lastBotMessage.isError)}
              isThinking={mascotThinking}
            />

            <div className={styles.messagesArea}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`${styles.messageRow} ${msg.isUser ? styles.messageRowUser : styles.messageRowBot}`}
                >
                  <div
                    className={`${styles.bubble} ${msg.isUser ? styles.bubbleUser : styles.bubbleBot} ${msg.isError ? styles.bubbleError : ''}`}
                  >
                    <p>{msg.text}</p>
                    {!msg.isUser && !msg.isError && msg.fines && msg.fines.length > 0 && (
                      <div className={styles.fineBlock}>
                        <div className={styles.fineTitle}>
                          <AlertTriangle size={16} /> Applicable Fines
                        </div>
                        {msg.fines.map((f, i) => (
                          <div key={i}>
                            • {f.violation_name}: ₹{f.total_fine} ({f.jurisdiction_name})
                          </div>
                        ))}
                      </div>
                    )}
                    {!msg.isUser && !msg.isError && msg.citations && msg.citations.length > 0 && (
                      <div className={styles.citationBlock}>
                        <div className={styles.citationTitle}>
                          <BookOpen size={14} /> Legal Citations
                        </div>
                        <div className={styles.citationList}>
                          {msg.citations.map((c, i) => (
                            <CitationChip key={c.id ?? `${c.act_name}-${c.section}-${i}`} citation={c} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className={`${styles.messageRow} ${styles.messageRowBot}`}>
                  <div className={styles.typing}>
                    <div className={styles.typingDot} />
                    <div className={styles.typingDot} />
                    <div className={styles.typingDot} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {inputBox}
            {popularSection}
          </div>
        )}
      </div>

      <footer className={styles.simFooter} aria-label="Road safety simulation">
        <DriveLegalSimulator variant="footer" />
      </footer>
    </>
  );
}
