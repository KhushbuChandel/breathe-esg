export default function StatCard({ label, value, sub, color = '#3182ce' }) {
  return (
    <div style={{
      background: '#fff',
      borderRadius: 12,
      padding: '20px 24px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
      borderTop: `4px solid ${color}`,
      minWidth: 180,
    }}>
      <div style={{ fontSize: 13, color: '#718096', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: '#1a202c' }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: '#a0aec0', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}