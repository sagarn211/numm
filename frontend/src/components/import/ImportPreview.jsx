import React from 'react';
import { CheckCircle2, AlertTriangle, FileSpreadsheet, ArrowRight } from 'lucide-react';
import { Button } from '../common/Button';

export const ImportPreview = ({ validationData, onConfirmImport }) => {
  if (!validationData) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs space-y-5 animate-fade-in">
      
      {/* Top File Summary Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase">FILE READY FOR PIPELINE</div>
            <h4 className="text-sm font-bold text-slate-900 font-mono">{validationData.filename}</h4>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono font-bold text-slate-700">
          <div className="bg-white px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="text-slate-400 font-normal">Rows: </span>
            <span className="text-blue-600 font-extrabold">{validationData.totalRows}</span>
          </div>
          <div className="bg-white px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="text-slate-400 font-normal">Size: </span>
            <span>{validationData.fileSize}</span>
          </div>
        </div>
      </div>

      {/* Validation Checklist Grid */}
      <div>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
          Pre-Import Schema & Validation Audit
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {validationData.validations.map((val, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border text-xs font-semibold flex items-center gap-2.5 ${
                val.type === 'success'
                  ? 'bg-emerald-50/60 text-emerald-800 border-emerald-200'
                  : 'bg-amber-50/60 text-amber-800 border-amber-200'
              }`}
            >
              {val.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              )}
              <span>{val.message}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Preview Table */}
      <div>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
          Sample Dataset Row Preview (First 5 Rows)
        </h4>
        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold text-slate-500 uppercase">
              <tr>
                <th className="py-2.5 px-3">Material Code</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Technical Specification</th>
                <th className="py-2.5 px-3">UOM</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {validationData.previewRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-bold text-blue-600">{row.code}</td>
                  <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">{row.description}</td>
                  <td className="py-2.5 px-3 font-sans text-slate-600">{row.category}</td>
                  <td className="py-2.5 px-3 text-slate-500 text-[11px] truncate max-w-xs">{row.specification}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-700">{row.uom}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirm Action Button */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100">
        <span className="text-xs text-slate-500">Validation passed. Data pipeline is ready to initiate.</span>
        <Button variant="success" size="md" icon={ArrowRight} onClick={onConfirmImport}>
          Validate & Import Pipeline →
        </Button>
      </div>

    </div>
  );
};
