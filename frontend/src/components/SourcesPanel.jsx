/**
 * SourcesPanel.jsx
 * Collapsible panel listing retrieved document sources with scores.
 */
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';

const scoreColor = (s) => {
  if (s >= 0.7) return '#22d3a0';
  if (s >= 0.5) return '#f59e0b';
  return '#f97316';
};

export default function SourcesPanel({ sources }) {
  const [open, setOpen]         = useState(false);
  const [expanded, setExpanded] = useState({});

  if (!sources || sources.length === 0) return null;

  const toggleSource = (i) =>
    setExpanded((prev) => ({ ...prev, [i]: !prev[i] }));

  return (
    <div style={{
      border:       '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow:     'hidden',
      marginTop:    '20px',
    }}>
      {/* header / toggle */}
      <button
        onClick={() => setOpen((p) => !p)}
        style={{
          width:          '100%',
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'space-between',
          padding:        '10px 16px',
          background:     'var(--bg-input)',
          border:         'none',
          color:          'var(--text-dim)',
          cursor:         'pointer',
          fontFamily:     'var(--font-mono)',
          fontSize:       '0.78rem',
          letterSpacing:  '0.05em',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={14} />
          RETRIEVED SOURCES ({sources.length})
        </span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div style={{ padding: '10px' }}>
          {sources.map((src, i) => (
            <div
              key={i}
              style={{
                border:       '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                marginBottom: i < sources.length - 1 ? '8px' : 0,
                overflow:     'hidden',
              }}
            >
              {/* source header */}
              <button
                onClick={() => toggleSource(i)}
                style={{
                  width:          '100%',
                  display:        'flex',
                  alignItems:     'center',
                  justifyContent: 'space-between',
                  padding:        '8px 12px',
                  background:     'var(--bg-card)',
                  border:         'none',
                  color:          'var(--text)',
                  cursor:         'pointer',
                  fontFamily:     'var(--font-mono)',
                  fontSize:       '0.75rem',
                }}
              >
                <span style={{ color: 'var(--text-dim)' }}>
                  doc_{src.doc_id ?? i} · chunk_{src.chunk_id ?? i}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{
                    color:       scoreColor(src.score),
                    fontWeight:  700,
                  }}>
                    {(src.score * 100).toFixed(1)}%
                  </span>
                  {expanded[i] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </span>
              </button>

              {/* expanded text */}
              {expanded[i] && (
                <div style={{
                  padding:    '10px 12px',
                  background: 'var(--bg)',
                  color:      'var(--text-dim)',
                  fontSize:   '0.78rem',
                  lineHeight: '1.55',
                  borderTop:  '1px solid var(--border)',
                }}>
                  {src.text || src.preview}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
