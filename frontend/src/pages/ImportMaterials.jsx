import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle2, ArrowRight, History, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { importApi } from '../services/importApi';
import { FileUploader } from '../components/import/FileUploader';
import { ImportPreview } from '../components/import/ImportPreview';
import { ImportStatus } from '../components/import/ImportStatus';
import { Button } from '../components/common/Button';

export const ImportMaterials = () => {
  const navigate = useNavigate();
  const [cpse, setCpse] = useState('NTPC');
  const [sector, setSector] = useState('Power');
  const [step, setStep] = useState('IDLE'); // IDLE | PREVIEW | PIPELINE | DONE
  
  const [file, setFile] = useState(null);
  const [validationData, setValidationData] = useState(null);
  const [progressData, setProgressData] = useState(null);
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const res = await importApi.getImportBatches();
        setBatches(res.data || []);
      } catch (err) {
        console.error('Failed to load import batches', err);
      }
    };
    fetchBatches();
  }, []);

  const handleFileSelected = async (selectedFile) => {
    setFile(selectedFile);
    const res = await importApi.validateFile();
    setValidationData(res.data);
    setStep('PREVIEW');
  };

  const handleStartPipeline = async () => {
    const res = await importApi.startImport({ cpse, sector, filename: file?.name });
    const progressRes = await importApi.getImportProgress(res.data.jobId);
    setProgressData(progressRes.data);
    setStep('PIPELINE');
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Import CPSE Material Master Data</h2>
        <p className="text-xs text-slate-500 mt-0.5">Upload CPSE dataset files (.CSV, .XLSX) for automated schema validation, normalization, and AI matching</p>
      </div>

      {/* Step Indicator */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between text-xs font-semibold text-slate-500">
        <div className={`flex items-center gap-2 ${step === 'IDLE' ? 'text-blue-600 font-bold' : 'text-slate-400'}`}>
          <span className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-mono font-bold">1</span>
          <span>Select File & CPSE</span>
        </div>
        <div className="h-[1px] w-12 bg-slate-200"></div>
        <div className={`flex items-center gap-2 ${step === 'PREVIEW' ? 'text-blue-600 font-bold' : 'text-slate-400'}`}>
          <span className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-mono font-bold">2</span>
          <span>Validation Audit</span>
        </div>
        <div className="h-[1px] w-12 bg-slate-200"></div>
        <div className={`flex items-center gap-2 ${step === 'PIPELINE' ? 'text-blue-600 font-bold' : 'text-slate-400'}`}>
          <span className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-mono font-bold">3</span>
          <span>Data Pipeline</span>
        </div>
      </div>

      {/* Step 1: File Dropzone & Dropdown Controls */}
      {step === 'IDLE' && (
        <div className="space-y-6">
          <FileUploader
            onFileSelected={handleFileSelected}
            cpse={cpse}
            setCpse={setCpse}
            sector={sector}
            setSector={setSector}
          />

          {/* Recent Import Batches History */}
          <div className="bg-white border border-slate-200/80 rounded-xl p-5 shadow-2xs">
            <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
              <History className="w-4 h-4 text-blue-600" />
              Recent Import Batches
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 font-bold uppercase text-[10px]">
                    <th className="py-2.5 px-3">Batch ID</th>
                    <th className="py-2.5 px-3">Filename</th>
                    <th className="py-2.5 px-3">CPSE</th>
                    <th className="py-2.5 px-3">Total Rows</th>
                    <th className="py-2.5 px-3">Success</th>
                    <th className="py-2.5 px-3">Errors</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Imported At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {batches.map((batch) => (
                    <tr key={batch.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-slate-700 font-bold">{batch.id}</td>
                      <td className="py-2.5 px-3 font-medium text-slate-900 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-slate-400" />
                        {batch.filename}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-blue-600">{batch.cpse}</td>
                      <td className="py-2.5 px-3 font-mono">{batch.totalRecords?.toLocaleString() || batch.total_rows}</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-600 font-bold">{batch.successCount?.toLocaleString() || batch.successful_rows}</td>
                      <td className="py-2.5 px-3 font-mono text-rose-600 font-bold">{batch.errorCount?.toLocaleString() || batch.failed_rows}</td>
                      <td className="py-2.5 px-3">
                        <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[10px] font-bold">
                          <CheckCircle className="w-3 h-3 text-emerald-600" />
                          {batch.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">{batch.importedAt || '2026-08-27'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Import Validation Preview */}
      {step === 'PREVIEW' && (
        <ImportPreview
          validationData={validationData}
          onConfirmImport={handleStartPipeline}
        />
      )}

      {/* Step 3: Animated Live Data Pipeline Status */}
      {step === 'PIPELINE' && (
        <ImportStatus
          progressData={progressData}
          onComplete={() => navigate('/ai-recommendations')}
        />
      )}

    </div>
  );
};
