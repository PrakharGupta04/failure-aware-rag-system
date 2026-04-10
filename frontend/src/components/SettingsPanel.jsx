/**
 * SettingsPanel.jsx
 * Inline settings bar for switching embedding model, vector store,
 * chunk size, similarity threshold, and LLM backend.
 */
import React from 'react';
import { Settings2 } from 'lucide-react';

/* Reusable pill-toggle group */
function ToggleGroup({ label, options, value, onChange }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <span style={{
        fontSize:      '0.65rem',
        color:         'var(--text-dim)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        fontFamily:    'var(--font-mono)',
      }}>
        {label}
      </span>
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              padding:      '4px 12px',
              borderRadius: '999px',
              border:       `1px solid ${value === opt.value ? 'var(--accent)' : 'var(--border)'}`,
              background:   value === opt.value ? 'var(--accent-dim)' : 'transparent',
              color:        value === opt.value ? 'var(--accent)' : 'var(--text-dim)',
              fontFamily:   'var(--font-mono)',
              fontSize:     '0.72rem',
              cursor:       'pointer',
              transition:   'all 0.15s ease',
              whiteSpace:   'nowrap',
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/* Slider control */
function SliderControl({ label, value, min, max, step, onChange, format }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <span style={{
        fontSize:      '0.65rem',
        color:         'var(--text-dim)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        fontFamily:    'var(--font-mono)',
        display:       'flex',
        justifyContent:'space-between',
      }}>
        <span>{label}</span>
        <span style={{ color: 'var(--accent)' }}>{format ? format(value) : value}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{
          width:     '100%',
          accentColor: 'var(--accent)',
          cursor:    'pointer',
        }}
      />
    </div>
  );
}

export default function SettingsPanel({ settings, onChange, open, onToggle }) {
  return (
    <div style={{
      border:       '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow:     'hidden',
      marginBottom: '20px',
    }}>
      {/* Header */}
      <button
        onClick={onToggle}
        style={{
          width:          '100%',
          display:        'flex',
          alignItems:     'center',
          gap:            '8px',
          padding:        '10px 16px',
          background:     'var(--bg-input)',
          border:         'none',
          color:          'var(--text-dim)',
          cursor:         'pointer',
          fontFamily:     'var(--font-mono)',
          fontSize:       '0.76rem',
          letterSpacing:  '0.06em',
          justifyContent: 'space-between',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Settings2 size={14} />
          EXPERIMENT SETTINGS
        </span>
        <span style={{
          fontSize:  '0.65rem',
          color:     open ? 'var(--accent)' : 'var(--text-faint)',
        }}>
          {open ? 'COLLAPSE ▲' : 'EXPAND ▼'}
        </span>
      </button>

      {open && (
        <div style={{
          padding:             '16px',
          display:             'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap:                 '20px',
          background:          'var(--bg-card)',
          borderTop:           '1px solid var(--border)',
          animation:           'fadeUp 0.2s ease',
        }}>
          <ToggleGroup
            label="Embedding Model"
            options={[
              { value: 'minilm', label: 'MiniLM-L6' },
              { value: 'bge',    label: 'BGE-small' },
            ]}
            value={settings.embeddingModel}
            onChange={(v) => onChange('embeddingModel', v)}
          />

          <ToggleGroup
            label="Vector Store"
            options={[
              { value: 'faiss',  label: 'FAISS' },
              { value: 'chroma', label: 'Chroma' },
            ]}
            value={settings.vectorStore}
            onChange={(v) => onChange('vectorStore', v)}
          />

          <ToggleGroup
            label="Chunk Size (words)"
            options={[
              { value: 200, label: '200' },
              { value: 500, label: '500' },
            ]}
            value={settings.chunkSize}
            onChange={(v) => onChange('chunkSize', v)}
          />

          <ToggleGroup
            label="LLM Backend"
            options={[
              { value: 'ollama', label: 'Ollama (local)' },
              { value: 'openai', label: 'OpenAI' },
            ]}
            value={settings.llmBackend}
            onChange={(v) => onChange('llmBackend', v)}
          />

          <SliderControl
            label="Similarity Threshold"
            value={settings.threshold}
            min={0.1}
            max={0.9}
            step={0.05}
            onChange={(v) => onChange('threshold', v)}
            format={(v) => v.toFixed(2)}
          />

          <SliderControl
            label="Top-K Results"
            value={settings.topK}
            min={1}
            max={10}
            step={1}
            onChange={(v) => onChange('topK', v)}
          />
        </div>
      )}
    </div>
  );
}
