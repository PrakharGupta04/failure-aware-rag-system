/**
 * IndexBuilder.jsx
 * Panel to trigger a (re-)build of the vector index on the backend.
 * Shows live status feedback during the build.
 */
import React, { useState } from 'react';
import { Database, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { buildIndex } from '../api';

export default function IndexBuilder({ settings }) {
  const [status, setStatus]   = useState(null);  // null | 'building' | 'done' | 'error'
  const [msg, setMsg]         = useState('');

  const handleBuild = async () => {
    setStatus('building');
    setMsg('Building index… this may take 1–3 minutes on first run.');
    try {
      const res = await buildIndex({
        embeddingModel: settings.embeddingModel,
        vectorStore:    settings.vectorStore,
        chunkSize:      settings.chunkSize,
        forceRebuild:   true,
      });
      setStatus('done');
      setMsg(
        `Index ready — ${res.num_vectors} vectors · ` +
        `${res.embedding_model} · ${res.vector_store} · chunk=${res.chunk_size}`
      );
    } catch (e) {
      setStatus('error');
      setMsg(`Build failed: ${e.message}`);
    }
  };

  const statusColor = {
    building: 'var(--warning)',
    done:     'var(--success)',
    error:    'var(--danger)',
  }[status] || 'var(--text-dim)';

  const Icon = {
    building: () => <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} />,
    done:     () => <CheckCircle size={14} />,
    error:    () => <AlertCircle size={14} />,
  }[status] || (() => <Database size={14} />);

  return (
    <div style={{
      display:    'flex',
      alignItems: 'center',
      gap:        '12px',
      padding:    '10px 14px',
      border:     '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      background: 'var(--bg-card)',
      marginBottom: '16px',
      flexWrap:   'wrap',
    }}>
      <button
        onClick={handleBuild}
        disabled={status === 'building'}
        style={{
          display:      'flex',
          alignItems:   'center',
          gap:          '7px',
          padding:      '7px 16px',
          border:       '1px solid var(--accent-dim)',
          borderRadius: '999px',
          background:   status === 'building' ? 'var(--accent-dim)' : 'transparent',
          color:        'var(--accent)',
          fontFamily:   'var(--font-mono)',
          fontSize:     '0.74rem',
          cursor:       status === 'building' ? 'not-allowed' : 'pointer',
          transition:   'all 0.15s',
          whiteSpace:   'nowrap',
        }}
      >
        <RefreshCw size={13} />
        {status === 'building' ? 'Building…' : 'Rebuild Index'}
      </button>

      {status && (
        <span style={{
          display:    'flex',
          alignItems: 'center',
          gap:        '6px',
          fontFamily: 'var(--font-mono)',
          fontSize:   '0.74rem',
          color:      statusColor,
          animation:  'fadeUp 0.2s ease',
        }}>
          <Icon /> {msg}
        </span>
      )}
    </div>
  );
}
