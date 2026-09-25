import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

const CLASS_HEX = {
  Depression: '#64748b', 'Deep Depression': '#0284c7', 'Cyclonic Storm': '#0d9488',
  'Severe Cyclonic Storm': '#ca8a04', 'Very Severe Cyclonic Storm': '#ea580c',
  'Extremely Severe Cyclonic Storm': '#dc2626', 'Super Cyclonic Storm': '#9333ea',
}

function latLonToVec(lat, lon, r, out = new THREE.Vector3()) {
  const phi = ((90 - lat) * Math.PI) / 180
  const theta = ((lon + 180) * Math.PI) / 180
  return out.set(-r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(theta))
}

function Spin({ children, speed = 0.06 }) {
  const ref = useRef()
  useFrame((_, dt) => { ref.current.rotation.y += dt * speed })
  return <group ref={ref}>{children}</group>
}

/** Dotted-globe surface: fibonacci points read as a solid planet from afar. */
function DotSphere() {
  const geo = useMemo(() => {
    const N = 2600
    const pos = new Float32Array(N * 3)
    const v = new THREE.Vector3()
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2
      const rad = Math.sqrt(Math.max(0, 1 - y * y))
      const th = i * 2.399963
      v.set(Math.cos(th) * rad, y, Math.sin(th) * rad)
      pos.set([v.x, v.y, v.z], i * 3)
    }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    return g
  }, [])
  return (
    <>
      <mesh>
        <sphereGeometry args={[0.985, 64, 64]} />
        <meshBasicMaterial color="#0a1628" transparent opacity={0.96} />
      </mesh>
      {/* eslint-disable-next-line react/no-unknown-property */}
      <points geometry={geo}>
        {/* eslint-disable-next-line react/no-unknown-property */}
        <pointsMaterial color="#2f6db3" size={0.0085} transparent opacity={0.85} sizeAttenuation />
      </points>
    </>
  )
}

function Glow() {
  return (
    <>
      <mesh scale={1.0}>
        <sphereGeometry args={[1, 48, 48]} />
        <meshBasicMaterial color="#1d4ed8" transparent opacity={0.06} side={THREE.BackSide} depthWrite={false} />
      </mesh>
      <mesh scale={1.12}>
        <sphereGeometry args={[1, 48, 48]} />
        <meshBasicMaterial color="#38bdf8" transparent opacity={0.05} side={THREE.BackSide} depthWrite={false} />
      </mesh>
    </>
  )
}

function Graticule() {
  const lines = useMemo(() => {
    const geos = []
    for (const lat of [-60, -30, 0, 30, 60]) {
      const pts = []
      for (let i = 0; i <= 128; i++) pts.push(latLonToVec(lat, (i / 128) * 360 - 180, 0.988))
      geos.push(new THREE.BufferGeometry().setFromPoints(pts))
    }
    for (let k = 0; k < 12; k++) {
      const pts = []
      for (let i = 0; i <= 128; i++) pts.push(latLonToVec((i / 128) * 360 - 180, k * 30 - 180, 0.988))
      geos.push(new THREE.BufferGeometry().setFromPoints(pts))
    }
    return geos
  }, [])
  return (
    <group>
      {lines.map((g, i) => (
        // eslint-disable-next-line react/no-unknown-property
        <lineLoop key={i} geometry={g}>
          {/* eslint-disable-next-line react/no-unknown-property */}
          <lineBasicMaterial color="#274a75" transparent opacity={0.5} />
        </lineLoop>
      ))}
    </group>
  )
}

/** Genesis → peak arcs + pulsing genesis markers. */
function StormArcs({ storms }) {
  const group = useRef()
  const items = useMemo(() => storms
    .filter((s) => Number.isFinite(s.genesis_lat) && Number.isFinite(s.peak_lat))
    .map((s) => {
      const a = latLonToVec(s.genesis_lat, s.genesis_lon, 1.0)
      const b = latLonToVec(s.peak_lat, s.peak_lon, 1.0)
      const mid = a.clone().add(b).multiplyScalar(0.5).normalize().multiplyScalar(1.22)
      const curve = new THREE.QuadraticBezierCurve3(a, mid, b)
      return { geo: new THREE.BufferGeometry().setFromPoints(curve.getPoints(48)),
               pos: a, color: CLASS_HEX[s.peak_class] || '#38bdf8' }
    }), [storms])
  useFrame(({ clock }) => {
    const t = clock.elapsedTime
    group.current?.children.forEach((m, i) => {
      if (m.userData.pulse) {
        const s = 1 + 0.35 * Math.sin(t * 3 + i)
        m.scale.setScalar(s)
      }
    })
  })
  return (
    <group ref={group}>
      {items.map((it, i) => (
        <group key={i}>
          {/* eslint-disable-next-line react/no-unknown-property */}
          <lineLoop geometry={it.geo}>
            {/* eslint-disable-next-line react/no-unknown-property */}
            <lineBasicMaterial color={it.color} transparent opacity={0.75} blending={THREE.AdditiveBlending} depthWrite={false} />
          </lineLoop>
          <mesh position={it.pos} userData={{ pulse: true }}>
            <sphereGeometry args={[0.014, 12, 12]} />
            <meshBasicMaterial color={it.color} />
          </mesh>
        </group>
      ))}
    </group>
  )
}

function CycloneSpiral({ lat = 15, lon = 85 }) {
  const ref = useRef()
  const { geo, halo } = useMemo(() => {
    const mk = (turns, r0, r1, lift, n) => {
      const arr = []
      for (let i = 0; i < n; i++) {
        const t = i / n
        const a = t * Math.PI * 2 * turns
        const r = r0 + (r1 - r0) * t
        arr.push(new THREE.Vector3(Math.cos(a) * r, t * lift, Math.sin(a) * r))
      }
      return new THREE.BufferGeometry().setFromPoints(arr)
    }
    return { geo: mk(4, 0.015, 0.16, 0.3, 260), halo: mk(2.5, 0.05, 0.3, 0.34, 200) }
  }, [])
  const base = useMemo(() => latLonToVec(lat, lon, 1.0), [lat, lon])
  const normal = useMemo(() => base.clone().normalize(), [base])
  useFrame((_, dt) => { ref.current.rotation.y -= dt * 1.6 })
  return (
    <group position={base} quaternion={new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal)}>
      <group ref={ref}>
        {/* eslint-disable-next-line react/no-unknown-property */}
        <lineLoop geometry={geo}>
          {/* eslint-disable-next-line react/no-unknown-property */}
          <lineBasicMaterial color="#7dd3fc" transparent opacity={0.95} blending={THREE.AdditiveBlending} depthWrite={false} />
        </lineLoop>
        {/* eslint-disable-next-line react/no-unknown-property */}
        <lineLoop geometry={halo}>
          {/* eslint-disable-next-line react/no-unknown-property */}
          <lineBasicMaterial color="#38bdf8" transparent opacity={0.4} blending={THREE.AdditiveBlending} depthWrite={false} />
        </lineLoop>
      </group>
    </group>
  )
}

export default function Globe3D({ storms = [] }) {
  return (
    <Canvas camera={{ position: [0, 0.7, 3.0] }} dpr={[1, 1.75]} style={{ height: '100%', width: '100%' }}>
      <ambientLight intensity={1.1} />
      <pointLight position={[5, 3, 5]} intensity={1.4} />
      <Glow />
      <Spin>
        <DotSphere />
        <Graticule />
        <StormArcs storms={storms} />
      </Spin>
      <CycloneSpiral />
      <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} enablePan={false} />
    </Canvas>
  )
}
