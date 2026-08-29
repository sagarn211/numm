/**
 * Formatters and helper utilities for National Unified Material Master (NUMM)
 */

export const getCPSEBadgeColor = (cpse) => {
  const code = (cpse || '').toUpperCase();
  switch (code) {
    case 'ONGC':
      return 'bg-amber-100 text-amber-800 border-amber-300';
    case 'NTPC':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'SAIL':
      return 'bg-slate-100 text-slate-800 border-slate-300';
    case 'CIL':
      return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    case 'BHEL':
      return 'bg-indigo-100 text-indigo-800 border-indigo-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
};

export const getStatusBadgeColor = (status) => {
  const s = (status || '').toLowerCase();
  if (s.includes('match') || s === 'approved' || s === 'success' || s === 'active') {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  }
  if (s.includes('pending') || s.includes('review') || s === 'processing') {
    return 'bg-amber-50 text-amber-700 border-amber-200';
  }
  if (s.includes('duplicate') || s === 'rejected' || s === 'failed') {
    return 'bg-rose-50 text-rose-700 border-rose-200';
  }
  return 'bg-slate-50 text-slate-700 border-slate-200';
};

export const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  return new Intl.NumberFormat('en-IN').format(num);
};

export const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export const formatConfidence = (val) => {
  if (val === null || val === undefined) return '0%';
  const num = typeof val === 'number' ? val : parseFloat(val);
  return `${num.toFixed(1)}%`;
};
