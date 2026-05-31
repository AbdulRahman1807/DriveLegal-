export type TrafficPhase = 'red' | 'amber' | 'green';

export type BadgeKind =
  | 'helmet'
  | 'signal'
  | 'lane'
  | 'speed'
  | 'pedestrian'
  | 'warning';

export const PHASE_MS: Record<TrafficPhase, number> = {
  green: 5500,
  amber: 2200,
  red: 5000,
};

export const PHASE_ORDER: TrafficPhase[] = ['green', 'amber', 'red'];

/** Zebra crossing zone (% from left) */
export const ZEBRA_LEFT = 36;
export const ZEBRA_RIGHT = 52;
export const SIDEWALK_LEFT = 22;
export const SIDEWALK_RIGHT = 60;
export const STOP_LINE = 46;

export const LOCATION = {
  city: 'Chennai',
  state: 'Tamil Nadu',
  speedLimitKmh: 40,
  helmetRule: 'Helmet Rule Active',
  schoolZone: 'School Zone',
} as const;

export const RULE_CARDS = [
  { label: 'Helmet Detected' },
  { label: 'Speed Within Limit' },
  { label: 'Pedestrian Priority' },
  { label: 'Signal Compliance' },
  { label: 'Lane Discipline' },
] as const;

export const SHIELD_COACH: Record<
  BadgeKind | 'default' | 'red' | 'green',
  { title: string; subtitle: string }
> = {
  helmet: {
    title: 'Great! The rider is wearing a helmet.',
    subtitle: 'Safe driving starts with protection.',
  },
  signal: {
    title: 'The vehicle stopped at the red signal.',
    subtitle: 'Traffic rules save lives.',
  },
  lane: {
    title: 'Excellent lane discipline.',
    subtitle: 'Stay in your lane — that is the law.',
  },
  speed: {
    title: 'Speed is within the limit.',
    subtitle: `Under ${LOCATION.speedLimitKmh} km/h — well done.`,
  },
  pedestrian: {
    title: 'Pedestrian crossed safely.',
    subtitle: 'You yielded — pedestrian priority matters.',
  },
  warning: {
    title: 'Pedestrian ahead — slow down!',
    subtitle: 'Always yield at crossings.',
  },
  red: {
    title: 'Red light — all vehicles must stop.',
    subtitle: 'Pedestrians may cross now.',
  },
  green: {
    title: 'Green light — proceed with care.',
    subtitle: 'Watch for pedestrians and signals.',
  },
  default: {
    title: 'I am watching the road with you.',
    subtitle: 'DriveLegal helps you follow traffic laws.',
  },
};

export const BADGE_LABELS: Record<BadgeKind, string> = {
  helmet: 'Helmet On',
  signal: 'Signal Compliance',
  lane: 'Following Lane Discipline',
  speed: 'Safe Speed',
  pedestrian: 'Pedestrian Priority',
  warning: 'Pedestrian Ahead',
};
