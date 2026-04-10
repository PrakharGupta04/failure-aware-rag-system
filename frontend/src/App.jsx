/**
 * App.jsx — Root component for the Failure-Aware RAG System UI
 *
 * Layout:
 *  ┌─ Header ─────────────────────────────────────┐
 *  │  Title + server status indicator             │
 *  ├─ Settings Panel (collapsible) ───────────────┤
 *  │  Embedding model / Vector store / etc.       │
 *  ├─ Index Builder ──────────────────────────────┤
 *  ├─ Query Input ────────────────────────────────┤
 *  │  Text area + Submit button                   │
 *  ├─ Loading Animation (conditional) ───────────┤
 *  ├─ Result Panel (conditional) ─────────────────┤
 *  │  Answer card OR Rejection card               │
 *  └─ Stats Panel ─────────────────────────────────┘
 */

import React, { useState, useEffect, useRef } from 'react';
import { Send, Cpu, Wifi, WifiOff }            from 'lucide-react';

import SettingsPanel    from './components/SettingsPanel';
import IndexBuilder     from './components/IndexBuilder';
import LoadingAnimation from './components/LoadingAnimation';
import ResultPanel      from './components/ResultPanel';
import StatsPanel       from './components/StatsPanel';

import { queryRAG, checkHealth } from './api';

/* ── Default experiment settings ────────────────────────── */
const DEFAULT_SETTINGS = {
  embeddingModel: 'minilm',
  vectorStore:    'faiss',
  chunkSize:      200,
  threshold:      0.40,
  topK:           5,
  llmBackend:     'ollama',
};

/* ── Example queries shown as quick-fill chips ───────────── */
const EXAMPLE_QUERIES = [
  'What is machine learning?',
  'How does retrieval-augmented generation work?',
  'What is the Python programming language?',
  'Explain quantum computing.',
  'What causes climate change?',
  'Who invented the internet?',           // likely to be rejected
  'What is the capital of Mars?',         // certain rejection
];

export default function App() {
  const [query, setQuery]             = useState('');
  const [result, setResult]           = useState(null);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [serverOk, setServerOk]       = useState(null);  // null | true | false
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings]       = useState(DEFAULT_SETTINGS);
  const resultRef                     = useRef(null);

  /* ── Health check on mount ──────────────────────────── */
  useEffect(() => {
    checkHealth()
      .then(() => setServerOk(true))
      .catch(() => setServerOk(false));
  }, []);

  /* ── Scroll to result when it appears ─────────────────── */
  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [result]);

  /* ── Settings change handler ──────────────────────────── */
  const handleSettingChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  /* ── Submit query ────────────────────────────────────── */
  const handleSubmit = async (q) => {
    const trimmed = (q || query).trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await queryRAG({
        query:          trimmed,
        embeddingModel: settings.embeddingModel,
        vectorStore:    settings.vectorStore,
        topK:           settings.topK,
        threshold:      settings.threshold,
        llmBackend:     settings.llmBackend,
      });
      setResult(res);
    } catch (e) {
      setError(e.message || 'Unknown error from the backend.');
    } finally {
      setLoading(false);
    }
  };

  /* ── Keyboard shortcut: Cmd/Ctrl+Enter ───────────────── */
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  /* ═══════════════════════════════════════════════════════ */
  return (
    <div style={{
      minHeight:   '100vh',
      background:  'var(--bg)',
      padding:     '0 0 60px',
    }}>
      {/* ── Scanline decorative overlay ─────────────────── */}
      <div style={{
        position:   'fixed',
        inset:      0,
        pointerEvents: 'none',
        zIndex:     0,
        background: 'repeating-linear-gradient(transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
      }} />

      <div style={{
        maxWidth:   'var(--max-w)',
        margin:     '0 auto',
        padding:    '0 20px',
        position:   'relative',
        zIndex:     1,
      }}>

        {/* ════ HEADER ════════════════════════════════════ */}
        <header style={{
          padding:        '36px 0 28px',
          borderBottom:   '1px solid var(--border)',
          marginBottom:   '28px',
          display:        'flex',
          alignItems:     'flex-start',
          justifyContent: 'space-between',
          flexWrap:       'wrap',
          gap:            '12px',
        }}>
          <div>
            {/* Tag line */}
            <div style={{
              fontFamily:    'var(--font-mono)',
              fontSize:      '0.65rem',
              color:         'var(--accent)',
              letterSpacing: '0.18em',
              textTransform: 'uppercase',
              marginBottom:  '8px',
            }}>
              Failure-Aware
            </div>

            {/* Main title */}
            <h1 style={{
              fontFamily:  'var(--font-display)',
              fontWeight:  800,
              fontSize:    'clamp(1.7rem, 5vw, 2.6rem)',
              lineHeight:  1.1,
              letterSpacing: '-0.02em',
              color:       'var(--text)',
            }}>
              RAG{' '}
              <span style={{
                background:          'linear-gradient(135deg, var(--accent) 0%, #a78bfa 100%)',
                WebkitBackgroundClip:'text',
                WebkitTextFillColor: 'transparent',
              }}>
                System
              </span>
            </h1>

            <p style={{
              fontFamily: 'var(--font-mono)',
              fontSize:   '0.78rem',
              color:      'var(--text-dim)',
              marginTop:  '8px',
            }}>
              Intelligent QA · knows when to say "I don't know"
            </p>
          </div>

          {/* Server status badge */}
          <div style={{
            display:      'flex',
            alignItems:   'center',
            gap:          '7px',
            padding:      '6px 14px',
            border:       `1px solid ${serverOk === false ? 'var(--danger)' : serverOk ? 'var(--success)' : 'var(--border)'}`,
            borderRadius: '999px',
            fontFamily:   'var(--font-mono)',
            fontSize:     '0.7rem',
            color:        serverOk === false ? 'var(--danger)' : serverOk ? 'var(--success)' : 'var(--text-dim)',
            background:   serverOk === false ? 'var(--danger-bg)' : serverOk ? 'var(--success-bg)' : 'transparent',
          }}>
            {serverOk === false ? <WifiOff size={12} /> : <Wifi size={12} />}
            {serverOk === null ? 'Connecting…' : serverOk ? 'Backend Online' : 'Backend Offline'}
          </div>
        </header>

        {/* ════ SETTINGS PANEL ════════════════════════════ */}
        <SettingsPanel
          settings={settings}
          onChange={handleSettingChange}
          open={settingsOpen}
          onToggle={() => setSettingsOpen((p) => !p)}
        />

        {/* ════ INDEX BUILDER ════════════════════════════ */}
        <IndexBuilder settings={settings} />

        {/* ════ QUERY INPUT ═══════════════════════════════ */}
        <div style={{
          border:       '1px solid var(--border-bright)',
          borderRadius: 'var(--radius-lg)',
          overflow:     'hidden',
          background:   'var(--bg-input)',
          boxShadow:    loading ? '0 0 0 2px var(--accent-dim)' : 'none',
          transition:   'box-shadow 0.2s ease',
        }}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything… (⌘+Enter to submit)"
            rows={3}
            style={{
              width:       '100%',
              background:  'transparent',
              border:      'none',
              outline:     'none',
              color:       'var(--text)',
              fontFamily:  'var(--font-mono)',
              fontSize:    '0.95rem',
              lineHeight:  '1.65',
              padding:     '18px 20px 12px',
              resize:      'vertical',
              minHeight:   '80px',
            }}
          />

          {/* Bottom bar: example chips + submit */}
          <div style={{
            display:        'flex',
            alignItems:     'center',
            justifyContent: 'space-between',
            padding:        '8px 14px 10px',
            borderTop:      '1px solid var(--border)',
            flexWrap:       'wrap',
            gap:            '8px',
          }}>
            {/* Example query chips */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {EXAMPLE_QUERIES.slice(0, 4).map((eq) => (
                <button
                  key={eq}
                  onClick={() => { setQuery(eq); handleSubmit(eq); }}
                  style={{
                    padding:      '3px 10px',
                    border:       '1px solid var(--border)',
                    borderRadius: '999px',
                    background:   'transparent',
                    color:        'var(--text-dim)',
                    fontFamily:   'var(--font-mono)',
                    fontSize:     '0.68rem',
                    cursor:       'pointer',
                    whiteSpace:   'nowrap',
                    transition:   'all 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.borderColor = 'var(--accent)';
                    e.target.style.color = 'var(--accent)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.borderColor = 'var(--border)';
                    e.target.style.color = 'var(--text-dim)';
                  }}
                >
                  {eq.length > 28 ? eq.slice(0, 26) + '…' : eq}
                </button>
              ))}
            </div>

            {/* Submit button */}
            <button
              onClick={() => handleSubmit()}
              disabled={loading || !query.trim()}
              style={{
                display:      'flex',
                alignItems:   'center',
                gap:          '8px',
                padding:      '8px 20px',
                borderRadius: '999px',
                border:       'none',
                background:   loading || !query.trim()
                  ? 'var(--accent-dim)'
                  : 'linear-gradient(135deg, var(--accent), #a78bfa)',
                color:        '#fff',
                fontFamily:   'var(--font-mono)',
                fontSize:     '0.8rem',
                fontWeight:   700,
                cursor:       loading || !query.trim() ? 'not-allowed' : 'pointer',
                opacity:      !query.trim() ? 0.5 : 1,
                transition:   'all 0.2s ease',
                boxShadow:    loading || !query.trim() ? 'none' : '0 0 20px var(--accent-glow)',
                letterSpacing:'0.04em',
              }}
            >
              {loading ? (
                <>
                  <Cpu size={14} style={{ animation: 'spin 1s linear infinite' }} />
                  Processing…
                </>
              ) : (
                <>
                  <Send size={14} />
                  Submit
                </>
              )}
            </button>
          </div>
        </div>

        {/* ════ LOADING ANIMATION ════════════════════════ */}
        {loading && <LoadingAnimation />}

        {/* ════ ERROR BANNER ══════════════════════════════ */}
        {error && !loading && (
          <div style={{
            marginTop:    '20px',
            padding:      '14px 18px',
            border:       '1px solid var(--danger)',
            borderRadius: 'var(--radius)',
            background:   'var(--danger-bg)',
            color:        'var(--danger)',
            fontFamily:   'var(--font-mono)',
            fontSize:     '0.82rem',
            animation:    'fadeUp 0.3s ease',
          }}>
            ⚠ {error}
          </div>
        )}

        {/* ════ RESULT ════════════════════════════════════ */}
        {result && !loading && (
          <div ref={resultRef} style={{ marginTop: '24px' }}>
            <ResultPanel result={result} />
          </div>
        )}

        {/* ════ STATS ═════════════════════════════════════ */}
        <StatsPanel />

      </div>

      {/* ── Global spin keyframe (for icons) ─────────────── */}
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
