import React from 'react';
import { GitCompare, Globe2, CheckCircle2, ShieldCheck, Sparkles, Building2, Calendar, FileText } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { getCPSEBadgeColor, getStatusBadgeColor, formatConfidence } from '../../utils/formatters';

export const MaterialCard = ({
  material,
  open,
  onClose,
  onCompare,
  onMap
}) => {
  if (!material) return null;

  const cpseBadge = getCPSEBadgeColor(material.cpse);
  const statusBadge = getStatusBadgeColor(material.matchStatus);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Material Specification: ${material.code}`}
      subtitle={`Source Enterprise: ${material.cpse} (${material.sector})`}
      maxWidth="max-w-3xl"
      actions={
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" icon={GitCompare} onClick={() => onCompare(material)}>
            Compare Specs
          </Button>
          <Button variant="primary" size="sm" icon={Globe2} onClick={() => onMap(material)}>
            Map to National Code
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Top Summary Banner */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-2 py-0.5 rounded border ${cpseBadge}`}>
                {material.cpse}
              </span>
              <span className="text-xs text-slate-500 font-medium">Category: {material.category}</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 mt-1">{material.description}</h3>
          </div>
          <div className="text-right shrink-0">
            <div className="text-[10px] font-bold text-slate-400 uppercase">Current Match Status</div>
            <span className={`inline-block mt-0.5 text-xs font-bold px-2.5 py-1 rounded-full border ${statusBadge}`}>
              {material.matchStatus}
            </span>
          </div>
        </div>

        {/* Technical Specification Parameters */}
        <div>
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <FileText className="w-4 h-4 text-blue-600" />
            Technical Specifications & Metallurgy
          </h4>
          <div className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs leading-relaxed border border-slate-800">
            {material.specification}
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Unit of Measure (UOM)</div>
            <div className="text-sm font-extrabold text-slate-900 font-mono mt-0.5">{material.uom}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Material Grade</div>
            <div className="text-sm font-extrabold text-slate-900 font-mono mt-0.5">{material.grade || 'SS316'}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Nominal Dimension</div>
            <div className="text-sm font-extrabold text-slate-900 font-mono mt-0.5">{material.size || 'DN50 / 2"'}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div className="text-[10px] text-slate-400 font-bold uppercase">Manufacturer</div>
            <div className="text-sm font-extrabold text-slate-900 mt-0.5 truncate">{material.manufacturer || 'Industrial Grade'}</div>
          </div>
        </div>

        {/* Potential National Match & AI Confidence */}
        {material.nationalCode && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-50 to-blue-50 border border-cyan-200 text-xs">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-600" />
                <span className="font-bold text-slate-900">National Material Mapping Candidate</span>
              </div>
              <span className="font-bold text-cyan-700 bg-cyan-100 px-2 py-0.5 rounded font-mono">
                {material.nationalCode}
              </span>
            </div>
            <p className="text-slate-600">
              AI Confidence Score: <strong className="text-emerald-700">{formatConfidence(material.confidence)}</strong>. Matches National Standard SS316 Ball Valve DN50 PN16.
            </p>
          </div>
        )}

        {/* Audit Dates */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100">
          <span>Record ID: {material.id}</span>
          <span>Last Synchronized: {material.lastUpdated}</span>
        </div>
      </div>
    </Modal>
  );
};
