import { useState, useEffect, useCallback } from 'react';
import { getRecords, getStats } from './api';
import StatCard from './components/StatCard';
import UploadPanel from './components/UploadPanel';
import RecordTable from './components/RecordTable';
import Charts from './components/Charts';

const FILTERS = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'Flagged', value: 'FLAGGED' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Locked', value: 'LOCKED' },
];

const SOURCE_FILTERS = [
  { label: 'All Sources', value: '' },
  { label: 'SAP', value: 'SAP' },
  { label: 'Utility', value: 'UTILITY' },
  { label: 'Travel', value: 'TRAVEL' },
];

export default function App() {
  const [tab, setTab] = useState('dashboard');
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);

    try {
      const [recRes, statRes] = await Promise.all([
        getRecords({
          status: statusFilter,
          source_type: sourceFilter,
        }),
        getStats(),
      ]);

      setRecords(recRes.data.records);
      setStats(statRes.data);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, sourceFilter]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const totalCO2e = stats
    ? (stats.total_co2e_kg / 1000).toFixed(2)
    : '—';

  return (
    <div style={{ minHeight: '100vh', background: '#f0f4f8' }}>

      {/* Header */}
      <div
        style={{
          background: '#1a202c',
          padding: '0 32px',
          display: 'flex',
          alignItems: 'center',
          gap: 32,
        }}
      >

        {/* Logo */}
        <div
          style={{
            color: '#fff',
            fontWeight: 800,
            fontSize: 20,
            padding: '18px 0',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <img
            src="/plant.png"
            alt="logo"
            style={{
              width: 28,
              height: 28,
            }}
          />

          Breathe ESG
        </div>

        {/* Navigation */}
        <div style={{ display: 'flex', gap: 4 }}>
          {[
            ['dashboard', '📊 Dashboard'],
            ['upload', '📤 Upload'],
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              style={{
                padding: '18px 20px',
                background: 'none',
                border: 'none',
                borderBottom:
                  tab === key
                    ? '3px solid #68d391'
                    : '3px solid transparent',
                color:
                  tab === key
                    ? '#fff'
                    : '#a0aec0',
                fontWeight: 600,
                fontSize: 14,
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Company */}
        <div
          style={{
            marginLeft: 'auto',
            color: '#68d391',
            fontWeight: 600,
            fontSize: 13,
          }}
        >
          Breathe ESG
        </div>
      </div>

      <div
        style={{
          padding: 32,
          maxWidth: 1400,
          margin: '0 auto',
        }}
      >

        {/* Upload Page */}
        {tab === 'upload' && (
          <UploadPanel
            onDone={() => {
              fetchAll();
              setTab('dashboard');
            }}
          />
        )}

        {/* Dashboard */}
        {tab === 'dashboard' && (
          <>
            {/* Stat Cards */}
            <div
              style={{
                display: 'flex',
                gap: 16,
                marginBottom: 24,
                flexWrap: 'wrap',
              }}
            >
              <StatCard
                label="Total Records"
                value={stats?.total_records ?? '—'}
                color="#3182ce"
              />

              <StatCard
                label="Total CO₂e"
                value={`${totalCO2e} t`}
                color="#e53e3e"
                sub="tonnes CO2 equivalent"
              />

              <StatCard
                label="Pending Review"
                value={stats?.by_status?.PENDING ?? 0}
                color="#d69e2e"
              />

              <StatCard
                label="Flagged"
                value={stats?.by_status?.FLAGGED ?? 0}
                color="#c53030"
              />

              <StatCard
                label="Approved"
                value={stats?.by_status?.APPROVED ?? 0}
                color="#276749"
              />

              <StatCard
                label="Locked"
                value={stats?.by_status?.LOCKED ?? 0}
                color="#2b6cb0"
              />
            </div>

            {/* Charts */}
            <div style={{ marginBottom: 24 }}>
              <Charts stats={stats} />
            </div>

            {/* Records Table */}
            <div
              style={{
                background: '#fff',
                borderRadius: 12,
                boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              }}
            >
              <div
                style={{
                  padding: '20px 24px',
                  borderBottom: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  flexWrap: 'wrap',
                }}
              >
                <h2
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    marginRight: 8,
                  }}
                >
                  Emission Records
                </h2>

                {/* Status Filter */}
                <div style={{ display: 'flex', gap: 6 }}>
                  {FILTERS.map((f) => (
                    <button
                      key={f.value}
                      onClick={() => setStatusFilter(f.value)}
                      style={{
                        padding: '5px 12px',
                        borderRadius: 20,
                        border: '1px solid',
                        borderColor:
                          statusFilter === f.value
                            ? '#3182ce'
                            : '#e2e8f0',
                        background:
                          statusFilter === f.value
                            ? '#ebf8ff'
                            : '#fff',
                        color:
                          statusFilter === f.value
                            ? '#2b6cb0'
                            : '#4a5568',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                {/* Source Filter */}
                <div
                  style={{
                    display: 'flex',
                    gap: 6,
                    marginLeft: 8,
                  }}
                >
                  {SOURCE_FILTERS.map((f) => (
                    <button
                      key={f.value}
                      onClick={() => setSourceFilter(f.value)}
                      style={{
                        padding: '5px 12px',
                        borderRadius: 20,
                        border: '1px solid',
                        borderColor:
                          sourceFilter === f.value
                            ? '#805ad5'
                            : '#e2e8f0',
                        background:
                          sourceFilter === f.value
                            ? '#faf5ff'
                            : '#fff',
                        color:
                          sourceFilter === f.value
                            ? '#553c9a'
                            : '#4a5568',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                {loading && (
                  <span
                    style={{
                      fontSize: 12,
                      color: '#a0aec0',
                      marginLeft: 'auto',
                    }}
                  >
                    Refreshing...
                  </span>
                )}
              </div>

              <RecordTable
                records={records}
                onRefresh={fetchAll}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}