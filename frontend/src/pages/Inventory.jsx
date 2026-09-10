import { useEffect, useMemo, useRef, useState } from 'react';
import { Boxes, Edit3, PackagePlus, RefreshCw, Search, Warehouse } from 'lucide-react';
import { inventoryApi } from '../services/inventoryApi';
import { materialApi } from '../services/materialApi';
import { cpseApi } from '../services/cpseApi';
import { Button } from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';
import { hasPermission } from '../utils/permissions';

const blankForm = (cpseId = '') => ({ cpse_id: cpseId, material_id: '', warehouse: '', available_quantity: '', reserved_quantity: '0', uom: 'EA', unit_cost: '' });
const number = value => Number(value || 0);

export const Inventory = () => {
  const { user } = useAuth();
  const canWrite = hasPermission(user, 'inventory.write');
  const canChooseCpse = hasPermission(user, '*');
  const [rows, setRows] = useState([]); const [materials, setMaterials] = useState([]); const [cpses, setCpses] = useState([]);
  const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState(null); const [query, setQuery] = useState(''); const [filterCpse, setFilterCpse] = useState('');
  const [form, setForm] = useState(blankForm(user?.cpse_id || ''));
  const formRef = useRef(null);
  const warehouseRef = useRef(null);
  const load = async () => { setLoading(true); try { const [inventoryResponse, materialResponse, cpseResponse] = await Promise.all([inventoryApi.getAll(), materialApi.getMaterials(), cpseApi.getAll()]); setRows(inventoryResponse.data || []); setMaterials(materialResponse.data || []); setCpses(cpseResponse.data || []); setError(''); } catch (e) { setError(e?.response?.data?.detail || e.message || 'Unable to load inventory.'); } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);
  const materialById = useMemo(() => Object.fromEntries(materials.map(x => [x.id, x])), [materials]);
  const cpseById = useMemo(() => Object.fromEntries(cpses.map(x => [x.id, x])), [cpses]);
  const availableMaterials = materials.filter(x => !form.cpse_id || x.cpseId === Number(form.cpse_id));
  const stockedMaterialIds = useMemo(() => new Set(rows.map(row => row.material_id)), [rows]);
  const displayRows = useMemo(() => [
    ...rows,
    ...materials.filter(material => !stockedMaterialIds.has(material.id)).map(material => ({
      id: `not-stocked-${material.id}`,
      material_id: material.id,
      cpse_id: material.cpseId,
      warehouse: '',
      available_quantity: 0,
      reserved_quantity: 0,
      uom: material.uom,
      not_stocked: true,
    })),
  ], [rows, materials, stockedMaterialIds]);
  const filteredRows = displayRows.filter(row => { const material = materialById[row.material_id]; const cpse = cpseById[row.cpse_id]; const text = `${cpse?.code || ''} ${material?.code || ''} ${material?.nationalCode || ''} ${material?.description || ''} ${row.warehouse || ''}`.toLowerCase(); return (!filterCpse || String(row.cpse_id) === filterCpse) && (!query.trim() || text.includes(query.trim().toLowerCase())); });
  const totals = filteredRows.filter(row => !row.not_stocked).reduce((sum, row) => ({ available: sum.available + number(row.available_quantity), reserved: sum.reserved + number(row.reserved_quantity) }), { available: 0, reserved: 0 });
  const resetForm = () => { setEditingId(null); setForm(blankForm(user?.cpse_id || '')); };
  const save = async event => { event.preventDefault(); const available = number(form.available_quantity), reserved = number(form.reserved_quantity); if (!form.cpse_id || !form.material_id || !form.warehouse.trim() || !form.uom.trim()) return setError('Select CPSE and material, then enter warehouse and unit of measure.'); if (available < 0 || reserved < 0 || reserved > available) return setError('Available stock must be non-negative and cannot be lower than reserved stock.'); setSaving(true); setError(''); try { const payload = { ...form, cpse_id: Number(form.cpse_id), material_id: Number(form.material_id), warehouse: form.warehouse.trim(), available_quantity: available, reserved_quantity: reserved, uom: form.uom.trim().toUpperCase(), unit_cost: form.unit_cost === '' ? null : number(form.unit_cost) }; if (editingId) await inventoryApi.update(editingId, payload); else await inventoryApi.create(payload); resetForm(); await load(); } catch (e) { setError(e?.response?.data?.detail || e.message || 'Unable to save stock.'); } finally { setSaving(false); } };
  const edit = row => { setEditingId(row.id); setForm({ cpse_id: String(row.cpse_id), material_id: String(row.material_id), warehouse: row.warehouse, available_quantity: String(row.available_quantity), reserved_quantity: String(row.reserved_quantity), uom: row.uom, unit_cost: row.unit_cost == null ? '' : String(row.unit_cost) }); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const startStock = row => {
    setEditingId(null);
    setError('');
    setForm({
      ...blankForm(String(row.cpse_id)),
      material_id: String(row.material_id),
      uom: row.uom || materialById[row.material_id]?.uom || 'EA',
    });
    window.requestAnimationFrame(() => {
      formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      window.setTimeout(() => warehouseRef.current?.focus(), 350);
    });
  };
  return <div className="space-y-6">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-xl font-bold">Cross-CPSE Inventory</h2><p className="text-xs text-slate-500">Track usable stock, reservations, and reusable material availability before procurement.</p></div><Button variant="secondary" size="sm" icon={RefreshCw} onClick={load} loading={loading}>Refresh</Button></div>
    {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{error}</div>}
    <div className="grid gap-3 sm:grid-cols-3"><div className="rounded-xl border bg-white p-4"><p className="text-[11px] font-bold uppercase text-slate-500">CPSE products</p><p className="mt-1 text-2xl font-bold">{filteredRows.length}</p></div><div className="rounded-xl border bg-white p-4"><p className="text-[11px] font-bold uppercase text-slate-500">Available stock</p><p className="mt-1 text-2xl font-bold text-blue-700">{totals.available.toLocaleString()}</p></div><div className="rounded-xl border bg-emerald-50 p-4"><p className="text-[11px] font-bold uppercase text-emerald-700">Effective available</p><p className="mt-1 text-2xl font-bold text-emerald-700">{Math.max(totals.available - totals.reserved, 0).toLocaleString()}</p><p className="text-[11px] text-emerald-700">{totals.reserved.toLocaleString()} reserved</p></div></div>
    {canWrite && <form ref={formRef} onSubmit={save} className={`rounded-xl border bg-white p-4 shadow-2xs transition-all ${form.material_id && !editingId ? 'border-blue-400 ring-2 ring-blue-100' : ''}`}><div className="mb-3 flex items-center justify-between"><div><h3 className="text-sm font-bold">{editingId ? 'Update stock record' : 'Add stock record'}</h3><p className="text-xs text-slate-500">Reservations cannot exceed available stock.</p>{form.material_id && !editingId && <p className="mt-1 text-xs font-bold text-blue-700">Adding stock for {materialById[form.material_id]?.code || `Material #${form.material_id}`}</p>}</div>{editingId && <Button type="button" size="sm" variant="secondary" onClick={resetForm}>Cancel edit</Button>}</div><div className="grid gap-3 md:grid-cols-6"><select required value={form.cpse_id} disabled={editingId || !canChooseCpse} onChange={e => setForm({ ...form, cpse_id: e.target.value, material_id: '' })} className="rounded-lg border px-3 py-2 text-xs disabled:bg-slate-100"><option value="">CPSE</option>{cpses.map(x => <option key={x.id} value={x.id}>{x.code}</option>)}</select><select required value={form.material_id} disabled={editingId} onChange={e => { const material = materialById[e.target.value]; setForm({ ...form, material_id: e.target.value, uom: material?.uom || form.uom }); }} className="rounded-lg border px-3 py-2 text-xs md:col-span-2 disabled:bg-slate-100"><option value="">Material</option>{availableMaterials.map(x => <option key={x.id} value={x.id}>{x.code} — {x.description}</option>)}</select><input ref={warehouseRef} required placeholder="Warehouse / depot" value={form.warehouse} onChange={e => setForm({ ...form, warehouse: e.target.value })} className="rounded-lg border px-3 py-2 text-xs" /><input required min="0" step="any" type="number" placeholder="Available" value={form.available_quantity} onChange={e => setForm({ ...form, available_quantity: e.target.value })} className="rounded-lg border px-3 py-2 text-xs" /><div className="flex gap-2"><input required min="0" step="any" type="number" placeholder="Reserved" value={form.reserved_quantity} onChange={e => setForm({ ...form, reserved_quantity: e.target.value })} className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-xs" /><input required placeholder="UOM" value={form.uom} onChange={e => setForm({ ...form, uom: e.target.value })} className="w-16 rounded-lg border px-2 py-2 text-xs" /></div></div><div className="mt-3 flex justify-end"><Button type="submit" icon={editingId ? Edit3 : PackagePlus} loading={saving}>{editingId ? 'Save changes' : 'Add stock'}</Button></div></form>}
    <section className="overflow-hidden rounded-xl border bg-white">
      <div className="flex flex-col gap-3 border-b bg-slate-50 p-4 sm:flex-row">
        <div className="relative flex-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search material, CPSE, or warehouse" className="w-full rounded-lg border bg-white py-2 pl-9 pr-3 text-xs" /></div>
        <select value={filterCpse} onChange={e => setFilterCpse(e.target.value)} className="rounded-lg border bg-white px-3 py-2 text-xs"><option value="">All CPSEs</option>{cpses.map(x => <option key={x.id} value={x.id}>{x.code}</option>)}</select>
      </div>
      <div className="grid gap-4 p-4 lg:grid-cols-2">
        {filteredRows.map(row => {
          const material = materialById[row.material_id];
          const cpse = cpseById[row.cpse_id];
          const effective = Math.max(number(row.available_quantity) - number(row.reserved_quantity), 0);
          return <article key={row.id} className={`rounded-xl border bg-white p-4 shadow-sm ${row.not_stocked ? 'border-dashed' : ''}`}>
            <div className="flex items-start justify-between gap-3"><div><span className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-bold text-blue-700">{cpse?.code || `CPSE #${row.cpse_id}`}</span>{row.not_stocked && <span className="ml-2 rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">Not stocked</span>}<div className="mt-3 font-mono text-sm font-bold text-slate-900">{material?.code || `Material #${row.material_id}`}</div>{material?.nationalCode && <div className="mt-1 font-mono text-[11px] font-semibold text-violet-700">National Code: {material.nationalCode}</div>}</div>{canWrite && (row.not_stocked ? <button type="button" onClick={() => startStock(row)} className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900"><PackagePlus className="h-3.5 w-3.5" />Add stock</button> : <button type="button" onClick={() => edit(row)} className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900"><Edit3 className="h-3.5 w-3.5" />Edit</button>)}</div>
            <p className="mt-2 min-h-10 text-sm font-medium text-slate-700">{material?.description || 'Material description is unavailable.'}</p>
            <div className="mt-3 flex items-center gap-1 text-xs text-slate-500"><Warehouse className="h-3.5 w-3.5" />{row.warehouse || 'No warehouse or stock record registered'}</div>
            <dl className="mt-4 grid gap-x-4 gap-y-3 border-y py-3 text-xs sm:grid-cols-2">
              <div><dt className="text-slate-500">Category</dt><dd className="mt-1 font-medium text-slate-800">{material?.category || 'Not specified'}</dd></div>
              <div><dt className="text-slate-500">Unit of measure</dt><dd className="mt-1 font-medium text-slate-800">{row.uom || material?.uom || 'Not specified'}</dd></div>
              <div><dt className="text-slate-500">Manufacturer</dt><dd className="mt-1 font-medium text-slate-800">{material?.manufacturer || 'Not specified'}</dd></div>
              <div><dt className="text-slate-500">Model / part number</dt><dd className="mt-1 font-medium text-slate-800">{material?.model || 'Not specified'}</dd></div>
              <div><dt className="text-slate-500">Record source</dt><dd className="mt-1 font-medium text-slate-800">{material?.source || 'Manual'}</dd></div>
              <div><dt className="text-slate-500">Material status</dt><dd className="mt-1 font-medium text-slate-800">{material?.status || 'ACTIVE'}</dd></div>
            </dl>
            <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs"><div className="font-semibold text-slate-700">Technical specification</div><p className="mt-1 whitespace-pre-wrap text-slate-600">{material?.specification || 'No technical specification was registered for this product.'}</p></div>
            <div className="mt-4 grid grid-cols-3 divide-x rounded-lg border bg-slate-50 text-center text-xs"><div className="p-3"><div className="text-slate-500">Available</div><strong className="mt-1 block text-blue-700">{number(row.available_quantity).toLocaleString()} {row.uom}</strong></div><div className="p-3"><div className="text-slate-500">Reserved</div><strong className="mt-1 block text-amber-700">{number(row.reserved_quantity).toLocaleString()} {row.uom}</strong></div><div className="p-3"><div className="text-slate-500">Ready to use</div><strong className="mt-1 block text-emerald-700">{effective.toLocaleString()} {row.uom}</strong></div></div>
          </article>;
        })}
      </div>
      {!loading && !filteredRows.length && <div className="p-10 text-center text-slate-400"><Boxes className="mx-auto h-8 w-8" /><p className="mt-2 text-sm font-semibold">No inventory records found</p></div>}
    </section>
  </div>;
};
