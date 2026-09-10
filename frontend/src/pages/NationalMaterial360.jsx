import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, GitBranch, History, PackageSearch, ShieldCheck } from 'lucide-react';
import { nationalMaterialApi } from '../services/nationalMaterialApi';
import { Loading } from '../components/common/Loading';

const Section = ({ title, children }) => <section className="rounded-xl border border-slate-200 bg-white p-4"><h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-700">{title}</h3>{children}</section>;
const Empty = ({ children }) => <p className="text-xs text-slate-500">{children}</p>;

export const NationalMaterial360 = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    nationalMaterialApi.getMaterial360(id).then(response => { if (active) setData(response.data); })
      .catch(err => { if (active) setError(err?.response?.data?.detail || err.message || 'Unable to load National Material 360.'); });
    return () => { active = false; };
  }, [id]);
  if (error) return <div className="space-y-4"><Link to="/national-materials" className="text-xs text-blue-700">Back to National Materials</Link><div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div></div>;
  if (!data) return <Loading type="skeleton" rows={7} />;
  const material = data.material;
  return <div className="space-y-5">
    <Link to="/national-materials" className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700"><ArrowLeft className="h-4 w-4" /> National Materials</Link>
    <header className="rounded-2xl bg-slate-900 p-6 text-white"><p className="font-mono text-sm text-cyan-300">{material.national_code}</p><h2 className="mt-1 text-xl font-bold">{material.description}</h2><p className="mt-2 text-xs text-slate-300">{material.category} / {material.subcategory || 'Unspecified'} · {material.unit} · {material.status}</p></header>
    <div className="grid gap-4 md:grid-cols-3">
      <Section title="Technical identity"><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(material.specifications || {}, null, 2)}</pre></Section>
      <Section title="National stock">{data.stock_summary.length ? data.stock_summary.map(row => <div key={row.uom} className="grid grid-cols-3 gap-2 text-center text-xs"><div><strong>{row.available}</strong><br/>Available</div><div><strong>{row.reserved}</strong><br/>Reserved</div><div><strong>{row.ready_to_use}</strong><br/>Ready ({row.uom})</div></div>) : <Empty>No inventory records.</Empty>}</Section>
      <Section title="Procurement recommendation">{data.procurement_opportunity ? <><p className="text-2xl font-bold text-blue-800">{data.procurement_opportunity.opportunity_score}/100</p><p className="mt-2 text-xs">{data.procurement_opportunity.recommendation}</p></> : <Empty>No evidence-backed opportunity for the current period.</Empty>}</Section>
    </div>
    <Section title={`Legacy CPSE mappings (${data.legacy_mappings.length})`}>
      {data.legacy_mappings.length ? <div className="grid gap-2 md:grid-cols-2">{data.legacy_mappings.map(row => <div key={row.id} className="rounded-lg border bg-slate-50 p-3 text-xs"><strong>{row.cpse_code} · {row.material.material_code}</strong><p>{row.material.description}</p><span className="text-slate-500">{row.mapping_type}</span></div>)}</div> : <Empty>No legacy mappings.</Empty>}
    </Section>
    <div className="grid gap-4 lg:grid-cols-2">
      <Section title="Inventory by CPSE / warehouse">{data.inventory.length ? data.inventory.map(row => <p key={row.id} className="border-b py-2 text-xs">{row.cpse_code} · {row.warehouse}: {row.available_quantity} available, {row.reserved_quantity} reserved {row.uom}</p>) : <Empty>No inventory records.</Empty>}</Section>
      <Section title="Open demand">{data.demand.length ? data.demand.map(row => <p key={row.id} className="border-b py-2 text-xs">{row.cpse_code} · {row.period}: {row.required_quantity} {row.uom}</p>) : <Empty>No demand records.</Empty>}</Section>
      <Section title="Supplier and purchase summary">{data.supplier_summary.length ? data.supplier_summary.map((row, index) => <p key={`${row.supplier}-${index}`} className="border-b py-2 text-xs">{row.supplier}: {row.quantity} {row.uom}, {row.spend} {row.currency}, {row.order_count} orders</p>) : <Empty>No procurement history.</Empty>}</Section>
      <Section title="SAP / ERP sync status">{data.sap_sync_status.length ? data.sap_sync_status.map(row => <p key={row.id} className="border-b py-2 text-xs">{row.cpse_code} · {row.connector}: {row.status} ({row.records_created} created, {row.records_updated} updated, {row.records_failed} failed)</p>) : <Empty>No connector sync recorded for mapped CPSEs.</Empty>}</Section>
    </div>
    <div className="grid gap-4 lg:grid-cols-3">
      <Section title="AI matching history"><PackageSearch className="mb-2 h-4 w-4" />{data.ai_matching_history.length ? data.ai_matching_history.slice(0, 20).map(row => <p key={row.id} className="border-b py-2 text-xs">#{row.id} {row.classification} · {(row.final_score * 100).toFixed(1)}% · {row.status}</p>) : <Empty>No linked AI recommendation.</Empty>}</Section>
      <Section title="Approval history"><ShieldCheck className="mb-2 h-4 w-4" />{data.approval_history.length ? data.approval_history.slice(0, 20).map(row => <p key={row.id} className="border-b py-2 text-xs">{row.action} · {row.created_at}<br/>{row.comment}</p>) : <Empty>No linked approval action.</Empty>}</Section>
      <Section title="Lineage"><GitBranch className="mb-2 h-4 w-4" /><p className="text-xs">{data.lineage.legacy_material_ids.length} legacy records → {data.lineage.ai_match_ids.length} AI decisions → {data.lineage.mapping_ids.length} active mappings → National #{data.lineage.national_material_id}</p><pre className="mt-2 overflow-auto text-[10px]">{JSON.stringify(data.lineage.provenance, null, 2)}</pre></Section>
    </div>
    <Section title="Governance audit"><History className="mb-2 h-4 w-4" />{data.audit_history.length ? data.audit_history.slice(0, 50).map(row => <p key={row.id} className="border-b py-2 text-xs">#{row.id} {row.action} · {row.created_at}</p>) : <Empty>No linked audit events.</Empty>}</Section>
  </div>;
};
