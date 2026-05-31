"use client";

import { useState, useEffect } from 'react';
import { Calculator, AlertCircle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'drivelegal-secret-dev-key';

interface Violation {
  id: string;
  violation_code: string;
  name: string;
}

interface Jurisdiction {
  id: string;
  name: string;
  type: string;
}

interface FineResult {
  violation_name: string;
  vehicle_category: string;
  base_fine: number;
  surcharges: number;
  total_fine: number;
  imprisonment_months: number | null;
  license_suspension_months: number | null;
  compoundable: boolean;
  jurisdiction_name: string;
  legal_section_id: string;
}

export default function ChallanCalculator() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [selectedViolation, setSelectedViolation] = useState('');
  const [selectedJurisdiction, setSelectedJurisdiction] = useState('');
  const [vehicleCategory, setVehicleCategory] = useState('ALL');
  const [isRepeat, setIsRepeat] = useState(false);
  const [results, setResults] = useState<FineResult[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const res = await fetch(`${API_BASE}/calculator/metadata`, {
          headers: { 'Authorization': `Bearer ${API_KEY}` }
        });
        if (!res.ok) throw new Error('Failed to load calculator data.');
        const data = await res.json();
        setViolations(data.violations);
        setJurisdictions(data.jurisdictions);
        if (data.violations.length > 0) setSelectedViolation(data.violations[0].id);
        if (data.jurisdictions.length > 0) setSelectedJurisdiction(data.jurisdictions[0].id);
      } catch (err: any) {
        setError(err.message);
      }
    };
    fetchMetadata();
  }, []);

  const handleCalculate = async () => {
    if (!selectedViolation || !selectedJurisdiction) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/calculator/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${API_KEY}` },
        body: JSON.stringify({
          violation_id: selectedViolation,
          jurisdiction_id: selectedJurisdiction,
          vehicle_category: vehicleCategory,
          is_repeat_offence: isRepeat
        })
      });
      if (!res.ok) throw new Error('Failed to calculate fine.');
      setResults(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#1a1a1a] rounded-xl p-6 overflow-y-auto">
      <div className="flex items-center gap-2 mb-6 text-[#7FFFD4]">
        <Calculator size={24} />
        <h2 className="text-xl font-bold">Traffic Fine Calculator</h2>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded mb-4 flex items-center gap-2">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Violation</label>
          <select value={selectedViolation} onChange={e => setSelectedViolation(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-[#7FFFD4]">
            {violations.map(v => <option key={v.id} value={v.id} className="bg-gray-800">{v.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Jurisdiction</label>
          <select value={selectedJurisdiction} onChange={e => setSelectedJurisdiction(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-[#7FFFD4]">
            {jurisdictions.map(j => <option key={j.id} value={j.id} className="bg-gray-800">{j.name} ({j.type})</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Vehicle Category</label>
            <select value={vehicleCategory} onChange={e => setVehicleCategory(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-[#7FFFD4]">
              <option value="ALL" className="bg-gray-800">All Vehicles</option>
              <option value="2W" className="bg-gray-800">Two Wheeler (2W)</option>
              <option value="LMV" className="bg-gray-800">Light Motor Vehicle</option>
              <option value="HMV" className="bg-gray-800">Heavy Motor Vehicle</option>
            </select>
          </div>
          <div className="flex items-center mt-6">
            <label className="flex items-center cursor-pointer">
              <input type="checkbox" checked={isRepeat} onChange={e => setIsRepeat(e.target.checked)}
                className="w-5 h-5 rounded border-white/10 bg-white/5 text-[#7FFFD4]" />
              <span className="ml-2 text-sm text-gray-300">Repeat Offence</span>
            </label>
          </div>
        </div>

        <button onClick={handleCalculate} disabled={isLoading || !selectedViolation || !selectedJurisdiction}
          className="w-full py-3 mt-4 bg-[#7FFFD4]/10 hover:bg-[#7FFFD4]/20 text-[#7FFFD4] border border-[#7FFFD4]/30 rounded-lg font-medium transition-colors disabled:opacity-50">
          {isLoading ? 'Calculating…' : 'Calculate Fine'}
        </button>
      </div>

      {results && (
        <div className="mt-4 border-t border-white/10 pt-6">
          <h3 className="text-lg font-medium text-white mb-4">Results</h3>
          {results.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No specific fines found for this combination.</p>
          ) : (
            <div className="space-y-4">
              {results.map((r, idx) => (
                <div key={idx} className="bg-white/5 border border-white/10 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-[#7FFFD4]">{r.violation_name}</h4>
                    <span className="text-xs px-2 py-1 bg-white/10 rounded-full text-gray-300">{r.jurisdiction_name}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-y-2 mt-4 text-sm">
                    <div className="text-gray-400">Base Fine:</div>
                    <div className="text-right font-mono">₹{r.base_fine}</div>
                    <div className="text-gray-400">Surcharges:</div>
                    <div className="text-right font-mono">₹{r.surcharges}</div>
                    <div className="text-gray-300 font-bold border-t border-white/10 pt-2 mt-1">Total Fine:</div>
                    <div className="text-right font-bold text-red-400 font-mono border-t border-white/10 pt-2 mt-1">₹{r.total_fine}</div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-white/10 text-xs text-gray-500">
                    {r.imprisonment_months && <div>Imprisonment: Up to {r.imprisonment_months} months</div>}
                    {r.license_suspension_months && <div>License Suspension: {r.license_suspension_months} months</div>}
                    <div>Compoundable: {r.compoundable ? 'Yes' : 'No'}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
