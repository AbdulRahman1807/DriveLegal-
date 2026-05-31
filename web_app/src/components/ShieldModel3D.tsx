'use client';

import { useMemo, useRef, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Bounds, Center, OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import styles from './ShieldAvatar.module.css';

const MODEL_URL = '/shield-mascot.glb';

/** Uniform scale per layout slot — model geometry is unchanged */
const SCALE_BY_SIZE = {
  hero: 1,
  compact: 0.55,
  auth: 1.35,
} as const;

type ShieldModel3DProps = {
  size?: 'hero' | 'compact' | 'auth';
  onDragStart?: () => void;
  isTalking?: boolean;
  isListening?: boolean;
  isThinking?: boolean;
};

function AnimatedShield({ size, isTalking, isListening, isThinking }: { size: keyof typeof SCALE_BY_SIZE; isTalking?: boolean; isListening?: boolean; isThinking?: boolean }) {
  const { scene } = useGLTF(MODEL_URL);
  const model = useMemo(() => scene.clone(), [scene]);
  const scale = SCALE_BY_SIZE[size];
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (!groupRef.current) return;
    
    const time = state.clock.getElapsedTime();
    
    // Idle breathing animation
    if (!isTalking && !isListening && !isThinking) {
      groupRef.current.position.y = Math.sin(time * 0.8) * 0.03;
      groupRef.current.rotation.y = Math.sin(time * 0.3) * 0.05;
    }
    
    // Talking animation - subtle bobbing
    if (isTalking) {
      groupRef.current.position.y = Math.sin(time * 4) * 0.02;
      groupRef.current.rotation.y = Math.sin(time * 2) * 0.03;
    }
    
    // Listening animation - lean forward slightly
    if (isListening) {
      groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, 0.1, 0.05);
      groupRef.current.position.z = THREE.MathUtils.lerp(groupRef.current.position.z, 0.1, 0.05);
    } else {
      groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, 0, 0.05);
      groupRef.current.position.z = THREE.MathUtils.lerp(groupRef.current.position.z, 0, 0.05);
    }
    
    // Thinking animation - slow rotation
    if (isThinking) {
      groupRef.current.rotation.y += 0.01;
    }
  });

  return (
    <Bounds fit clip observe margin={1.12}>
      <Center>
        <group ref={groupRef}>
          <primitive object={model} scale={scale} />
        </group>
      </Center>
    </Bounds>
  );
}

function ShieldScene({ size, onDragStart, isTalking, isListening, isThinking }: ShieldModel3DProps) {
  const slot = size ?? 'hero';

  return (
    <>
      <ambientLight intensity={0.7} />
      <directionalLight position={[4, 6, 4]} intensity={1.1} />
      <directionalLight position={[-2, 3, -2]} intensity={0.35} />
      <AnimatedShield size={slot} isTalking={isTalking} isListening={isListening} isThinking={isThinking} />
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        autoRotate={false}
        rotateSpeed={0.85}
        onStart={onDragStart}
      />
    </>
  );
}

export default function ShieldModel3D({ size = 'hero', onDragStart, isTalking, isListening, isThinking }: ShieldModel3DProps) {
  return (
    <Canvas
      className={styles.canvas3d}
      style={{ background: 'transparent' }}
      camera={{ position: [0, 0.1, 2.4], fov: 42 }}
      gl={{
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
        premultipliedAlpha: true,
      }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x000000, 0);
        gl.domElement.style.background = 'transparent';
      }}
      dpr={[1, 1.5]}
    >
      <ShieldScene size={size} onDragStart={onDragStart} isTalking={isTalking} isListening={isListening} isThinking={isThinking} />
    </Canvas>
  );
}

useGLTF.preload(MODEL_URL);
