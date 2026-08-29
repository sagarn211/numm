import React, { useState } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../common/Button';

export const FileUploader = ({ onFileSelected, cpse, setCpse, sector, setSector }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      onFileSelected(file);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      onFileSelected(file);
    }
  };

  return (
    <div className="space-y-4">
      {/* CPSE & Sector Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">Select Source CPSE Enterprise</label>
          <select
            value={cpse}
            onChange={(e) => setCpse(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="NTPC">NTPC Limited (Power)</option>
            <option value="ONGC">ONGC Corporation (Oil & Gas)</option>
            <option value="SAIL">SAIL Authority of India (Steel)</option>
            <option value="CIL">Coal India Limited (Mining)</option>
            <option value="BHEL">BHEL Heavy Electricals (Heavy Eng.)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">Industrial Sector</label>
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="Power">Power Generation & Transmission</option>
            <option value="Oil & Gas">Oil & Gas Refining & Exploration</option>
            <option value="Steel">Steel & Metallurgy</option>
            <option value="Mining">Mining & Extraction</option>
            <option value="Heavy Engineering">Heavy Machinery & Electricals</option>
          </select>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200 cursor-pointer ${
          dragActive
            ? 'border-blue-500 bg-blue-50/50 scale-[1.01]'
            : selectedFile
            ? 'border-emerald-400 bg-emerald-50/20'
            : 'border-slate-300 bg-white hover:bg-slate-50/80 hover:border-slate-400'
        }`}
      >
        <input
          type="file"
          accept=".csv, .xlsx, .xls"
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <div className="flex flex-col items-center justify-center">
          <div className={`w-14 h-14 rounded-full flex items-center justify-center mb-3 transition-transform ${
            selectedFile ? 'bg-emerald-100 text-emerald-600' : 'bg-blue-50 text-blue-600'
          }`}>
            {selectedFile ? <FileSpreadsheet className="w-7 h-7" /> : <UploadCloud className="w-7 h-7" />}
          </div>

          {selectedFile ? (
            <div>
              <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-100 border border-emerald-200 px-3 py-1 rounded-full">
                ✓ {selectedFile.name}
              </span>
              <p className="text-xs text-slate-500 mt-2 font-medium">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready for schema validation
              </p>
            </div>
          ) : (
            <div>
              <h3 className="text-sm font-bold text-slate-900">Upload CPSE Material Dataset</h3>
              <p className="text-xs text-slate-500 mt-1">Drag & drop your CSV or Excel file here, or click to browse</p>
              <div className="flex items-center justify-center gap-2 mt-3">
                <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">.CSV</span>
                <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">.XLSX</span>
                <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">.XLS</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
