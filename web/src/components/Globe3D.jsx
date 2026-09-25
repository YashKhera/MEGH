import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

const CLASS_HEX = {
  Depression: '#64748b', 'Deep Depression': '#0284c7', 'Cyclonic Storm': '#0d9488',
  'Severe Cyclonic Storm': '#ca8a04', 'Very Severe Cyclonic Storm': '#ea580c',
  'Extremely Severe Cyclonic Storm': '#dc2626', 'Super Cyclonic Storm': '#9333ea',
}

function latLonToVec(lat, lon, r) {
  const phi = ((90 - lat) * Math.PI) / 180
  const theta = ((lon + 180) * Math.PI) / 180
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta),
  )
}

function Earth() {
  const ref = useRef()
  useFrame((_, dt) => { ref.current.rotation.y += dt * 0.05 })
  return (
    <group ref={ref}>
      <mesh>
        <sphereGeometry args={[1, 48, 48]} />
        <meshStandardMaterial color="#16324f" wireframe transparent opacity={0.55} />
      </mesh>
      <mesh scale={0.995}>
        <sphereGeometry args={[1, 48, 48]} />
        <meshStandardMaterial color="#0b1c33" transparent opacity={0.9} />
      </mesh>
    </group>
  )
}

function CycloneSpiral({ lat = 15, lon = 85 }) {
  const ref = useRef()
  const pts = useMemo(() => {
    const arr = []
    for (let i = 0; i < 220; i++) {
      const t = i / 220
      const a = t * Math.PI * 7
      const r = 0.02 + t * 0.22
      arr.push(new THREE.Vector3(Math.cos(a) * r, t * 0.35, Math.sin(a) * r))
    }
    return new THREE.BufferGeometry().setFromPoints(arr)
  }, [])
  const base = useMemo(() => latLonToVec(lat, lon, 1.0), [lat, lon])
  useFrame((_, dt) => { ref.current.rotation.y -= dt * 1.4 })
  return (
    <group position={base}>
      {/* eslint-disable-next-line react/no-unknown-property */}
      <lineLoop ref={ref} geometry={pts}>
        {/* eslint-disable-next-line react/no-unknown-property */}
        <lineBasicMaterial color="#38bdf8" transparent opacity={0.95} />
      </lineLoop>
    </group>
  )
}

function StormMarkers({ storms }) {
  const pts = useMemo(() => storms.map((s) => ({
    pos: latLonToVec(s.genesis_lat, s.genesis_lon, 1.01),
    color: CLASS_HEX[s.peak_class] || '#38bdf8',
  })), [storms])
  return (
    <group>
      {pts.map((p, i) => (
        <mesh key={i} position={p.pos}>
          <sphereGeometry args={[0.012, 8, 8]} />
          <meshBasicMaterial color={p.color} />
        </mesh>
      ))}
    </group>
  )
}

export default function Globe3D({ storms = [] }) {
  return (
    <Canvas camera={{ position: [0, 0.6, 2.8] }} style={{ height: '100%', width: '100%' }}>
      <ambientLight intensity={0.9} />
      <pointLight position={[5, 3, 5]} intensity={1.2} />
      <Earth />
      <StormMarkers storms={storms} />
      <CycloneSpiral />
      <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.6} enablePan={false} />
    </Canvas>
  )
}
