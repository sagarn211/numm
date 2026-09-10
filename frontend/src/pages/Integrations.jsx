import { useCallback, useEffect, useState } from 'react';
import { PlugZap, RefreshCw, UploadCloud } from 'lucide-react';
import { integrationApi } from '../services/integrationApi';
import { cpseApi } from '../services/cpseApi';
import { Button } from '../components/common/Button';

export const Integrations = () => {
  const [cpses, setCpses] = useState([]);
  const [cpse, setCpse] = useState('');
  const [connector, setConnector] = useState('MOCK');
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    try {
      const [cpseResponse, historyResponse] = await Promise.all([cpseApi.getAll(), integrationApi.getSapHistory()]);
      setCpses(cpseResponse.data || []);
      setHistory(historyResponse.data || []);
      setError('');
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  }, []);
  useEffect(() => {
    const timer = window.setTimeout(load, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  const sync = async () => {
    if (!cpse) return;
    setLoading(true);
    setError('');
    try { await integrationApi.syncSap(Number(cpse), connector); await load(); }
    catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message); }
    finally { setLoading(false); }
  };
  const push = async () => {
    if (!cpse) return;
    setLoading(true);
    setError('');
    try { await integrationApi.pushMappings(Number(cpse), connector); await load(); }
    catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message); }
    finally { setLoading(false); }
  };
  return <div className="space-y-6">
    <div><h2 className="text-xl font-bold">ERP / SAP Integrations</h2><p className="text-xs text-slate-500">MOCK is simulated; ODATA uses the configured live SAP endpoint.</p></div>
    {error && <div className="p-3 bg-amber-50 text-amber-800 rounded-lg text-xs">{error}</div>}
    <div className="bg-white border rounded-xl p-5 flex flex-wrap gap-3">
      <PlugZap className="w-7 h-7 text-blue-600" />
      <select value={cpse} onChange={event => setCpse(event.target.value)} className="border rounded-lg px-3 py-2 text-xs flex-1"><option value="">Select CPSE</option>{cpses.map(item => <option key={item.id} value={item.id}>{item.code} — {item.name}</option>)}</select>
      <select value={connector} onChange={event => setConnector(event.target.value)} className="border rounded-lg px-3 py-2 text-xs"><option value="MOCK">Mock SAP (simulated)</option><option value="ODATA">SAP OData (live)</option></select>
      <Button icon={RefreshCw} loading={loading} onClick={sync}>Pull materials</Button>
      <Button icon={UploadCloud} loading={loading} onClick={push} disabled={connector === 'MOCK'}>Push mappings</Button>
    </div>
    <div className="bg-white border rounded-xl p-4 space-y-2">{history.map(item => <div key={item.id} className="grid grid-cols-6 gap-2 text-xs border-b py-2"><span>#{item.id}</span><span>{cpses.find(cpseItem => cpseItem.id === item.cpse_id)?.code || item.cpse_id}</span><span>{item.connector || 'MOCK'}</span><span className="font-bold">{item.status}</span><span>Created {item.records_created}</span><span>Failed {item.records_failed}</span></div>)}</div>
  </div>;
};
