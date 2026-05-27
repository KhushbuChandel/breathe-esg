import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const SCOPE_COLORS  = { SCOPE_1: '#fc8181', SCOPE_2: '#f6e05e', SCOPE_3: '#63b3ed' };
const STATUS_COLORS = { PENDING: '#f6ad55', FLAGGED: '#fc8181', APPROVED: '#68d391', LOCKED: '#63b3ed' };

export default function Charts({ stats }) {
  if (!stats) return null;

  const scopeData = Object.entries(stats.by_scope || {}).map(([k, v]) => ({
    name: k.replace('_', ' '), value: Math.round(v), fill: SCOPE_COLORS[k] || '#a0aec0',
  }));

  const statusData = Object.entries(stats.by_status || {}).map(([k, v]) => ({
    name: k, value: v, fill: STATUS_COLORS[k] || '#a0aec0',
  }));

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      {/* CO2e by Scope */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
        <div style={{ fontWeight: 700, marginBottom: 16, color: '#2d3748' }}>CO₂e by Scope (kg)</div>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={scopeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
              {scopeData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Records by Status */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
        <div style={{ fontWeight: 700, marginBottom: 16, color: '#2d3748' }}>Records by Status</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={statusData}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {statusData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}