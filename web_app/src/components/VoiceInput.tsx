import React, { useState, useEffect, useRef } from 'react';

interface VoiceInputProps {
  onTranscription: (text: string) => void;
}

export default function VoiceInput({ onTranscription }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  // Holds the latest callback without being a dep — prevents the recognition
  // object from being torn down on every parent re-render.
  const onTranscriptionRef = useRef(onTranscription);

  useEffect(() => {
    onTranscriptionRef.current = onTranscription;
  });

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const rec = new SpeechRecognition();
    rec.continuous = true;       // keep session alive across natural pauses
    rec.interimResults = false;  // only fire onresult on finalised utterances
    rec.lang = 'en-IN';

    rec.onresult = (event: any) => {
      // With interimResults=false every entry in event.results is final.
      // Concatenate all results so the field reflects the full session so far.
      let transcript = '';
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      onTranscriptionRef.current(transcript.trim());
    };

    rec.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      setIsRecording(false);
    };

    rec.onend = () => {
      setIsRecording(false);
    };

    setRecognition(rec);

    // Null handlers before aborting so no callbacks fire on an unmounted component.
    return () => {
      rec.onresult = null;
      rec.onerror = null;
      rec.onend = null;
      rec.abort();
    };
  }, []); // runs once — onTranscription is accessed via ref

  const toggleRecording = () => {
    if (!recognition) {
      alert('Voice input is not supported in this browser.');
      return;
    }

    if (isRecording) {
      try {
        recognition.stop();
        // setIsRecording(false) is called by onend once the browser confirms stop.
      } catch (e) {
        console.error('Failed to stop recognition', e);
        setIsRecording(false);
      }
    } else {
      try {
        recognition.start();
        setIsRecording(true);
      } catch (e) {
        console.error('Failed to start recognition', e);
      }
    }
  };

  if (!recognition) {
    // BUG-U2: Provide fallback UX instead of disappearing silently
    return (
      <button
        type="button"
        disabled
        className="p-2 rounded-full transition-all border bg-gray-500/10 text-gray-600 border-gray-500/20 cursor-not-allowed"
        title="Voice input requires Chrome or Safari."
      >
        <svg className="w-5 h-5 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          <line x1="4" y1="4" x2="20" y2="20" strokeWidth={2} />
        </svg>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleRecording}
      className={`p-2 rounded-full transition-all border ${
        isRecording
          ? 'bg-red-500/20 text-red-400 border-red-500/50 animate-pulse'
          : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10 hover:text-white'
      }`}
      title={isRecording ? "Stop Recording" : "Start Voice Input"}
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    </button>
  );
}
