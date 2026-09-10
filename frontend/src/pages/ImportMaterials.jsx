import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, FileText, History } from 'lucide-react';
import { importApi } from '../services/importApi';
import { cpseApi } from '../services/cpseApi';
import { FileUploader } from '../components/import/FileUploader';
import { ImportPreview } from '../components/import/ImportPreview';
import { ImportStatus } from '../components/import/ImportStatus';

const TERMINAL = ['COMPLETED', 'COMPLETED_WITH_ERRORS', 'COMPLETED_WITH_AI_ERROR', 'FAILED', 'CANCELLED'];

export const ImportMaterials = () => {
  const navigate = useNavigate();
  const [cpse, setCpse] = useState('NTPC');
  const [sector, setSector] = useState('Power');
  const [cpses, setCpses] = useState([]);
  const [importType, setImportType] = useState('MATERIAL');
  const [conflictPolicy, setConflictPolicy] = useState('REJECT');
  const [step, setStep] = useState('IDLE');
  const [validationData, setValidationData] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [batches, setBatches] = useState([]);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [cpseResponse, batchResponse] = await Promise.all([cpseApi.getAll(), importApi.getImportBatches()]);
      setCpses(cpseResponse.data || []); setBatches(batchResponse.data || []);
      if (cpseResponse.data?.length && !cpseResponse.data.some(item => item.code === cpse)) {
        setCpse(cpseResponse.data[0].code); setSector(cpseResponse.data[0].sector);
      }
    } catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message); }
  }, [cpse]);

  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer); }, [load]);
  useEffect(() => {
    if (!jobId) return undefined;
    let stopped = false;
    const poll = async () => {
      try {
        const response = await importApi.getImportProgress(jobId);
        if (stopped) return;
        setProgressData(response.data);
        if (TERMINAL.includes(response.data.status)) { stopped = true; load(); }
      } catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message); stopped = true; }
    };
    poll(); const timer = window.setInterval(() => { if (!stopped) poll(); }, 1000);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [jobId, load]);

  const selected = cpses.find(item => item.code === cpse);
  const choose = async file => {
    if (!file) return;
    if (!selected) { setError('Create/select a CPSE first.'); return; }
    try {
      const response = await importApi.previewFile(file, selected.id, { importType, conflictPolicy });
      setValidationData(response.data); setStep('PREVIEW'); setError('');
    } catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message); }
  };
  const confirm = async () => {
    if (!validationData?.batchId) { setError('Import preview is missing its batch identifier. Please preview the file again.'); return; }
    try {
      const response = await importApi.startImport({ batchId: validationData.batchId });
      setJobId(response.data.jobId);
      setProgressData({ progress: 0, processedRows: 0, totalRows: response.data.totalRows, stage: 'QUEUED', stageMessage: 'Import queued…', status: response.data.status });
      setStep('PIPELINE');
    } catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message); }
  };
  const retryAi = async batch => {
    try {
      const response = await importApi.retryAi(batch.id); setJobId(response.data.jobId);
      setProgressData({ progress: 100, processedRows: batch.totalRecords, totalRows: batch.totalRecords, stage: 'AI_QUEUED', stageMessage: 'AI matching retry queued…', status: response.data.status });
      setStep('PIPELINE'); setError('');
    } catch (requestError) { setError(requestError?.response?.data?.detail || requestError.message || 'Unable to retry AI matching.'); }
  };
  const changeImportType = value => { setImportType(value); setValidationData(null); setProgressData(null); setJobId(null); setError(''); };

  return <div className="space-y-6">
    <button type="button" className="text-sm font-semibold text-blue-700" onClick={() => navigate('/procurement-history')}>Import procurement history and view spend analytics</button>
    <div><h2 className="text-xl font-bold">Import CPSE Data</h2><p className="text-xs text-slate-500">Import material-master records or physical warehouse stock through a validated CSV/XLSX pipeline.</p></div>
    {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700"><AlertCircle className="mr-2 inline h-4 w-4" />{error}</div>}
    {step === 'IDLE' && <>
      <div className="rounded-xl border bg-white p-4 shadow-2xs"><div className="grid gap-4 sm:grid-cols-2"><div><label className="mb-1.5 block text-xs font-bold text-slate-700">Import type</label><select value={importType} onChange={event => changeImportType(event.target.value)} className="w-full rounded-lg border bg-slate-50 px-3 py-2 text-xs font-bold"><option value="MATERIAL">Material Master</option><option value="INVENTORY">Inventory Stock</option></select></div>{importType === 'INVENTORY' && <div><label className="mb-1.5 block text-xs font-bold text-slate-700">When stock already exists</label><select value={conflictPolicy} onChange={event => setConflictPolicy(event.target.value)} className="w-full rounded-lg border bg-slate-50 px-3 py-2 text-xs font-bold"><option value="REJECT">Reject existing rows (safer)</option><option value="UPDATE">Update existing stock</option></select></div>}</div></div>
      <FileUploader key={importType} importType={importType} onFileSelected={choose} cpse={cpse} setCpse={code => { setCpse(code); const item = cpses.find(value => value.code === code); if (item) setSector(item.sector); }} sector={sector} setSector={setSector} cpses={cpses} />
      <div className="rounded-xl border bg-white p-5"><h3 className="mb-3 text-sm font-bold"><History className="mr-2 inline h-4 w-4 text-blue-600" />Recent Import Batches</h3>{batches.map(batch => <div key={batch.id} className="grid grid-cols-7 items-center gap-2 border-t py-2 text-xs"><span className="font-mono">#{batch.id}</span><span className="col-span-2"><FileText className="mr-1 inline h-3 w-3" />{batch.filename}</span><span className={`w-fit rounded-full px-2 py-0.5 text-[10px] font-bold ${batch.importType === 'INVENTORY' ? 'bg-violet-50 text-violet-700' : 'bg-blue-50 text-blue-700'}`}>{batch.importType}</span><span>{batch.successCount}/{batch.totalRecords}</span><span className="font-bold">{batch.status}</span><span>{batch.status === 'COMPLETED_WITH_AI_ERROR' && batch.importType === 'MATERIAL' && <button type="button" className="font-bold text-blue-700 hover:underline" onClick={() => retryAi(batch)}>Retry AI</button>}</span></div>)}</div>
    </>}
    {step === 'PREVIEW' && <ImportPreview validationData={validationData} onConfirmImport={confirm} onCancel={() => { setStep('IDLE'); setValidationData(null); setError(''); }} />}
    {step === 'PIPELINE' && <ImportStatus progressData={progressData} importType={validationData?.importType || importType} onComplete={() => navigate((validationData?.importType || importType) === 'INVENTORY' ? '/inventory' : '/ai-recommendations')} />}
  </div>;
};
