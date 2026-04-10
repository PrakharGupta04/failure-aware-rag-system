/**
 * ResultPanel.jsx
 * Renders the RAG response — either a successful answer or a rejection.
 */
import React from 'react';
import { AlertTriangle, CheckCircle, Zap } from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';
import SourcesPanel    from './SourcesPanel';

/* ── Rejection panel ─────────────────────────────────────── */
function RejectionCard({ rejection }) {
  return (
    <div style={{
      border:       '1px solid var(--danger)',
      borderRadius: 'var(--radius-lg)',
      overflow:     'hidden',
      animation:    'fadeUp 0.35s ease',
    }}>
      {/* Red header */}
      <div style={{
        display:    'flex',
        alignItems: 'center',
        gap:        '10px',
        padding:    '14px 18px',
        background: 'var(--danger-bg)',
        borderBottom: '1px solid var(--danger)',
      }}>
        <AlertTriangle size={18} color="var(--danger)" />
        <span style={{
          fontFamily:    'var(--font-mono)',
          fontSize:      '0.8rem',
          color:         'var(--danger)',
          letterSpacing: '0.08em',
          fontWeight:    700,
        }}>
          QUERY REJECTED — INSUFFICIENT CONTEXT
        </span>
      </div>

      {/* Body */}
      <div style={{
        padding:    '20px 18px',
        background: 'var(--bg-card)',
      }}>
        {/* Main message */}
        <p style={{
          fontSize:   '1rem',
          color:      'var(--text)',
          lineHeight: '1.65',
          marginBottom: '20px',
        }}>
          {rejection.message}
        </p>

        {/* Reason + score */}
        <div style={{
          display:      'grid',
          gridTemplateColumns: '1fr 1fr',
          gap:          '12px',
        }}>
          <div style={{
            padding:      '12px 14px',
            border:       '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            background:   'var(--bg)',
          }}>
            <div style={{ fontSize: '0.62rem', color: 'var(--text-dim)', letterSpacing: '0.1em', marginBottom: '4px' }}>
              REASON
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text)', lineHeight: '1.5' }}>
              {rejection.reason}
            </div>
          </div>

          <div style={{
            padding:      '12px 14px',
            border:       '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            background:   'var(--bg)',
          }}>
            <div style={{ fontSize: '0.62rem', color: 'var(--text-dim)', letterSpacing: '0.1em', marginBottom: '4px' }}>
              MAX SIMILARITY SCORE
            </div>
            <div style={{
              fontSize:   '1.6rem',
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              color:      'var(--danger)',
            }}>
              {(rejection.max_similarity_score * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px' }}>
              threshold: {(rejection.threshold * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Success panel ────────────────────────────────────────── */
function AnswerCard({ answer, confidence, sources, meta }) {
  return (
    <div style={{
      border:       '1px solid var(--border-bright)',
      borderRadius: 'var(--radius-lg)',
      overflow:     'hidden',
      animation:    'fadeUp 0.35s ease',
    }}>
      {/* Header */}
      <div style={{
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'space-between',
        padding:        '14px 18px',
        background:     'var(--bg-input)',
        borderBottom:   '1px solid var(--border)',
      }}>
        <span style={{
          display:    'flex',
          alignItems: 'center',
          gap:        '8px',
          fontFamily: 'var(--font-mono)',
          fontSize:   '0.78rem',
          color:      'var(--success)',
          letterSpacing: '0.06em',
        }}>
          <CheckCircle size={15} /> ANSWER GENERATED
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ConfidenceBadge level={confidence} />
          {meta && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize:   '0.68rem',
              color:      'var(--text-dim)',
            }}>
              {(meta.max_similarity_score * 100).toFixed(1)}% match
            </span>
          )}
        </div>
      </div>

      {/* Answer text */}
      <div style={{
        padding:    '22px 18px',
        background: 'var(--bg-card)',
      }}>
        <div style={{
          display:       'flex',
          alignItems:    'flex-start',
          gap:           '12px',
          marginBottom:  '6px',
        }}>
          <Zap size={16} color="var(--accent)" style={{ marginTop: '3px', flexShrink: 0 }} />
          <p style={{
            fontSize:   '1.05rem',
            lineHeight: '1.75',
            color:      'var(--text)',
            fontFamily: 'var(--font-mono)',
            whiteSpace: 'pre-wrap',
          }}>
            {answer}
          </p>
        </div>

        {/* Sources */}
        <SourcesPanel sources={sources} />
      </div>
    </div>
  );
}

/* ── Main export ─────────────────────────────────────────── */
export default function ResultPanel({ result }) {
  if (!result) return null;

  if (result.status === 'rejected') {
    return <RejectionCard rejection={result.rejection} />;
  }

  return (
    <AnswerCard
      answer={result.answer}
      confidence={result.confidence}
      sources={result.sources}
      meta={result.meta}
    />
  );
}
