import axios from 'axios';

const BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

export const uploadFile = (file, sourceType, tenantId = 1) => {
  const form = new FormData();
  form.append('file', file);
  form.append('source_type', sourceType);
  form.append('tenant_id', tenantId);
  return axios.post(`${BASE}/upload/`, form);
};

export const getRecords = (filters = {}) => {
  return axios.get(`${BASE}/records/`, { params: filters });
};

export const getStats = () => {
  return axios.get(`${BASE}/stats/`);
};

export const doAction = (id, action, flagReason = '') => {
  return axios.patch(`${BASE}/records/${id}/action/`, {
    action,
    flag_reason: flagReason,
  });
};