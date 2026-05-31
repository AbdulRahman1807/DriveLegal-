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
    rec.continuous = true;       // keep session alive across natural pauses
    rec.interimResults = false;  // only fire onresult on finalised utterances
    rec.lang = 'en-IN';

    rec.onresult = (event: SpeechRecognitionEvent) => {
      // Concatenate all results — event.results accumulates across the session.
      let transcript = '';
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript.trim()) {
        onTranscriptionRef.current(transcript.trim());
      }
      // Do NOT stop recording here — session continues until user clicks Stop.
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

    return () => {
      rec.onresult = null;
      rec.onerror = null;
      rec.onend = null;
      rec.abort();
    };
  }, []);

  const toggleRecording = () => {
    const rec = recognitionRef.current;
    if (!rec) {
      alert('Voice input is not supported in this browser. Try Chrome or Safari.');
      return;
    }

    if (isRecording) {
      try {
        rec.stop();
        // setIsRecording(false) called by onend once browser confirms stop.
      } catch (e) {
        console.error('Failed to stop recognition', e);
        setIsRecording(false);
        onRecordingChangeRef.current?.(false);
      }
      return;
    }

    try {
      rec.start();
      setIsRecording(true);
      onRecordingChangeRef.current?.(true);
    } catch (e) {
      console.error('Failed to start recognition', e);
    }
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
