/**
 * ConfidenceBadge.jsx
 * Color-coded badge showing High / Medium / Low confidence.
 */
import React from 'react';

const COLORS = {
  High:   { bg: 'rgba(34,211,160,0.12)',  border: '#22d3a0', text: '#22d3a0' },
  Medium: { bg: 'rgba(245,158,11,0.12)',  border: '#f59e0b', text: '#f59e0b' },
  Low:    { bg: 'rgba(249,115,22,0.12)',  border: '#f97316', text: '#f97316' },
};

export default function ConfidenceBadge({ level }) {
  const c = COLORS[level] || COLORS.Low;
  return (
    <span style={{
      display:       'inline-flex',
      alignItems:    'center',
      gap:           '6px',
      padding:       '3px 10px',
      borderRadius:  '999px',
      border:        `1px solid ${c.border}`,
      background:    c.bg,
      color:         c.text,
      fontSize:      '0.72rem',
      fontFamily:    'var(--font-mono)',
      fontWeight:    700,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
    }}>
      {/* pulsing dot */}
      <span style={{
        width:        '6px',
        height:       '6px',
        borderRadius: '50%',
        background:   c.border,
        boxShadow:    `0 0 6px ${c.border}`,
      }} />
      {level}
    </span>
  );
}
