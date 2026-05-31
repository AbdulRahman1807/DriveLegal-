import React, { useRef, useState } from 'react';

interface TicketAnalysisResult {
  extracted_text: string;
  inferred_violation: string;
  detected_fine: number;
  confidence: number;
}

interface TicketUploaderProps {
  onAnalysisComplete: (text: string) => void;
}

export default function TicketUploader({ onAnalysisComplete }: TicketUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setError("File is too large. Max 5MB.");
      return;
    }

    setIsScanning(true);
    setError(null);

    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64String = (reader.result as string).split(',')[1];
        
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        
        // BUG-U1: Add AbortController for timeout to prevent infinite UI lock
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout
        
        try {
          const res = await fetch(`${baseUrl}/analyze_ticket`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer drivelegal-secret-dev-key' // Should come from env in prod
            },
            body: JSON.stringify({
              image_base64: base64String,
              mime_type: file.type
            }),
            signal: controller.signal
          });

          clearTimeout(timeoutId);

          if (!res.ok) {
            throw new Error(`Failed to scan ticket: ${res.statusText}`);
          }

          const data: TicketAnalysisResult = await res.json();
          
          // Convert the structured result into a prompt for the main chat UI
          const generatedPrompt = `I received a ticket. The scanner extracted this text: "${data.extracted_text}". It thinks the violation is ${data.inferred_violation} with a fine of ₹${data.detected_fine}. Can you confirm if this is correct under the law?`;
          
          onAnalysisComplete(generatedPrompt);
        } catch (innerErr: any) {
          setError(innerErr.message || "An error occurred during scanning.");
          setIsScanning(false);
          if (fileInputRef.current) fileInputRef.current.value = "";
        }
      };
      reader.readAsDataURL(file);
    } catch (err: any) {
      setError(err.message || "An error occurred during scanning.");
    } finally {
      setIsScanning(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <input 
        type="file" 
        accept="image/*" 
        className="hidden" 
        ref={fileInputRef} 
        onChange={handleFileChange}
        disabled={isScanning} // Prevent consecutive uploads race condition
      />
      <button 
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={isScanning}
        className="p-2 text-gray-400 hover:text-white bg-white/5 rounded-full hover:bg-white/10 transition-all border border-white/10"
        title="Upload e-Challan"
      >
        {isScanning ? (
          <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
        )}
      </button>
      {error && <span className="text-red-400 text-xs absolute -mt-8">{error}</span>}
    </div>
  );
}
