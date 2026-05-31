'use client';

import styles from '../RoadSafetySimulator.module.css';

type WheelProps = { cx: number; cy: number; r?: number; spinning?: boolean };

export function Wheel({ cx, cy, r = 7, spinning = true }: WheelProps) {
  return (
    <g
      className={spinning ? styles.wheelSpin : undefined}
      style={{ transformBox: 'fill-box', transformOrigin: `${cx}px ${cy}px` }}
    >
      <circle cx={cx} cy={cy} r={r} fill="#111827" stroke="#374151" strokeWidth="1.2" />
      <circle cx={cx} cy={cy} r={r * 0.42} fill="#1f2937" />
      <circle cx={cx} cy={cy} r={r * 0.18} fill="#6b7280" />
    </g>
  );
}

export function SedanSvg({
  body,
  accent,
  headlightsOn = true,
  spinning = true,
}: {
  body: string;
  accent: string;
  headlightsOn?: boolean;
  spinning?: boolean;
}) {
  return (
    <svg viewBox="0 0 96 44" className={styles.vehicleSvg} role="presentation">
      <ellipse cx="48" cy="40" rx="38" ry="3" fill="rgba(0,0,0,0.35)" />
      <path
        d="M12 28 Q12 22 20 20 L28 14 Q36 10 48 10 Q60 10 68 14 L76 20 Q84 22 84 28 L84 32 Q84 36 78 36 L18 36 Q12 36 12 32 Z"
        fill={body}
      />
      <path
        d="M26 20 L34 14 L62 14 L70 20 L68 26 L28 26 Z"
        fill={accent}
        opacity="0.95"
      />
      <path d="M38 14 L42 11 L54 11 L58 14 Z" fill="rgba(255,255,255,0.2)" />
      {headlightsOn && (
        <>
          <ellipse cx="16" cy="28" rx="5" ry="3" fill="#fef08a" opacity="0.9" />
          <ellipse cx="16" cy="28" rx="8" ry="5" fill="#fef08a" opacity="0.25" />
        </>
      )}
      <rect x="72" y="24" width="6" height="4" rx="1" fill="#fca5a5" opacity="0.85" />
      <Wheel cx={26} cy={36} r={7.5} spinning={spinning} />
      <Wheel cx={70} cy={36} r={7.5} spinning={spinning} />
    </svg>
  );
}

export function MotorcycleSvg({
  helmetGlow,
  spinning = true,
}: {
  helmetGlow?: boolean;
  spinning?: boolean;
}) {
  return (
    <svg viewBox="0 0 78 52" className={styles.vehicleSvg} role="presentation">
      <ellipse cx="39" cy="48" rx="28" ry="2.5" fill="rgba(0,0,0,0.3)" />
      <path
        d="M14 40 Q14 36 18 34 L32 22 L44 26 L60 40"
        stroke="#c026d3"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <ellipse cx="16" cy="40" rx="9" ry="9" fill="#111827" stroke="#374151" strokeWidth="1.2" />
      <ellipse cx="58" cy="40" rx="9" ry="9" fill="#111827" stroke="#374151" strokeWidth="1.2" />
      <g className={spinning ? styles.wheelSpin : undefined} style={{ transformOrigin: '16px 40px', transformBox: 'fill-box' }}>
        <circle cx="16" cy="40" r="4" fill="#4b5563" />
      </g>
      <g className={spinning ? styles.wheelSpin : undefined} style={{ transformOrigin: '58px 40px', transformBox: 'fill-box' }}>
        <circle cx="58" cy="40" r="4" fill="#4b5563" />
      </g>
      <rect x="38" y="30" width="14" height="6" rx="2" fill="#4b5563" />
      <circle cx="46" cy="22" r="5" fill="#94a3b8" />
      <g className={helmetGlow ? styles.helmetGlowActive : undefined}>
        <path
          d="M36 20 Q46 8 56 20 L54 23 Q46 14 38 23 Z"
          fill="#64748b"
          stroke="#475569"
          strokeWidth="0.6"
        />
        <ellipse cx="46" cy="18" rx="8" ry="6" fill="#374151" />
        <rect x="42" y="10" width="8" height="3" rx="1" fill="#fbbf24" />
      </g>
      <ellipse cx="12" cy="32" rx="4" ry="2.5" fill="#fef08a" opacity="0.85" />
    </svg>
  );
}

export function PedestrianSvg({ walking }: { walking?: boolean }) {
  return (
    <svg
      viewBox="0 0 28 44"
      className={`${styles.pedSvg} ${walking ? styles.pedWalking : ''}`}
      role="presentation"
    >
      <circle cx="14" cy="9" r="5.5" fill="#fbbf24" />
      <rect x="10" y="15" width="8" height="15" rx="2.5" fill="#64748b" />
      <g className={styles.pedLegs}>
        <line x1="14" y1="30" x2="9" y2="42" stroke="#e5e7eb" strokeWidth="2.8" strokeLinecap="round" />
        <line x1="14" y1="30" x2="19" y2="42" stroke="#e5e7eb" strokeWidth="2.8" strokeLinecap="round" />
      </g>
      <line x1="14" y1="20" x2="8" y2="26" stroke="#e5e7eb" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="14" y1="20" x2="20" y2="26" stroke="#e5e7eb" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}
