import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Network } from 'lucide-react';
import { matchingApi } from '../services/matchingApi';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';
import { Modal } from '../components/common/Modal';

const Tabs = ['PROPOSED', 'UNDER_REVIEW', 'READY_FOR_APPROVAL', 'APPROVED'];
export const DuplicateClusters = () => {
  const [searchParams] = useSearchParams();
  const [tab, setTab] = useState('PROPOSED'), [data,setData]=useState(null), [review,setReview]=useState(null), [busy,setBusy]=useState(false), [error,setError]=useState('');
  const load=useCallback(async()=>{try { const r=await matchingApi.getClusters(tab); setData(r.data); } catch(e){setError(e?.response?.data?.detail||e.message)}},[tab]);
  const act=useCallback(async(fn)=>{setBusy(true);try{const r=await fn(); if(r?.data?.cluster)setReview(r.data.cluster); else if(r?.data?.id)setReview(r.data); await load()}catch(e){setError(e?.response?.data?.detail||e.message)}finally{setBusy(false)}},[load]);
  useEffect(()=>{load()},[load]);
  useEffect(()=>{const clusterId=Number(searchParams.get('cluster')); if(!clusterId)return; act(()=>matchingApi.getCluster(clusterId));},[act,searchParams]);
  const submitForApproval=async()=>{
    if(!review)return;
    setBusy(true);
    try {
      await matchingApi.submitCluster(review.id);
      setReview(null);
      await load();
    } catch(e) {
      setError(e?.response?.data?.detail||e.message);
    } finally {
      setBusy(false);
    }
  };
  const open=async row=>act(async()=>row.status==='PROPOSED' ? matchingApi.startClusterReview(row.id) : matchingApi.getCluster(row.id));
  if(!data&&!error)return <Loading type="skeleton" rows={5}/>;
  return <div className="space-y-5"><div className="flex items-center gap-2"><Network className="h-5 w-5 text-blue-700"/><div><h2 className="text-xl font-bold">Identity Clusters</h2><p className="text-xs text-slate-500">AI pairs are evidence. Persisted clusters are the review unit.</p></div></div>
    {error&&<div className="rounded border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{typeof error==='string'?error:JSON.stringify(error)}</div>}
    <div className="flex gap-2 border-b">{Tabs.map(x=><button key={x} onClick={()=>setTab(x)} className={`px-3 py-2 text-xs font-bold ${tab===x?'border-b-2 border-blue-600 text-blue-700':'text-slate-500'}`}>{x.replaceAll('_',' ')}</button>)}</div>
    {(data?.items||[]).map(row=><article key={row.id} className="rounded-xl border bg-white p-4"><div className="flex justify-between gap-3"><div><p className="font-mono text-xs text-blue-700">{row.cluster_code}</p><h3 className="font-semibold">{row.proposed_canonical_description||'Canonical description needs review'}</h3><p className="mt-1 text-xs text-slate-500">{row.identity_members.length} identity · {row.functional_alternatives.length} functional alternatives · Risk: <b>{row.risk_level}</b></p></div><Button size="sm" onClick={()=>open(row)} loading={busy}>Review Cluster</Button></div></article>)}
    {data?.total===0&&<p className="rounded border bg-white p-8 text-center text-sm text-slate-500">No clusters in this queue.</p>}
    <Modal open={!!review} onClose={()=>!busy&&setReview(null)} title={`Review ${review?.cluster_code||''}`} subtitle="Edits are persisted; removal never deletes Material Master records." maxWidth="max-w-4xl" actions={<><Button size="sm" variant="ghost" onClick={()=>setReview(null)}>Close</Button>{review?.status!=='APPROVED'&&<Button size="sm" variant="success" loading={busy} onClick={submitForApproval}>Submit for Approval</Button>}</>}>
      {review&&<div className="space-y-4 text-xs">{[['Identity members',review.identity_members],['Functional alternatives',review.functional_alternatives],['Removed members',review.removed_members]].map(([title,items])=><section key={title}><h3 className="mb-2 font-bold">{title}</h3>{items.length?items.map(m=><div className="mb-2 flex items-center justify-between rounded border p-2" key={m.material_id}><span><b>{m.cpse} · {m.material_code}</b><br/>{m.description}<br/><span className="text-slate-500">{m.relationship_type} · {m.confidence?.toFixed?.(2)||'-'}</span></span>{title==='Identity members'&&<span className="flex gap-2"><Button size="sm" variant="secondary" disabled={busy} onClick={()=>act(()=>matchingApi.classifyClusterMember(review.id,m.material_id,{member_type:'FUNCTIONAL_ALTERNATIVE'}))}>Move to Functional</Button><Button size="sm" variant="danger" disabled={busy} onClick={()=>act(()=>matchingApi.removeClusterMember(review.id,m.material_id))}>Remove</Button></span>}{title==='Functional alternatives'&&<Button size="sm" variant="danger" disabled={busy} onClick={()=>act(()=>matchingApi.removeClusterMember(review.id,m.material_id))}>Remove</Button>}{title==='Removed members'&&<Button size="sm" disabled={busy} onClick={()=>act(()=>matchingApi.restoreClusterMember(review.id,m.material_id))}>Restore</Button>}</div>):<p className="text-slate-500">None</p>}</section>)}</div>}
    </Modal></div>;
};
