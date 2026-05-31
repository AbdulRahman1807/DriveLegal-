'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import styles from './Shield360Viewer.module.css';

const SPRITE_URL = '/shield-360/spritesheet.png';
const FRAME_COUNT = 16;
const CELL_W = 205;
const CELL_H = 480;

type Shield360ViewerProps = {
  size?: 'hero' | 'compact' | 'auth';
  isTalking?: boolean;
  isListening?: boolean;
};

export default function Shield360Viewer({
  size = 'hero',
  isTalking = false,
  isListening = false,
}: Shield360ViewerProps) {
  const [loaded, setLoaded] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const rotationRef = useRef(0);
  const dragRef = useRef<{ startX: number; startRotation: number } | null>(null);
  const viewerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sheetRef = useRef<HTMLImageElement | null>(null);
  const rafRef = useRef<number | null>(null);

  const paintFrame = useCallback((deg: number) => {
    const canvas = canvasRef.current;
    const sheet = sheetRef.current;
    if (!canvas || !sheet) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const normalized = ((deg % 360) + 360) % 360;
    const pos = (normalized / 360) * FRAME_COUNT;
    const i0 = Math.floor(pos) % FRAME_COUNT;
    const i1 = (i0 + 1) % FRAME_COUNT;
    const blend = pos - Math.floor(pos);

    const cw = canvas.clientWidth;
    const ch = canvas.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cw, ch);

    const scale = Math.min(cw / CELL_W, ch / CELL_H);
    const dw = CELL_W * scale;
    const dh = CELL_H * scale;
    const dx = (cw - dw) / 2;
    const dy = ch - dh;

    const drawFrame = (index: number, alpha: number) => {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.drawImage(
        sheet,
        index * CELL_W,
        0,
        CELL_W,
        CELL_H,
        dx,
        dy,
        dw,
        dh,
      );
      ctx.restore();
    };

    drawFrame(i0, 1 - blend);
    if (blend > 0.001) {
      drawFrame(i1, blend);
    }
  }, []);

  const schedulePaint = useCallback(
    (deg: number) => {
      rotationRef.current = deg;
      if (rafRef.current !== null) return;
      rafRef.current = window.requestAnimationFrame(() => {
        paintFrame(rotationRef.current);
        rafRef.current = null;
      });
    },
    [paintFrame],
  );

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    dragRef.current = { startX: e.clientX, startRotation: rotationRef.current };
    setIsDragging(true);
    viewerRef.current?.setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragRef.current) return;
      const deltaX = e.clientX - dragRef.current.startX;
      schedulePaint(dragRef.current.startRotation + deltaX * 1.1);
    },
    [schedulePaint],
  );

  const endDrag = useCallback((e: React.PointerEvent) => {
    dragRef.current = null;
    setIsDragging(false);
    try {
      viewerRef.current?.releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const img = new window.Image();
    img.onload = () => {
      if (!mounted) return;
      sheetRef.current = img;
      setLoaded(true);
      paintFrame(0);
    };
    img.onerror = () => {
      if (mounted) setLoaded(true);
    };
    img.src = SPRITE_URL;

    return () => {
      mounted = false;
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
      }
    };
  }, [paintFrame]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.round(rect.width * dpr));
      canvas.height = Math.max(1, Math.round(rect.height * dpr));
      paintFrame(rotationRef.current);
    };

    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [loaded, paintFrame]);

  return (
    <div
      ref={viewerRef}
      className={`${styles.viewer} ${styles[size]} ${isTalking ? styles.talking : ''} ${isListening ? styles.listening : ''} ${isDragging ? styles.dragging : ''} ${loaded ? styles.loaded : ''}`}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      role="img"
      aria-label="Shield mascot — drag to rotate 360 degrees"
    >
      <div className={styles.glowRing} aria-hidden />
      <div className={`${styles.floatWrap} ${isDragging ? styles.floatPaused : ''}`}>
        <canvas ref={canvasRef} className={styles.canvas} />
      </div>
    </div>
  );
}
