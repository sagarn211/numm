import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Button } from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';
import { hasPermission } from '../utils/permissions';

export const ProcurementHistory = () => {
  const { user } = useAuth();
  const [cpses, setCpses] = useState([]);
  const [cpse, setCpse] = useState('');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    Promise.all([api.get('/api/cpses'), api.get('/api/procurement/analytics')]).then(([companies, analytics]) => {
      if (active) { setCpses(companies.data); setRows(analytics.data); }
    }).catch(() => { if (active) setError('Unable to load procurement history.'); });
    return () => { active = false; };
  }, []);
  const upload = async confirm => {
    setBusy(true); setError('');
    try {
      const form = new FormData();
      form.append('file', file); form.append('cpse_id', cpse); form.append('confirm', String(confirm));
      const response = await api.post('/api/procurement/import', form);
      setPreview(response.data);
      if (confirm) setRows((await api.get('/api/procurement/analytics')).data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : detail?.message || 'Import failed.');
    } finally { setBusy(false); }
  };
  return <div className="space-y-5">
    <h2 className="text-xl font-bold">Procurement history and collaboration</h2>
    <p className="text-sm">Purchase quantities and spend are grouped by national identity, month, unit, and currency.</p>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {hasPermission(user, 'import.manage') && <section className="space-y-3 rounded border bg-white p-4">
      <p className="text-xs">CSV columns: material_code, order_number, line_number, supplier, period (YYYY-MM), quantity, uom, unit_price, currency. Optional: lead_time_days.</p>
      <select aria-label="CPSE" value={cpse} disabled={busy} onChange={e => { setCpse(e.target.value); setPreview(null); }}><option value="">Select CPSE</option>{cpses.map(c => <option key={c.id} value={c.id}>{c.code}</option>)}</select>
      <input aria-label="Purchase history CSV" type="file" accept=".csv" disabled={busy} onChange={e => { setFile(e.target.files[0]); setPreview(null); }} />
      <Button loading={busy} disabled={!file || !cpse} onClick={() => upload(false)}>Preview purchase history</Button>
      {preview && <div><p>{preview.confirmed ? 'Imported' : 'Valid rows'}: {preview.valid_rows}</p>{preview.errors.map((item, i) => <p key={i} className="text-xs text-red-700">Row {item.row}: {item.message}</p>)}
        {!preview.confirmed && <><pre className="overflow-auto text-xs">{JSON.stringify(preview.preview, null, 2)}</pre><Button loading={busy} disabled={preview.errors.length > 0 || !preview.valid_rows} onClick={() => upload(true)}>Confirm import</Button></>}
      </div>}
    </section>}
    <div className="overflow-auto rounded border bg-white"><table className="w-full text-left text-xs"><thead><tr>{['Identity', 'Month', 'Quantity / unit', 'Spend', 'Suppliers', 'CPSEs', 'Mean lead time'].map(t => <th key={t} className="p-3">{t}</th>)}</tr></thead><tbody>{rows.map((r, i) => <tr key={i} className="border-t"><td className="p-3">{r.national_material_id ? `National #${r.national_material_id}` : `Unmapped material #${r.material_id}`}</td><td>{r.period}</td><td>{r.quantity} {r.uom}</td><td>{r.spend} {r.currency}</td><td>{r.suppliers.join(', ')}</td><td>{r.participating_cpses.length}</td><td>{r.average_lead_time_days ?? 'Unknown'}</td></tr>)}</tbody></table>{!rows.length && <p className="p-4">Import purchase history to see spend and demand patterns.</p>}</div>
  </div>;
};
