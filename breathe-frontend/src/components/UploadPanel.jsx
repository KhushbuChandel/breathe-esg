import { useState } from 'react';
import { uploadFile } from '../api';

const SOURCE_TYPES = [
  { value: 'SAP',     label: 'SAP — Fuel & Procurement',   color: '#2b6cb0' },
  { value: 'UTILITY', label: 'Utility — Electricity Data', color: '#276749' },
  { value: 'TRAVEL',  label: 'Travel — Flights / Hotels',  color: '#744210' },
];

export default function UploadPanel({ onDone }) {
  const [sourceType, setSourceType] = useState('SAP');
  const [file, setFile]             = useState(null);
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState(null);
  const [error, setError]           = useState(null);
  const [dragging, setDragging]     = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await uploadFile(file, sourceType);
      setResult(res.data);
      onDone();
    } catch (e) {
      setError(e.response?.data?.error || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 28, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20 }}>Upload Data</h2>

      {/* Source type selector */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: '#718096', marginBottom: 8 }}>Source Type</div>
        <div style={{ display: 'flex', gap: 10 }}>
          {SOURCE_TYPES.map(s => (
            <button key={s.value} onClick={() => setSourceType(s.value)} style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: '2px solid',
              borderColor: sourceType === s.value ? s.color : '#e2e8f0',
              background: sourceType === s.value ? s.color : '#fff',
              color: sourceType === s.value ? '#fff' : '#4a5568',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 600,
              transition: 'all 0.15s',
            }}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput').click()}
        style={{
          border: `2px dashed ${dragging ? '#3182ce' : '#cbd5e0'}`,
          borderRadius: 10,
          padding: '36px 20px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? '#ebf8ff' : '#f7fafc',
          transition: 'all 0.2s',
          marginBottom: 16,
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
        <div style={{ fontWeight: 600, color: '#2d3748' }}>
          {file ? file.name : 'Drop CSV here or click to browse'}
        </div>
        <div style={{ fontSize: 12, color: '#a0aec0', marginTop: 4 }}>
          Accepts .csv files
        </div>
        <input
          id="fileInput"
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={e => setFile(e.target.files[0])}
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        style={{
          width: '100%',
          padding: '12px',
          background: (!file || loading) ? '#cbd5e0' : '#3182ce',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          fontWeight: 700,
          fontSize: 15,
          cursor: (!file || loading) ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Processing...' : 'Upload & Parse'}
      </button>

      {/* Result */}
      {result && (
        <div style={{ marginTop: 16, padding: 14, background: '#f0fff4', borderRadius: 8, border: '1px solid #9ae6b4' }}>
          <div style={{ fontWeight: 700, color: '#276749' }}>✅ Upload successful</div>
          <div style={{ fontSize: 13, color: '#2f855a', marginTop: 4 }}>
            {result.records_created} records created · {result.errors.length} errors
          </div>
          {result.errors.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {result.errors.map((e, i) => (
                <div key={i} style={{ fontSize: 12, color: '#c53030' }}>Row {e.row}: {e.reason}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={{ marginTop: 16, padding: 14, background: '#fff5f5', borderRadius: 8, border: '1px solid #feb2b2' }}>
          <div style={{ color: '#c53030', fontWeight: 600 }}>❌ {error}</div>
        </div>
      )}
    </div>
  );
}