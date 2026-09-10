import { useEffect, useState } from 'react';
import { Network } from 'lucide-react';
import { matchingApi } from '../services/matchingApi';
import { Loading } from '../components/common/Loading';

export const DuplicateClusters = () => {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    matchingApi.getClusters().then(response => { if (active) setRows(response.data); })
      .catch(err => { if (active) setError(err?.response?.data?.detail || err.message || 'Unable to load duplicate clusters.'); });
    return () => { active = false; };
  }, []);
  if (rows === null && !error) return <Loading type="skeleton" rows={6} />;
  return <div className="space-y-5"><div><div className="flex items-center gap-2"><Network className="h-5 w-5 text-blue-700"/><h2 className="text-xl font-bold">Duplicate and Equivalence Clusters</h2></div><p className="text-xs text-slate-500">Persisted AI pairs grouped for whole-cluster review. Functional equivalents are shown separately and are never automatically merged.</p></div>
    {error && <div className="rounded border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{error}</div>}
    {(rows || []).map(row => <article key={row.cluster_id} className="rounded-xl border bg-white p-5"><div className="flex justify-between"><div><p className="font-mono text-xs font-bold text-blue-700">Cluster {row.cluster_id}</p><h3 className="font-bold">{row.member_count} legacy records · {(row.cluster_confidence * 100).toFixed(1)}% mean confidence</h3></div><div className="text-right text-[11px] text-slate-500">Exact {row.classification_counts.EXACT || 0}<br/>Near {row.classification_counts.NEAR_DUPLICATE || 0}<br/>Functional {row.classification_counts.FUNCTIONAL_EQUIVALENT || 0}</div></div><div className="mt-4 grid gap-2 md:grid-cols-2">{row.members.map(member => <div key={member.id} className="rounded-lg border bg-slate-50 p-3 text-xs"><strong>{member.cpse_code} · {member.material_code}</strong><p>{member.description}</p></div>)}</div>{row.functional_equivalent_edges.length > 0 && <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"><strong>Engineering substitution candidates — identity merge blocked</strong>{row.functional_equivalent_edges.map(edge => <p key={edge.match_id} className="mt-1">#{edge.match_id}: {edge.explanation}</p>)}</div>}{row.technical_conflicts.length > 0 && <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">{row.technical_conflicts.length} canonical conflict(s) require reviewer resolution.</div>}</article>)}
    {rows?.length === 0 && <p className="rounded-xl border bg-white p-5 text-sm text-slate-500">No pending duplicate clusters.</p>}
  </div>;
};
