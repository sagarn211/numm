import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckSquare } from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';

const tabs=[['IDENTITY','Identity Approvals'],['FUNCTIONAL','Functional Substitutions'],['CONFLICTS','Mapping Conflicts'],['HISTORY','History']];
const description=m=>`${m?.cpse||'CPSE'} · ${m?.material_code||'Unknown material'} — ${m?.description||''}`;

export const Approvals=()=>{
  const navigate=useNavigate();
  const [tab,setTab]=useState('IDENTITY'),[data,setData]=useState(null),[selected,setSelected]=useState(new Set()),[result,setResult]=useState(null),[error,setError]=useState(''),[page,setPage]=useState(1),[busy,setBusy]=useState(false);
  const load=useCallback(async()=>{if(tab==='HISTORY'){setData({items:[]});return;}try{setError('');setData((await api.get({IDENTITY:'/api/clusters/queues/identity',FUNCTIONAL:'/api/clusters/queues/functional',CONFLICTS:'/api/clusters/queues/conflicts'}[tab],{params:{page,limit:25}})).data)}catch(e){setError(e?.response?.data?.detail||e.message)}},[page,tab]);
  useEffect(()=>{setData(null);setSelected(new Set());load()},[load]);
  const batchApprove=async()=>{setBusy(true);try{const r=await api.post('/api/clusters/batch-approve',{cluster_ids:[...selected]});setResult(r.data);await load()}catch(e){setError(e?.response?.data?.detail||e.message)}finally{setBusy(false)}};
  const approveCluster=async id=>{setBusy(true);try{await api.post(`/api/clusters/${id}/approve`);await load()}catch(e){setError(e?.response?.data?.detail||e.message)}finally{setBusy(false)}};
  const decideFunctional=async(matchId,approve)=>{
    const comment=window.prompt(approve?'State the approved application and substitution limitations:':'State the rejection reason:');
    if(!comment?.trim())return;
    setBusy(true);try{await api.post(`/api/approvals/${matchId}/${approve?'approve':'reject'}`,approve?{comment,acknowledge_functional_equivalent:true}:{comment});await load()}catch(e){setError(e?.response?.data?.detail||e.message)}finally{setBusy(false)}
  };
  if(!data&&!error)return <Loading type="skeleton" rows={5}/>;
  const items=data?.items||[];
  return <div className="space-y-5"><div className="flex items-center gap-2"><CheckSquare className="h-5 w-5 text-blue-700"/><div><h2 className="text-xl font-bold">Approval Center</h2><p className="text-xs text-slate-500">Authorize reviewed identity clusters and record governed substitute decisions.</p></div></div>
    {error&&<div className="rounded border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{typeof error==='string'?error:JSON.stringify(error)}</div>}
    <div className="flex gap-2 border-b">{tabs.map(([key,label])=><button key={key} onClick={()=>{setPage(1);setTab(key)}} className={`px-3 py-2 text-xs font-bold ${tab===key?'border-b-2 border-blue-600 text-blue-700':'text-slate-500'}`}>{label}</button>)}</div>
    {tab==='IDENTITY'&&<div className="flex justify-end"><Button size="sm" disabled={!selected.size||busy} onClick={batchApprove}>Approve Selected Low-Risk Clusters</Button></div>}
    {tab==='IDENTITY'&&items.map(x=><article className="rounded-xl border bg-white p-4" key={x.id}><div className="flex items-start justify-between gap-3"><label className="flex gap-3"><input className="mt-1" type="checkbox" disabled={x.risk_level!=='LOW'||busy} checked={selected.has(x.id)} onChange={e=>setSelected(s=>{const n=new Set(s);e.target.checked?n.add(x.id):n.delete(x.id);return n})}/><span><b>{x.cluster_code}</b><br/>{x.proposed_canonical_description}<br/><small>{x.identity_members.length} identity members · <b>{x.risk_level}</b> risk · {x.functional_alternatives.length} functional alternatives, never mapped</small></span></label><span className="flex shrink-0 gap-2"><Button size="sm" variant="secondary" onClick={()=>navigate(`/duplicate-clusters?cluster=${x.id}`)}>View Review</Button><Button size="sm" variant="success" disabled={busy} onClick={()=>approveCluster(x.id)}>Approve National Identity</Button></span></div></article>)}
    {tab==='FUNCTIONAL'&&items.map(x=><article className="rounded-xl border bg-white p-4 text-xs" key={x.match_id}><p className="font-mono font-bold text-blue-700">Functional substitution evidence #{x.match_id} · {(Number(x.confidence||0)*100).toFixed(1)}%</p><div className="mt-2 grid gap-2 md:grid-cols-2"><div className="rounded border bg-slate-50 p-2">{description(x.material_a)}</div><div className="rounded border bg-slate-50 p-2">{description(x.material_b)}</div></div><p className="mt-2 text-slate-600">{x.explanation||'Engineering review is required; identities and stock remain separate.'}</p><div className="mt-3 flex justify-end gap-2"><Button size="sm" variant="danger" disabled={busy} onClick={()=>decideFunctional(x.match_id,false)}>Reject Relationship</Button><Button size="sm" variant="success" disabled={busy} onClick={()=>decideFunctional(x.match_id,true)}>Approve Conditional Substitute</Button></div></article>)}
    {tab==='CONFLICTS'&&items.map(x=><article className="rounded-xl border border-amber-300 bg-white p-4 text-xs" key={x.id}><p className="font-mono font-bold text-amber-800">{x.cluster_code} · Mapping conflict</p><p className="mt-1 font-medium">{x.proposed_canonical_description}</p><p className="mt-2 text-slate-600">Active identity members already map to different National Materials. Normal approval cannot reassign them.</p><div className="mt-2 space-y-1">{x.identity_members.map(m=><p key={m.material_id}>{m.material_code} · {m.cpse} · current NMC: {m.mapped_national_material_id||'unmapped'}</p>)}</div><div className="mt-3 flex justify-end"><Button size="sm" variant="secondary" onClick={()=>navigate(`/duplicate-clusters?cluster=${x.id}`)}>View Cluster Review</Button></div></article>)}
    {tab==='HISTORY'&&<p className="rounded border bg-white p-8 text-center text-sm text-slate-500">Cluster approval history is retained in the Audit Trail and National Material 360 views.</p>}
    {tab!=='HISTORY'&&!items.length&&<p className="rounded border bg-white p-8 text-center text-sm text-slate-500">No actionable items in this queue.</p>}
    {data?.pages>1&&<div className="flex items-center justify-between text-xs"><Button size="sm" variant="secondary" disabled={page<=1||busy} onClick={()=>setPage(x=>x-1)}>Previous</Button><span>Page {data.page} of {data.pages} · {data.total} items</span><Button size="sm" variant="secondary" disabled={page>=data.pages||busy} onClick={()=>setPage(x=>x+1)}>Next</Button></div>}
    {result&&<div className="rounded border border-emerald-200 bg-emerald-50 p-3 text-xs">Submitted: {result.submitted} · Approved: {result.approved} · Already resolved: {result.already_resolved} · Moved to conflict: {result.moved_to_conflict} · Failed: {result.failed}</div>}
  </div>;
};
