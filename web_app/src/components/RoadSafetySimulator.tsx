'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import styles from './RoadSafetySimulator.module.css';
import { MotorcycleSvg, PedestrianSvg, SedanSvg } from './road-safety/vehicles';
import {
  BADGE_LABELS,
  LOCATION,
  PHASE_MS,
  PHASE_ORDER,
  RULE_CARDS,
  SHIELD_COACH,
  SIDEWALK_LEFT,
  SIDEWALK_RIGHT,
  STOP_LINE,
  ZEBRA_LEFT,
  type BadgeKind,
  type TrafficPhase,
} from './road-safety/constants';

type PedPhase = 'idle' | 'crossing' | 'exiting';

type FloatingBadge = { id: string; kind: BadgeKind; label: string };

type RoadSafetySimulatorProps = {
  variant?: 'login' | 'footer';
  onShieldComment?: (message: string) => void;
};

function coachText(key: keyof typeof SHIELD_COACH) {
  const c = SHIELD_COACH[key];
  return `${c.title} ${c.subtitle}`;
}

export default function RoadSafetySimulator({
  variant = 'login',
  onShieldComment,
}: RoadSafetySimulatorProps) {
  const [phase, setPhase] = useState<TrafficPhase>('green');
  const [bikerX, setBikerX] = useState(-14);
  const [carLaneX, setCarLaneX] = useState(-28);
  const [carFrontX, setCarFrontX] = useState(-42);
  const [pedPhase, setPedPhase] = useState<PedPhase>('idle');
  const [badges, setBadges] = useState<FloatingBadge[]>([]);
  const [coachKey, setCoachKey] = useState<keyof typeof SHIELD_COACH>('default');
  const [helmetGlow, setHelmetGlow] = useState(false);
  const [ruleIdx, setRuleIdx] = useState(0);
  const [violationActive, setViolationActive] = useState(false);
  const [wheelsSpin, setWheelsSpin] = useState(true);

  const phaseRef = useRef(phase);
  const cycleRef = useRef(0);
  const lastHelmet = useRef(false);
  const lastSignal = useRef(false);
  const lastSpeed = useRef(false);
  const lastPedBadge = useRef(false);
  const onShieldRef = useRef(onShieldComment);

  phaseRef.current = phase;
  onShieldRef.current = onShieldComment;

  const isLogin = variant === 'login';
  const canMove = phase !== 'red';
  const vehiclesStopped = phase === 'red';

  const notifyShield = useCallback((key: keyof typeof SHIELD_COACH) => {
    setCoachKey(key);
    onShieldRef.current?.(coachText(key));
  }, []);

  const pushBadge = useCallback((kind: BadgeKind) => {
    const id = `${kind}-${Date.now()}`;
    setBadges((prev) => [...prev.slice(-2), { id, kind, label: BADGE_LABELS[kind] }]);
    setCoachKey(kind);
    onShieldRef.current?.(coachText(kind));
    window.setTimeout(() => {
      setBadges((prev) => prev.filter((b) => b.id !== id));
    }, 3000);
  }, []);

  const pushBadgeRef = useRef(pushBadge);
  const notifyRef = useRef(notifyShield);
  pushBadgeRef.current = pushBadge;
  notifyRef.current = notifyShield;

  useEffect(() => {
    const t = setInterval(() => {
      setRuleIdx((i) => (i + 1) % RULE_CARDS.length);
    }, 3200);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    let idx = 0;
    let timer: ReturnType<typeof setTimeout>;

    const advance = () => {
      const current = PHASE_ORDER[idx];
      setPhase(current);
      setWheelsSpin(current !== 'red');

      if (current === 'amber') {
        cycleRef.current += 1;
        if (cycleRef.current % 3 === 0) {
          setViolationActive(true);
          pushBadgeRef.current('warning');
        }
      }

      if (current === 'red') {
        setBikerX((x) => (x >= STOP_LINE - 10 ? STOP_LINE : x));
        setCarLaneX((x) => (x >= STOP_LINE - 10 ? STOP_LINE : x));
        setCarFrontX((x) => (x >= STOP_LINE - 10 ? STOP_LINE : x));
        setPedPhase('crossing');
        notifyRef.current('red');
        if (!lastSignal.current) {
          lastSignal.current = true;
          window.setTimeout(() => pushBadgeRef.current('signal'), 300);
          window.setTimeout(() => {
            lastSignal.current = false;
          }, 5000);
        }
      }

      if (current === 'green') {
        setPedPhase('idle');
        setViolationActive(false);
        notifyRef.current('green');
      }

      timer = setTimeout(advance, PHASE_MS[current]);
      idx = (idx + 1) % PHASE_ORDER.length;
    };

    advance();
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (pedPhase !== 'crossing') return undefined;
    const done = setTimeout(() => setPedPhase('exiting'), 3400);
    return () => clearTimeout(done);
  }, [pedPhase]);

  useEffect(() => {
    if (pedPhase !== 'exiting') return undefined;
    const hide = setTimeout(() => {
      setPedPhase('idle');
      if (!lastPedBadge.current) {
        lastPedBadge.current = true;
        pushBadgeRef.current('pedestrian');
        window.setTimeout(() => {
          lastPedBadge.current = false;
        }, 5000);
      }
    }, 450);
    return () => clearTimeout(hide);
  }, [pedPhase]);

  useEffect(() => {
    if (!canMove) return undefined;

    const tick = setInterval(() => {
      const p = phaseRef.current;
      const mult = p === 'green' ? 1.15 : p === 'amber' ? 0.2 : 0;
      if (mult === 0) return;

      const step = (x: number) => {
        if (p === 'amber' && x >= STOP_LINE - 14) {
          return Math.min(x + mult * 0.45, STOP_LINE);
        }
        return x + mult * 0.9;
      };

      setBikerX((x) => {
        let nx = step(x);
        if (nx > 108) nx = -14;
        if (nx > 16 && nx < 28 && !lastHelmet.current) {
          lastHelmet.current = true;
          setHelmetGlow(true);
          pushBadgeRef.current('helmet');
          window.setTimeout(() => {
            setHelmetGlow(false);
            lastHelmet.current = false;
          }, 3500);
        }
        return nx;
      });

      setCarLaneX((x) => {
        let nx = step(x);
        if (violationActive && nx > ZEBRA_LEFT - 10) {
          nx = Math.min(nx, ZEBRA_LEFT - 3);
        }
        if (nx > 112) nx = -28;
        if (nx > 60 && nx < 76 && !lastSpeed.current) {
          lastSpeed.current = true;
          pushBadgeRef.current('speed');
          window.setTimeout(() => {
            lastSpeed.current = false;
          }, 4500);
        }
        return nx;
      });

      setCarFrontX((x) => {
        let nx = step(x);
        if (nx > 112) nx = -42;
        return nx;
      });
    }, 48);

    return () => clearInterval(tick);
  }, [canMove, violationActive]);

  const bulbClass = (target: TrafficPhase) =>
    phase === target ? styles.bulbActive : styles.bulbDim;

  const coach = SHIELD_COACH[coachKey];
  const ruleCard = RULE_CARDS[ruleIdx];

  return (
    <div
      className={`${styles.scene} ${isLogin ? styles.login : styles.footer}`}
      role="img"
      aria-label="Interactive road safety simulation for Chennai"
    >
      <div className={styles.glassPanel} />

      <div className={styles.locationBar}>
        <span className={styles.locationPin}>{LOCATION.city}, {LOCATION.state}</span>
        <span className={styles.locationMeta}>{LOCATION.helmetRule}</span>
        <span className={styles.locationMeta}>{LOCATION.speedLimitKmh} km/h · {LOCATION.schoolZone}</span>
      </div>

      <motion.div
        className={styles.ruleCard}
        key={ruleIdx}
        initial={{ opacity: 0, x: -6 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <span>{ruleCard.label}</span>
      </motion.div>

      <motion.div
        className={styles.cityLayer}
        animate={{ x: [0, -10, 0] }}
        transition={{ duration: 24, repeat: Infinity, ease: 'easeInOut' }}
      >
        <div className={styles.skyline}>
          {[22, 36, 18, 42, 28, 16, 34, 24, 20, 38].map((h, i) => (
            <span key={i} className={styles.building} style={{ height: h }}>
              <span className={styles.windowRow} />
            </span>
          ))}
        </div>
        <div className={styles.streetLights}>
          {[10, 26, 42, 58, 74, 90].map((left) => (
            <span key={left} className={styles.streetLamp} style={{ left: `${left}%` }}>
              <span className={styles.lampPole} />
              <span className={styles.lampGlow} />
            </span>
          ))}
        </div>
      </motion.div>

      <div className={styles.roadside}>
        <div className={styles.schoolBuilding} title="School Zone">
          <span className={styles.schoolRoof} />
          <span className={styles.schoolBody}>School</span>
        </div>
        <div className={styles.busStop}>
          <span className={styles.busPole} />
          <span className={styles.busSign}>Bus</span>
        </div>
        <div className={styles.trees}>
          <span className={styles.tree}>Tree</span>
          <span className={styles.tree}>Tree</span>
        </div>
        <div className={styles.dirSign}>Road</div>
      </div>

      <div className={styles.signalCluster}>
        <div className={styles.trafficLight} aria-label={`Signal ${phase}`}>
          <span className={`${styles.bulb} ${styles.bulbRed} ${bulbClass('red')}`} />
          <span className={`${styles.bulb} ${styles.bulbAmber} ${bulbClass('amber')}`} />
          <span className={`${styles.bulb} ${styles.bulbGreen} ${bulbClass('green')}`} />
        </div>
        <span className={styles.phaseLabel}>
          {phase === 'green' ? 'GO' : phase === 'amber' ? 'SLOW' : 'STOP'}
        </span>
      </div>

      <div className={styles.roadPerspective}>
        <div className={styles.roadLayer}>
          <div className={styles.roadNeon} />
          <div className={styles.roadSurface}>
            <div className={styles.sidewalkLeft} />
            <div className={styles.sidewalkRight} />
            <div className={styles.roadReflection} />
            <div
              className={styles.laneStripes}
              style={{ animationPlayState: canMove ? 'running' : 'paused' }}
            />
            <div
              className={styles.laneStripesInner}
              style={{ animationPlayState: canMove ? 'running' : 'paused' }}
            />
            <div className={styles.zebra}>
              <div className={styles.zebraBars} />
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {pedPhase === 'crossing' && (
          <motion.div
            key="ped-walk"
            className={styles.pedestrian}
            initial={{ left: `${SIDEWALK_LEFT}%`, opacity: 0 }}
            animate={{ left: `${SIDEWALK_RIGHT}%`, opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
              left: { duration: 3.2, ease: 'easeInOut' },
              opacity: { duration: 0.25 },
            }}
          >
            <PedestrianSvg walking />
          </motion.div>
        )}
        {pedPhase === 'exiting' && (
          <motion.div
            key="ped-exit"
            className={styles.pedestrian}
            initial={{ left: `${SIDEWALK_RIGHT}%`, opacity: 1 }}
            animate={{ opacity: 0 }}
            transition={{ opacity: { duration: 0.4 } }}
          >
            <PedestrianSvg />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        className={`${styles.vehicle} ${styles.biker} ${vehiclesStopped ? styles.vehicleStopped : ''}`}
        style={{ left: `${bikerX}%` }}
      >
        <MotorcycleSvg helmetGlow={helmetGlow} spinning={wheelsSpin} />
      </motion.div>

      <motion.div
        className={`${styles.vehicle} ${styles.carLane} ${vehiclesStopped ? styles.vehicleStopped : ''} ${violationActive ? styles.carYielding : ''}`}
        style={{ left: `${carLaneX}%` }}
      >
        <SedanSvg body="#4f46e5" accent="#818cf8" spinning={wheelsSpin} />
      </motion.div>

      <motion.div
        className={`${styles.vehicle} ${styles.carFront} ${vehiclesStopped ? styles.vehicleStopped : ''}`}
        style={{ left: `${carFrontX}%` }}
      >
        <SedanSvg body="#059669" accent="#34d399" spinning={wheelsSpin} />
      </motion.div>

      <AnimatePresence>
        {badges.map((b, i) => (
          <motion.div
            key={b.id}
            className={`${styles.badge} ${styles[`badge_${b.kind}`]}`}
            style={{ top: `${8 + i * 11}%`, right: '6%' }}
            initial={{ opacity: 0, y: 8, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4 }}
          >
            {b.label}
          </motion.div>
        ))}
      </AnimatePresence>

      {!isLogin && (
        <motion.div
          className={styles.coachBubble}
          key={coachKey}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <span className={styles.coachDot} />
          <span className={styles.coachText}>
            <strong>Shield:</strong> {coach.title}
            <span className={styles.coachSub}>{coach.subtitle}</span>
          </span>
        </motion.div>
      )}
    </div>
  );
}
