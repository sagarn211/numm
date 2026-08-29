import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Sparkles, Globe2 } from 'lucide-react';
import { Button } from '../common/Button';
import { getCPSEBadgeColor } from '../../utils/formatters';

export const ComparisonPanel = ({ comparisonData, onCreateMapping }) => {
  if (!comparisonData) return null;

  const { materialA, materialB, comparisons, aiVerdict, confidenceScore, suggestedNationalCode } = comparisonData;

  const badgeA = getCPSEBadgeColor(materialA.cpse);
  const badgeB = getCPSEBadgeColor(materialB.cpse);

  return (
    <div className="space-y-6">
      
      {/* Side-by-Side Item Headers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Material A */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded border ${badgeA}`}>
              {materialA.cpse} (Source A)
            </span>
            <span className="font-mono font-bold text-blue-600 text-xs">{materialA.code}</span>
          </div>
          <h3 className="text-sm font-bold text-slate-900">{materialA.description}</h3>
          <p className="text-xs text-slate-500 font-mono mt-1">{materialA.category} • UOM: {materialA.uom}</p>
        </div>

        {/* Material B */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs">
          <div className="flex items-center justify-between mb-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded border ${badgeB}`}>
              {materialB.cpse} (Source B)
            </span>
            <span className="font-mono font-bold text-blue-600 text-xs">{materialB.code}</span>
          </div>
          <h3 className="text-sm font-bold text-slate-900">{materialB.description}</h3>
          <p className="text-xs text-slate-500 font-mono mt-1">{materialB.category} • UOM: {materialB.uom}</p>
        </div>

      </div>

      {/* Parameter Field Comparison Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden shadow-2xs">
        <div className="p-4 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
          <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-700">
            Technical Parameter Audit Grid
          </h4>
          <span className="text-[11px] text-slate-400 font-mono">8 Field Checks Evaluated</span>
        </div>

        <div className="divide-y divide-slate-100 text-xs">
          {comparisons.map((comp, idx) => {
            const isMatch = comp.status === 'MATCH';
            const isDiff = comp.status === 'DIFFERENCE';

            return (
              <div key={idx} className="grid grid-cols-1 md:grid-cols-12 gap-2 p-3.5 items-center hover:bg-slate-50">
                <div className="md:col-span-3 font-bold text-slate-700 flex items-center gap-2">
                  {isMatch ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  ) : isDiff ? (
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                  )}
                  <span>{comp.field}</span>
                </div>

                <div className={`md:col-span-4 p-2 rounded-lg font-mono text-[11px] ${
                  isMatch ? 'bg-emerald-50/50 text-emerald-900' : 'bg-amber-50/50 text-amber-900'
                }`}>
                  {comp.textA}
                </div>

                <div className="md:col-span-1 text-center font-extrabold font-mono text-[10px]">
                  <span className={`px-2 py-0.5 rounded ${
                    isMatch ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {comp.status}
                  </span>
                </div>

                <div className={`md:col-span-4 p-2 rounded-lg font-mono text-[11px] ${
                  isMatch ? 'bg-emerald-50/50 text-emerald-900' : 'bg-amber-50/50 text-amber-900'
                }`}>
                  {comp.textB}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Verdict Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-xl border border-cyan-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs">
            <Sparkles className="w-4 h-4" />
            <span>AI VERDICT & CONFIDENCE EVALUATION</span>
          </div>
          <p className="text-sm font-semibold text-slate-200 mt-1 max-w-xl">{aiVerdict}</p>
          <div className="text-xs text-slate-400 mt-2 flex items-center gap-3">
            <span>Match Confidence: <strong className="text-emerald-400 font-mono">{confidenceScore}%</strong></span>
            <span>Target National Code: <strong className="text-cyan-300 font-mono">{suggestedNationalCode}</strong></span>
          </div>
        </div>

        <Button
          variant="success"
          size="lg"
          icon={Globe2}
          onClick={() => onCreateMapping(suggestedNationalCode)}
        >
          Create National Mapping
        </Button>
      </div>

    </div>
  );
};
