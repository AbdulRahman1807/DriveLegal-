'use client';

import { useEffect, useRef, useState } from 'react';
import styles from './DriveLegalSimulator.module.css';

type DriveLegalSimulatorProps = {
  variant?: 'footer' | 'hero';
};

export default function DriveLegalSimulator({ variant = 'footer' }: DriveLegalSimulatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isRunning, setIsRunning] = useState(true);
  const [signalColor, setSignalColor] = useState<'red' | 'amber' | 'green'>('green');
  const [eventText, setEventText] = useState('Simulation running...');
  const [eventColor, setEventColor] = useState('#639922');

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    let running = true;
    let raf: number;
    let t = 0;

    const COLORS = {
      sky: '#dce8f5',
      grass: '#c4d9b0',
      pavement: '#c8c2b8',
      road: '#2a2d36',
      roadLine: 'rgba(255,255,255,0.22)',
      roadCenter: 'rgba(255,220,80,0.55)',
      zebra: 'rgba(255,255,255,0.7)',
      building1: '#b8b4ac',
      building2: '#9e9a94',
      building3: '#ccc9c2',
      window: 'rgba(180,200,230,0.5)',
      tree: '#7aaf5a',
      treeTrunk: '#8a7060',
      pole: '#888080',
      carBlue: '#3d5fa0',
      carBlue2: '#2d4f90',
      carGreen: '#4a7a55',
      carGreen2: '#3a6a45',
      carSilver: '#9a9da8',
      carSilver2: '#7a7d88',
      bikeFrame: '#5a5060',
      helmet: '#2c2c2c',
      busStop: '#ccc5b8',
      text: '#3a3830',
      signalRed: '#e24b4a',
      signalAmber: '#ef9f27',
      signalGreen: '#639922',
    };

    const ROAD_Y_TOP = 0.38;
    const ROAD_Y_BOT = 0.85;
    const LANE1_Y = 0.50;
    const LANE2_Y = 0.68;
    const LANE3_Y = 0.83;
    const ZEBRA_X = 0.68;
    const SIGNAL_X = 0.78;

    const signal = {
      phase: 0,
      timer: 0,
      phases: [
        { color: 'red' as const, duration: 280 },
        { color: 'amber' as const, duration: 60 },
        { color: 'green' as const, duration: 340 },
        { color: 'amber' as const, duration: 60 },
      ],
      get current() { return this.phases[this.phase]; },
      tick() {
        this.timer++;
        if (this.timer >= this.current.duration) {
          this.phase = (this.phase + 1) % this.phases.length;
          this.timer = 0;
        }
      },
      isRed() { return this.current.color === 'red'; },
      isGreen() { return this.current.color === 'green'; },
    };

    function lerp(a: number, b: number, t: number) { return a + (b - a) * t; }
    function easeOut(t: number) { return 1 - Math.pow(1 - t, 2); }
    function easeInOut(t: number) { return t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2, 2)/2; }

    interface Vehicle {
      x: number;
      lane: number;
      color: string;
      color2: string;
      type: 'car' | 'bike';
      baseSpeed: number;
      speed: number;
      id: string;
      stopped: boolean;
    }

    function Vehicle({ x, lane, color, color2, type, speed, id }: { x: number; lane: number; color: string; color2: string; type: 'car' | 'bike'; speed: number; id: string }): Vehicle {
      return { x, lane, color, color2, type, baseSpeed: speed, speed, id, stopped: false };
    }

    function makeVehicles(): Vehicle[] {
      return [
        Vehicle({ x: 0.05,  lane: LANE1_Y, color: COLORS.carBlue,   color2: COLORS.carBlue2,   type: 'car',  speed: 0.0018, id: 'car1'  }),
        Vehicle({ x: -0.30, lane: LANE1_Y, color: COLORS.carSilver, color2: COLORS.carSilver2, type: 'car',  speed: 0.0018, id: 'car2'  }),
        Vehicle({ x: -0.80, lane: LANE1_Y, color: COLORS.carGreen,  color2: COLORS.carGreen2,  type: 'car',  speed: 0.0018, id: 'car3'  }),
        Vehicle({ x: 0.20,  lane: LANE2_Y, color: COLORS.carGreen,  color2: COLORS.carGreen2,  type: 'car',  speed: 0.0014, id: 'car4'  }),
        Vehicle({ x: -0.50, lane: LANE2_Y, color: COLORS.carBlue,   color2: COLORS.carBlue2,   type: 'car',  speed: 0.0014, id: 'car5'  }),
        Vehicle({ x: 0.35,  lane: LANE2_Y, color: COLORS.bikeFrame, color2: COLORS.bikeFrame,  type: 'bike', speed: 0.0012, id: 'bike1' }),
      ];
    }

    const vehicles = makeVehicles();

    const pedestrian = {
      active: false, x: 0, y: 0,
      progress: 0, timer: 0, cooldown: 0, step: 0,
    };

    function triggerPedestrian(w: number, h: number) {
      if (!pedestrian.active && pedestrian.cooldown <= 0 && signal.isRed()) {
        pedestrian.active = true;
        pedestrian.progress = 0;
        pedestrian.x = ZEBRA_X;
        pedestrian.step = 0;
      }
    }

    function updatePedestrian() {
      if (!pedestrian.active) {
        pedestrian.cooldown = Math.max(0, pedestrian.cooldown - 1);
        return;
      }
      pedestrian.progress += 0.004;
      pedestrian.step++;
      if (pedestrian.progress >= 1) {
        pedestrian.active = false;
        pedestrian.cooldown = 220;
        setEventText('Pedestrian crossed safely');
        setEventColor(COLORS.signalGreen);
      }
    }

    function drawPedestrian(w: number, h: number) {
      if (!pedestrian.active) return;
      const px = pedestrian.x * w;
      const roadTop = ROAD_Y_TOP * h;
      const roadBot = ROAD_Y_BOT * h;
      const py = lerp(roadTop - h * 0.04, roadBot + h * 0.04, easeInOut(pedestrian.progress));
      const bobX = Math.sin(pedestrian.step * 0.5) * 2.5;
      const scale = lerp(0.55, 1.0, pedestrian.progress) * 0.7;

      context!.save();
      context!.translate(px + bobX, py);
      context!.scale(scale, scale);

      context!.fillStyle = '#8a8078';
      context!.beginPath(); context!.arc(0, -24, 7, 0, Math.PI * 2); context!.fill();

      context!.strokeStyle = '#6a6058';
      context!.lineWidth = 5; context!.lineCap = 'round';
      context!.beginPath(); context!.moveTo(0, -17); context!.lineTo(0, 4); context!.stroke();
      context!.beginPath(); context!.moveTo(0, -10); context!.lineTo(-8, 0); context!.stroke();
      context!.beginPath(); context!.moveTo(0, -10); context!.lineTo(8, 0);  context!.stroke();

      const lp = Math.sin(pedestrian.step * 0.5);
      context!.beginPath(); context!.moveTo(0, 4); context!.lineTo(-6, 14 + lp * 5); context!.stroke();
      context!.beginPath(); context!.moveTo(0, 4); context!.lineTo(6,  14 - lp * 5); context!.stroke();

      context!.restore();
    }

    function drawBackground(w: number, h: number) {
      const sky = context!.createLinearGradient(0, 0, 0, h * ROAD_Y_TOP);
      sky.addColorStop(0, '#cfe0f0');
      sky.addColorStop(1, '#dceaf7');
      context!.fillStyle = sky;
      context!.fillRect(0, 0, w, h * ROAD_Y_TOP);

      context!.fillStyle = COLORS.grass;
      context!.fillRect(0, h * ROAD_Y_TOP - h * 0.08, w, h * 0.08);

      context!.fillStyle = COLORS.road;
      context!.fillRect(0, h * ROAD_Y_TOP, w, h * (ROAD_Y_BOT - ROAD_Y_TOP));

      context!.fillStyle = COLORS.pavement;
      context!.fillRect(0, h * ROAD_Y_BOT, w, h * (1 - ROAD_Y_BOT));

      const laneH = h * (ROAD_Y_BOT - ROAD_Y_TOP) / 3;
      const laneMiddle = h * ROAD_Y_TOP + laneH;

      context!.strokeStyle = COLORS.roadCenter;
      context!.lineWidth = 2;
      context!.setLineDash([28, 18]);
      context!.beginPath(); context!.moveTo(0, laneMiddle); context!.lineTo(w, laneMiddle); context!.stroke();
      context!.setLineDash([]);

      context!.strokeStyle = COLORS.roadLine;
      context!.lineWidth = 1.5;
      context!.setLineDash([22, 16]);
      const lane2Middle = h * ROAD_Y_TOP + laneH * 2;
      context!.beginPath(); context!.moveTo(0, lane2Middle); context!.lineTo(w, lane2Middle); context!.stroke();
      context!.setLineDash([]);

      context!.strokeStyle = 'rgba(255,255,255,0.12)';
      context!.lineWidth = 1;
      context!.beginPath(); context!.moveTo(0, h * ROAD_Y_TOP); context!.lineTo(w, h * ROAD_Y_TOP); context!.stroke();
      context!.beginPath(); context!.moveTo(0, h * ROAD_Y_BOT); context!.lineTo(w, h * ROAD_Y_BOT); context!.stroke();
    }

    function drawZebra(w: number, h: number) {
      const zx = ZEBRA_X * w;
      const zw = 36;
      const roadTop = ROAD_Y_TOP * h;
      const roadBot = ROAD_Y_BOT * h;
      const stripeH = 10, gap = 7;
      let y = roadTop + 2;
      context!.save();
      context!.globalAlpha = 0.65;
      while (y < roadBot - 2) {
        context!.fillStyle = COLORS.zebra;
        context!.fillRect(zx - zw / 2, y, zw, Math.min(stripeH, roadBot - y));
        y += stripeH + gap;
      }
      context!.restore();
    }

    function drawBuildings(w: number, h: number) {
      const horizon = h * (ROAD_Y_TOP - 0.08);
      const buildings = [
        { rx: 0.02, rh: 0.28, rw: 0.09, color: COLORS.building2 },
        { rx: 0.12, rh: 0.23, rw: 0.07, color: COLORS.building3 },
        { rx: 0.21, rh: 0.30, rw: 0.10, color: COLORS.building1 },
        { rx: 0.33, rh: 0.25, rw: 0.08, color: COLORS.building2 },
        { rx: 0.44, rh: 0.32, rw: 0.12, color: COLORS.building3 },
        { rx: 0.58, rh: 0.26, rw: 0.08, color: COLORS.building1 },
        { rx: 0.88, rh: 0.29, rw: 0.11, color: COLORS.building2 },
      ];
      buildings.forEach(b => {
        const bx = b.rx * w, bh = b.rh * h, bw = b.rw * w;
        const by = horizon - bh;
        context!.fillStyle = b.color;
        context!.beginPath();
        context!.roundRect(bx, by, bw, bh + 2, 3);
        context!.fill();
        for (let row = 0; row < 4; row++) {
          for (let col = 0; col < 3; col++) {
            context!.fillStyle = COLORS.window;
            context!.fillRect(bx + col * (bw / 3.5) + 3, by + row * (bh / 4.5) + 4, bw / 6, bh / 8);
          }
        }
      });
    }

    function drawTrees(w: number, h: number) {
      const baseY = h * (ROAD_Y_TOP - 0.02);
      [0.08, 0.19, 0.30, 0.42, 0.53, 0.62, 0.72, 0.84, 0.95].forEach(rx => {
        const tx = rx * w;
        context!.fillStyle = COLORS.treeTrunk;
        context!.fillRect(tx - 3, baseY - 22, 6, 22);
        context!.fillStyle = COLORS.tree;
        context!.beginPath(); context!.arc(tx,     baseY - 30, 14, 0, Math.PI * 2); context!.fill();
        context!.fillStyle = '#90b870';
        context!.beginPath(); context!.arc(tx - 5, baseY - 35, 10, 0, Math.PI * 2); context!.fill();
        context!.fillStyle = '#68a045';
        context!.beginPath(); context!.arc(tx + 5, baseY - 28,  9, 0, Math.PI * 2); context!.fill();
      });
    }

    function drawStreetLights(w: number, h: number) {
      const baseY = h * ROAD_Y_TOP;
      [0.14, 0.40, 0.65, 0.92].forEach(rx => {
        const lx = rx * w;
        context!.strokeStyle = '#888'; context!.lineWidth = 3; context!.lineCap = 'round';
        context!.beginPath();
        context!.moveTo(lx, baseY);
        context!.lineTo(lx, baseY - h * 0.22);
        context!.lineTo(lx + 18, baseY - h * 0.22);
        context!.stroke();
        context!.fillStyle = '#d4c070';
        context!.beginPath();
        context!.ellipse(lx + 18, baseY - h * 0.22 - 4, 9, 5, 0, 0, Math.PI * 2);
        context!.fill();
      });
    }

    function drawBusStop(w: number, h: number) {
      const bx = 0.88 * w, by = h * ROAD_Y_BOT;
      context!.fillStyle = COLORS.busStop; context!.strokeStyle = '#aaa8a0'; context!.lineWidth = 1;
      context!.beginPath(); context!.roundRect(bx - 18, by - h * 0.18, 36, h * 0.18, 4); context!.fill(); context!.stroke();
      context!.fillStyle = '#e0dcd5';
      context!.fillRect(bx - 16, by - h * 0.16, 32, h * 0.10);
      context!.fillStyle = COLORS.text;
      context!.font = 'bold 8px sans-serif';
      context!.textAlign = 'center';
      context!.fillText('BUS', bx, by - h * 0.09);
    }

    function drawSignal(w: number, h: number) {
      const sx = SIGNAL_X * w;
      const roadTop = ROAD_Y_TOP * h;
      const poleH = h * 0.30;
      const bw = 22, bh = 60;
      const by = roadTop - poleH;

      context!.strokeStyle = COLORS.pole; context!.lineWidth = 3;
      context!.beginPath(); context!.moveTo(sx, roadTop); context!.lineTo(sx, by); context!.stroke();

      context!.fillStyle = '#1a1a1a';
      context!.beginPath(); context!.roundRect(sx - bw/2, by, bw, bh, 4); context!.fill();

      const colors = {
        red:   [COLORS.signalRed,   '#1a1a1a', '#1a1a1a'],
        amber: ['#1a1a1a', COLORS.signalAmber, '#1a1a1a'],
        green: ['#1a1a1a', '#1a1a1a', COLORS.signalGreen],
      }[signal.current.color];

      [by + 8, by + 28, by + 48].forEach((ly, i) => {
        context!.fillStyle = colors[i];
        context!.beginPath(); context!.arc(sx, ly, 6, 0, Math.PI * 2); context!.fill();
        if (colors[i] !== '#1a1a1a') {
          context!.fillStyle = colors[i] + '40';
          context!.beginPath(); context!.arc(sx, ly, 10, 0, Math.PI * 2); context!.fill();
        }
      });
    }

    function drawRoadSigns(w: number, h: number) {
      const sy = h * (ROAD_Y_TOP - 0.08);
      context!.strokeStyle = COLORS.pole; context!.lineWidth = 2;

      const s1x = 0.26 * w;
      context!.beginPath(); context!.moveTo(s1x, sy + 4); context!.lineTo(s1x, h * ROAD_Y_TOP); context!.stroke();
      context!.strokeStyle = '#e24b4a'; context!.lineWidth = 2.5;
      context!.fillStyle = '#f0ede6';
      context!.beginPath(); context!.arc(s1x, sy - 12, 16, 0, Math.PI * 2); context!.fill(); context!.stroke();
      context!.fillStyle = '#1a1a1a';
      context!.font = 'bold 10px sans-serif'; context!.textAlign = 'center';
      context!.fillText('40',   s1x, sy - 8);
      context!.font = '7px sans-serif';
      context!.fillText('km/h', s1x, sy - 1);

      const s2x = 0.50 * w;
      context!.strokeStyle = COLORS.pole; context!.lineWidth = 2;
      context!.beginPath(); context!.moveTo(s2x, sy + 4); context!.lineTo(s2x, h * ROAD_Y_TOP); context!.stroke();
      context!.fillStyle = '#f0c040'; context!.strokeStyle = '#c09020'; context!.lineWidth = 1.5;
      context!.beginPath(); context!.roundRect(s2x - 20, sy - 26, 40, 22, 3); context!.fill(); context!.stroke();
      context!.fillStyle = '#1a1a1a';
      context!.font = 'bold 7px sans-serif'; context!.textAlign = 'center';
      context!.fillText('SCHOOL', s2x, sy - 17);
      context!.fillText('ZONE',   s2x, sy - 8);
    }

    function drawCar(vx: number, vy: number, w: number, h: number, c1: string, c2: string, scale: number) {
      const cw = 50 * scale, ch = 22 * scale;
      context!.save();
      context!.translate(vx, vy);

      context!.fillStyle = '#00000022';
      context!.beginPath(); context!.ellipse(0, ch/2 + 3*scale, cw*0.45, 4*scale, 0, 0, Math.PI*2); context!.fill();

      context!.fillStyle = c1;
      context!.beginPath(); context!.roundRect(-cw/2, -ch/2, cw, ch, 3*scale); context!.fill();
      context!.fillStyle = c2;
      context!.fillRect(-cw/2, -scale, cw, 2*scale);

      const rw = cw * 0.58, rh = ch * 0.65;
      context!.fillStyle = c1;
      context!.beginPath(); context!.roundRect(-rw/2 - 2*scale, -ch/2 - rh + 2*scale, rw, rh, [3*scale,3*scale,2*scale,2*scale]); context!.fill();

      context!.fillStyle = 'rgba(180,210,235,0.75)';
      context!.beginPath(); context!.roundRect(-rw/2 + scale, -ch/2 - rh + 4*scale, rw*0.44, rh - 5*scale, 2*scale); context!.fill();
      context!.beginPath(); context!.roundRect(-rw/2 + rw*0.5, -ch/2 - rh + 4*scale, rw*0.44, rh - 5*scale, 2*scale); context!.fill();

      [[-cw*0.3, ch/2], [cw*0.3, ch/2]].forEach(([wx, wy]) => {
        context!.fillStyle = '#1a1a1a'; context!.beginPath(); context!.arc(wx, wy, 6.5*scale, 0, Math.PI*2); context!.fill();
        context!.fillStyle = '#888';    context!.beginPath(); context!.arc(wx, wy, 3*scale,   0, Math.PI*2); context!.fill();
      });

      context!.fillStyle = '#f0e06090';
      context!.beginPath(); context!.ellipse(-cw/2 + 3*scale, -2*scale, 5*scale, 3*scale, 0, 0, Math.PI*2); context!.fill();
      context!.fillStyle = '#e2404090';
      context!.beginPath(); context!.ellipse(cw/2 - 3*scale,  -2*scale, 4*scale, 3*scale, 0, 0, Math.PI*2); context!.fill();

      context!.restore();
    }

    function drawBike(vx: number, vy: number, w: number, h: number, scale: number) {
      const s = scale;
      context!.save();
      context!.translate(vx, vy);

      context!.fillStyle = '#0000001a';
      context!.beginPath(); context!.ellipse(0, 14*s, 20*s, 4*s, 0, 0, Math.PI*2); context!.fill();

      [-16*s, 16*s].forEach(wx => {
        context!.strokeStyle = '#2a2a2a'; context!.lineWidth = 2.5*s;
        context!.beginPath(); context!.arc(wx, 8*s, 11*s, 0, Math.PI*2); context!.stroke();
        context!.fillStyle = '#aaa'; context!.beginPath(); context!.arc(wx, 8*s, 3*s, 0, Math.PI*2); context!.fill();
      });

      context!.strokeStyle = COLORS.bikeFrame; context!.lineWidth = 2.5*s; context!.lineCap = 'round';
      context!.beginPath(); context!.moveTo(-16*s, 8*s); context!.lineTo(0, -2*s); context!.lineTo(16*s, 8*s); context!.stroke();
      context!.beginPath(); context!.moveTo(0, -2*s); context!.lineTo(0,    8*s);  context!.stroke();
      context!.beginPath(); context!.moveTo(-2*s, 8*s); context!.lineTo(16*s, 8*s); context!.stroke();
      context!.beginPath(); context!.moveTo(0, -2*s); context!.lineTo(-10*s, -12*s); context!.stroke();

      context!.fillStyle = '#5a5060';
      context!.beginPath(); context!.arc(-10*s, -18*s, 6*s, 0, Math.PI*2); context!.fill();

      context!.fillStyle = COLORS.helmet;
      context!.beginPath(); context!.arc(-10*s, -23*s, 7*s, Math.PI, Math.PI*2); context!.fill();
      context!.fillStyle = '#444';
      context!.fillRect(-10*s - 7*s, -23*s, 14*s, 3*s);

      context!.strokeStyle = '#888'; context!.lineWidth = 2*s;
      context!.beginPath(); context!.moveTo(16*s, -2*s); context!.lineTo(22*s, -2*s); context!.stroke();

      context!.fillStyle = '#f0e06080';
      context!.beginPath(); context!.ellipse(-20*s, 8*s, 5*s, 3*s, 0, 0, Math.PI*2); context!.fill();

      context!.restore();
    }

    function getStopX(w: number) { return (ZEBRA_X - 0.06) * w; }

    function updateVehicle(v: Vehicle, w: number) {
      const stopX = getStopX(w);
      const vx = v.x * w;
      const targetSpeed = v.baseSpeed * w;
      const isMovingLane = v.lane === LANE1_Y || v.lane === LANE2_Y;

      if (isMovingLane && signal.isRed()) {
        const dist = stopX - vx;
        if (dist <= 2) {
          v.speed = 0; v.stopped = true;
        } else if (dist < w * 0.22) {
          v.speed = targetSpeed * easeOut(Math.max(0, dist / (w * 0.22)));
          v.stopped = false;
        } else {
          v.speed = targetSpeed; v.stopped = false;
        }
      } else {
        v.speed = targetSpeed; v.stopped = false;
      }

      if (!v.stopped) v.x += v.speed / w;
      if (v.x > 1.25) v.x = -0.3;
    }

    let lastSignalColor = signal.current.color;

    function loop() {
      if (!running) return;
      const w = canvas!.width  / (window.devicePixelRatio || 1);
      const h = canvas!.height / (window.devicePixelRatio || 1);

      context!.clearRect(0, 0, canvas!.width, canvas!.height);
      context!.save();

      signal.tick();

      if (signal.current.color !== lastSignalColor) {
        lastSignalColor = signal.current.color;
        if (signal.isGreen()) {
          setEventText('Signal green — traffic moving');
          setEventColor(COLORS.signalGreen);
        } else if (signal.current.color === 'red') {
          setEventText('Signal red — vehicles stopping');
          setEventColor(COLORS.signalRed);
        } else {
          setEventText('Signal amber — slowing down');
          setEventColor(COLORS.signalAmber);
        }
      }

      triggerPedestrian(w, h);
      updatePedestrian();
      vehicles.forEach(v => updateVehicle(v, w));

      drawBackground(w, h);
      drawBuildings(w, h);
      drawTrees(w, h);
      drawStreetLights(w, h);
      drawBusStop(w, h);
      drawRoadSigns(w, h);
      drawZebra(w, h);
      drawSignal(w, h);

      [...vehicles]
        .sort((a, b) => (b.lane - a.lane) || (b.x - a.x))
        .forEach(v => {
          const vx = v.x * w, vy = v.lane * h;
          const p = (v.lane - ROAD_Y_TOP) / (ROAD_Y_BOT - ROAD_Y_TOP);
          const scale = lerp(0.5, 1.0, p) * 0.85;
          if (v.type === 'car') drawCar(vx, vy, w, h, v.color, v.color2, scale);
          else drawBike(vx, vy, w, h, scale);
        });

      drawPedestrian(w, h);

      context!.restore();
      t++;
      raf = requestAnimationFrame(loop);
    }

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      canvas!.width = canvas!.offsetWidth * dpr;
      canvas!.height = canvas!.offsetHeight * dpr;
      context!.scale(dpr, dpr);
    }

    resize();
    window.addEventListener('resize', resize);

    loop();

    const interval = setInterval(() => {
      if (signal.isGreen()) {
        setSignalColor('green');
      } else if (signal.current.color === 'red') {
        setSignalColor('red');
      } else {
        setSignalColor('amber');
      }
    }, 500);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      clearInterval(interval);
      window.removeEventListener('resize', resize);
    };
  }, []);

  const toggleSimulation = () => {
    setIsRunning(!isRunning);
  };

  return (
    <div className={`${styles.simCard} ${styles[variant]}`}>
      <div className={styles.simHeader}>
        <div className={styles.simBrand}>
          <div className={styles.simDot} />
          <div>
            <div className={styles.simTitle}>Road Safety Simulation</div>
            <div className={styles.simSubtitle}>Tamil Nadu — Live preview</div>
          </div>
        </div>
        <div className={styles.simBadges}>
          <span className={`${styles.badge} ${styles.active}`}>Helmet compliant</span>
          <span className={`${styles.badge} ${signalColor === 'green' ? styles.active : ''}`}>40 km/h zone</span>
          <span className={`${styles.badge} ${signalColor === 'green' ? styles.active : ''}`}>
            {signalColor === 'red' ? 'Stopping at red' : signalColor === 'green' ? 'Signal obeying' : 'Slowing amber'}
          </span>
        </div>
      </div>

      <div className={styles.simStage}>
        <canvas ref={canvasRef} className={styles.canvas} />
      </div>

      <div className={styles.simFooter}>
        <div className={styles.eventLog}>
          <div className={styles.eventDot} style={{ background: eventColor }} />
          <span className={styles.eventText}>{eventText}</span>
        </div>
        <div className={styles.simControls}>
          <button className={styles.ctrlBtn} onClick={toggleSimulation}>
            {isRunning ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>
    </div>
  );
}
