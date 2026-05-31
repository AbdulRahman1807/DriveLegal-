'use client';

import { useEffect, useRef, useState } from 'react';
import { Mic, MicOff } from 'lucide-react';
import styles from './VoiceInput.module.css';

interface VoiceInputProps {
  onTranscription: (text: string) => void;
  onRecordingChange?: (recording: boolean) => void;
  variant?: 'icon' | 'prominent';
  disabled?: boolean;
}

export default function VoiceInput({
  onTranscription,
  onRecordingChange,
  variant = 'icon',
  disabled = false,
}: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const onTranscriptionRef = useRef(onTranscription);
  const onRecordingChangeRef = useRef(onRecordingChange);

  useEffect(() => {
    onTranscriptionRef.current = onTranscription;
    onRecordingChangeRef.current = onRecordingChange;
  }, [onTranscription, onRecordingChange]);

  useEffect(() => {
    const SpeechRecognitionCtor =
      window.SpeechRecognition || (window as unknown as { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      setSupported(false);
      return;
    }

    const rec = new SpeechRecognitionCtor();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = 'en-IN';

    rec.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) {
        onTranscriptionRef.current(transcript);
      }
      setIsRecording(false);
      onRecordingChangeRef.current?.(false);
    };

    rec.onerror = () => {
      setIsRecording(false);
      onRecordingChangeRef.current?.(false);
    };

    rec.onend = () => {
      setIsRecording(false);
      onRecordingChangeRef.current?.(false);
    };

    recognitionRef.current = rec;
  }, []);

  const toggleRecording = () => {
    const rec = recognitionRef.current;
    if (!rec) {
      alert('Voice input is not supported in this browser. Try Chrome or Safari.');
      return;
    }

    if (isRecording) {
      rec.stop();
      setIsRecording(false);
      onRecordingChangeRef.current?.(false);
      return;
    }

    rec.start();
    setIsRecording(true);
    onRecordingChangeRef.current?.(true);
  };

  if (variant === 'prominent') {
    return (
      <button
        type="button"
        onClick={toggleRecording}
        disabled={disabled || !supported}
        className={`${styles.prominentBtn} ${isRecording ? styles.prominentActive : ''}`}
        title={supported ? (isRecording ? 'Stop listening' : 'Talk to Shield') : 'Voice requires Chrome or Safari'}
        aria-pressed={isRecording}
      >
        {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
        <span>{isRecording ? 'Listening…' : 'Ask Shield'}</span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleRecording}
      disabled={disabled || !supported}
      className={`${styles.iconBtn} ${isRecording ? styles.iconActive : ''}`}
      title={supported ? (isRecording ? 'Stop recording' : 'Voice input') : 'Voice requires Chrome or Safari'}
      aria-pressed={isRecording}
    >
      <Mic size={20} />
    </button>
  );
}
