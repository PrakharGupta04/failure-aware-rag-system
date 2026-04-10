/**
 * LoadingAnimation.jsx
 * Animated "thinking" indicator shown while the backend processes the query.
 */
import React, { useEffect, useState } from 'react';

const STEPS = [
  'Encoding query…',
  'Searching vector index…',
  'Evaluating similarity…',
  'Generating answer…',
];

export default function LoadingAnimation() {
  const [step, setStep]     = useState(0);
  const [dots, setDots]     = useState('');

  // Cycle through steps every 1.4 s
  useEffect(() => {
    const stepTimer = setInterval(
      () => setStep((s) => (s + 1) % STEPS.length),
      1400
    );
    return () => clearInterval(stepTimer);
  }, []);

  // Animate trailing dots
  useEffect(() => {
    const dotTimer = setInterval(
      () => setDots((d) => (d.length < 3 ? d + '.' : '')),
      420
    );
    return () => clearInterval(dotTimer);
  }, []);

  return (
    <div style={{
      display:        'flex',
      flexDirection:  'column',
      alignItems:     'center',
      justifyContent: 'center',
      padding:        '52px 0',
      gap:            '28px',
      animation:      'fadeUp 0.4s ease',
    }}>
      {/* Pulsing radar rings */}
      <div style={{ position: 'relative', width: '60px', height: '60px' }}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              position:     'absolute',
              inset:        0,
              borderRadius: '50%',
              border:       '2px solid var(--accent)',
              animation:    `pulse-ring 1.8s ease-out ${i * 0.6}s infinite`,
              opacity:      0,
            }}
          />
        ))}
        {/* center dot */}
        <span style={{
          position:     'absolute',
          inset:        '50%',
          transform:    'translate(-50%, -50%)',
          width:        '10px',
          height:       '10px',
          borderRadius: '50%',
          background:   'var(--accent)',
          boxShadow:    '0 0 14px var(--accent)',
        }} />
      </div>

      {/* Step label */}
      <div style={{
        fontFamily:   'var(--font-mono)',
        fontSize:     '0.82rem',
        color:        'var(--text-dim)',
        letterSpacing:'0.06em',
        minWidth:     '220px',
        textAlign:    'center',
      }}>
        {STEPS[step]}{dots}
      </div>

      {/* Progress bar */}
      <div style={{
        width:        '200px',
        height:       '2px',
        background:   'var(--border)',
        borderRadius: '1px',
        overflow:     'hidden',
      }}>
        <div style={{
          height:     '100%',
          background: `linear-gradient(90deg, var(--accent-dim), var(--accent))`,
          borderRadius: '1px',
          width:      `${((step + 1) / STEPS.length) * 100}%`,
          transition: 'width 0.5s ease',
        }} />
      </div>
    </div>
  );
}
