/**
 * StatsPanel.jsx
 * Live evaluation statistics fetched from GET /api/stats.
 */
import React, { useEffect, useState } from 'react';
import { BarChart2, RefreshCw } from 'lucide-react';
import { fetchStats } from '../api';

function StatBox({ label, value, accent }) {
  return (
    <div style={{
      background:   'var(--bg)',
      border:       `1px solid ${accent ? 'var(--accent-dim)' : 'var(--border)'}`,
      borderRadius: 'var(--radius)',
      padding:      '12px 14px',
      display:      'flex',
      flexDirection:'column',
      gap:          '4px',
    }}>
      <span style={{
        fontSize:      '0.62rem',
        color:         'var(--text-dim)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        fontFamily:    'var(--font-mono)',
      }}>
        {label}
      </span>
      <span style={{
        fontSize:   '1.4rem',
        fontFamily: 'var(--font-display)',
        fontWeight: 700,
        color:      accent ? 'var(--accent)' : 'var(--text)',
        lineHeight: 1,
      }}>
        {value}
      </span>
    </div>
  );
}

export default function StatsPanel() {
  const [stats, setStats]     = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchStats();
      setStats(data);
    } catch (e) {
      console.warn('Stats unavailable:', e.message);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 10 s
  useEffect(() => {
    load();
    const t = setInterval(load, 10_000);
    return () => clearInterval(t);
  }, []);

  if (!stats) return null;

  return (
    <div style={{
      border:       '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow:     'hidden',
      marginTop:    '28px',
    }}>
      <div style={{
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'space-between',
        padding:        '10px 16px',
        background:     'var(--bg-input)',
        borderBottom:   '1px solid var(--border)',
      }}>
        <span style={{
          display:       'flex',
          alignItems:    'center',
          gap:           '8px',
          fontFamily:    'var(--font-mono)',
          fontSize:      '0.76rem',
          color:         'var(--text-dim)',
          letterSpacing: '0.06em',
        }}>
          <BarChart2 size={14} /> SESSION STATISTICS
        </span>
        <button
          onClick={load}
          disabled={loading}
          style={{
            background: 'transparent',
            border:     'none',
            color:      'var(--text-dim)',
            cursor:     'pointer',
            padding:    '2px',
          }}
        >
          <RefreshCw size={13} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
        </button>
      </div>

      <div style={{
        display:             'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
        gap:                 '8px',
        padding:             '12px',
        background:          'var(--bg-card)',
      }}>
        <StatBox label="Total Queries"   value={stats.total_queries} />
        <StatBox label="Answered"        value={stats.answered} />
        <StatBox label="Rejected"        value={stats.rejected} />
        <StatBox label="Answer Rate"     value={`${stats.answer_rate_pct}%`} accent />
        <StatBox label="Avg Similarity"  value={stats.avg_max_score?.toFixed(3) ?? '—'} />
        <StatBox label="Peak Similarity" value={stats.max_max_score?.toFixed(3) ?? '—'} />
      </div>
    </div>
  );
}
