// geneticframes-web/src/components/DNAFrame.tsx
import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import * as THREE from 'three';
import type { ArtTraits } from '../types';

interface DNAFrameProps {
    traits: ArtTraits;
}

const Helix = ({ traits }: { traits: ArtTraits }) => {
    const meshRef = useRef<THREE.Group>(null);
    const count = traits.particle_count || 100;

    // Generate particles based on geometry style
    const particles = useMemo(() => {
        const temp = [];
        const colors = traits.color_palette;

        for (let i = 0; i < count; i++) {
            const t = i / count;
            let x, y, z;

            // Creative geometry mapping
            if (traits.geometry_style === 'spiral' || traits.geometry_style === 'helix') {
                const angle = t * Math.PI * 10;
                const radius = 2 + Math.sin(t * 10) * 0.5;
                x = Math.cos(angle) * radius;
                y = (t - 0.5) * 10;
                z = Math.sin(angle) * radius;
            } else if (traits.geometry_style === 'fractal' || traits.geometry_style === 'voronoi') {
                const phi = Math.acos(-1 + (2 * i) / count);
                const theta = Math.sqrt(count * Math.PI) * phi;
                x = 3 * Math.cos(theta) * Math.sin(phi);
                y = 3 * Math.sin(theta) * Math.sin(phi);
                z = 3 * Math.cos(phi);
            } else {
                 // Cloud
                x = (Math.random() - 0.5) * 6;
                y = (Math.random() - 0.5) * 6;
                z = (Math.random() - 0.5) * 6;
            }

            const color = new THREE.Color(colors[i % colors.length]);
            temp.push({ position: [x, y, z], color });
        }
        return temp;
    }, [traits, count]);

    useFrame((_state, delta) => {
        if (meshRef.current) {
            meshRef.current.rotation.y += delta * 0.2;
            if (traits.geometry_style === 'fluid') {
                 meshRef.current.rotation.x += delta * 0.1;
            }
        }
    });

    return (
        <group ref={meshRef}>
            {particles.map((p, i) => (
                <mesh key={i} position={p.position as [number, number, number]}>
                    <sphereGeometry args={[0.08, 16, 16]} />
                    <meshStandardMaterial color={p.color} emissive={p.color} emissiveIntensity={0.5} />
                </mesh>
            ))}
            {/* Central Strand */}
             <mesh>
                <cylinderGeometry args={[0.1, 0.1, 10, 8]} />
                <meshStandardMaterial color={traits.color_palette[0]} transparent opacity={0.3} />
            </mesh>
        </group>
    );
};

export const DNAFrame: React.FC<DNAFrameProps> = ({ traits }) => {
    return (
        <div className="w-full h-[500px] bg-black rounded-lg overflow-hidden border border-gray-800 relative">
            <div className="absolute top-4 left-4 z-10 bg-black/50 p-2 rounded text-xs text-white backdrop-blur">
                <p>Style: {traits.geometry_style}</p>
                <p>Texture: {traits.texture_type}</p>
                <p>Complexity: {traits.complexity_score}</p>
            </div>
            <Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} />
                <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                <Helix traits={traits} />
                <OrbitControls enableZoom={true} autoRotate={false} />
            </Canvas>
        </div>
    );
};
