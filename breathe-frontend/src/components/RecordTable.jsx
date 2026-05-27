import { useState } from 'react';
import { doAction } from '../api';

const STATUS_COLORS = {
  PENDING:  { bg: '#fffbeb', text: '#92400e', border: '#fcd34d' },
  FLAGGED:  { bg: '#fff5f5', text: '#c53030', border: '#fc8181' },
  APPROVED: { bg: '#f0fff4', text: '#276749', border: '#9ae6b4' },
  LOCKED:   { bg: '#ebf4ff', text: '#2b6cb0', border: '#90cdf4' },
};

const SCOPE_LABELS = {
  SCOPE_1: '🔴 Scope 1',
  SCOPE_2: '🟡 Scope 2',
  SCOPE_3: '🔵 Scope 3',
};

export default function RecordTable({ records, onRefresh }) {
  const [flagModal, setFlagModal] = useState(null);
  const [flagReason, setFlagReason] = useState('');
  const [loading, setLoading] = useState(null);

  const act = async (id, action, reason = '') => {
    setLoading(id);
    try {
      await doAction(id, action, reason);
      onRefresh();
    } finally {
      setLoading(null);
      setFlagModal(null);
      setFlagReason('');
    }
  };

  if (records.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: '#a0aec0' }}>
        <div style={{ fontSize: 40 }}>📭</div>
        <div style={{ marginTop: 12, fontSize: 15 }}>No records found. Upload a file to get started.</div>
      </div>
    );
  }

  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>
              {['ID', 'Source', 'Scope', 'Description', 'Raw Value', 'CO₂e (kg)', 'Period', 'Facility', 'Status', 'Actions'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: '#4a5568', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((r, i) => {
              const s = STATUS_COLORS[r.status] || STATUS_COLORS.PENDING;
              return (
                <tr key={r.id} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb', borderBottom: '1px solid #e2e8f0' }}>
                  <td style={{ padding: '10px 12px', color: '#718096' }}>#{r.id}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                      background: r.source_type === 'SAP' ? '#ebf8ff' : r.source_type === 'UTILITY' ? '#f0fff4' : '#fffbeb',
                      color: r.source_type === 'SAP' ? '#2b6cb0' : r.source_type === 'UTILITY' ? '#276749' : '#744210',
                    }}>{r.source_type}</span>
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>{SCOPE_LABELS[r.scope]}</td>
                  <td style={{ padding: '10px 12px', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={r.description}>{r.description}</td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>{r.raw_quantity} {r.raw_unit}</td>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: '#2d3748' }}>
                    {r.normalized_quantity.toFixed(2)}
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: '#718096', fontSize: 12 }}>
                    {r.period_start}<br />{r.period_end !== r.period_start ? `→ ${r.period_end}` : ''}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#718096' }}>{r.facility_name || '—'}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                      background: s.bg, color: s.text, border: `1px solid ${s.border}` }}>
                      {r.status}
                    </span>
                    {r.flag_reason && (
                      <div style={{ fontSize: 11, color: '#c53030', marginTop: 3 }} title={r.flag_reason}>
                        ⚠ {r.flag_reason.slice(0, 30)}...
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                    {r.status === 'PENDING' && (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={() => act(r.id, 'approve')} disabled={loading === r.id}
                          style={{ padding: '4px 10px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                          ✓ Approve
                        </button>
                        <button onClick={() => setFlagModal(r.id)}
                          style={{ padding: '4px 10px', background: '#c53030', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                          ⚑ Flag
                        </button>
                      </div>
                    )}
                    {r.status === 'FLAGGED' && (
                      <button onClick={() => act(r.id, 'approve')} disabled={loading === r.id}
                        style={{ padding: '4px 10px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                        ✓ Approve
                      </button>
                    )}
                    {r.status === 'APPROVED' && (
                      <button onClick={() => act(r.id, 'lock')} disabled={loading === r.id}
                        style={{ padding: '4px 10px', background: '#2b6cb0', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                        🔒 Lock
                      </button>
                    )}
                    {r.status === 'LOCKED' && (
                      <span style={{ fontSize: 12, color: '#a0aec0' }}>🔒 Locked</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Flag Modal */}
      {flagModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 28, width: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <h3 style={{ marginBottom: 12 }}>Flag Record #{flagModal}</h3>
            <p style={{ color: '#718096', fontSize: 13, marginBottom: 16 }}>Describe why this record needs attention:</p>
            <textarea
              value={flagReason}
              onChange={e => setFlagReason(e.target.value)}
              placeholder="e.g. Unusually high consumption — verify meter reading"
              style={{ width: '100%', height: 90, padding: 10, borderRadius: 8, border: '1px solid #cbd5e0', fontSize: 13, resize: 'none' }}
            />
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <button onClick={() => act(flagModal, 'flag', flagReason)}
                style={{ flex: 1, padding: 10, background: '#c53030', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer' }}>
                Submit Flag
              </button>
              <button onClick={() => setFlagModal(null)}
                style={{ flex: 1, padding: 10, background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}