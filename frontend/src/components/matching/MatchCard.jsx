import React from 'react';
import { Sparkles, ArrowRight, GitCompare, CheckCircle2, XCircle, ShieldAlert } from 'lucide-react';
import { MatchScore } from './MatchScore';
import { Button } from '../common/Button';
import { getCPSEBadgeColor } from '../../utils/formatters';

export const MatchCard = ({
  recommendation,
  onApprove,
  onReject,
  onCompare
}) => {
  const { sourceMaterial, targetMaterial, overallConfidence, aiReasoning, suggestedNationalCode, matchMetrics, confidenceCategory } = recommendation;

  const srcBadge = getCPSEBadgeColor(sourceMaterial.cpse);
  const tgtBadge = getCPSEBadgeColor(targetMaterial.cpse);

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs space-y-4 hover:shadow-md transition-shadow">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-600" />
          <span className="text-xs font-bold text-slate-900">AI Clustering Recommendation</span>
          <span className="text-xs font-mono font-bold text-cyan-700 bg-cyan-50 border border-cyan-200 px-2 py-0.5 rounded">
            Target: {suggestedNationalCode}
          </span>
        </div>

        <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
          confidenceCategory === 'HIGH'
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
            : confidenceCategory === 'MEDIUM'
            ? 'bg-amber-50 text-amber-700 border-amber-200'
            : 'bg-rose-50 text-rose-700 border-rose-200'
        }`}>
          {confidenceCategory === 'HIGH' ? '● High Confidence (90%+)' : confidenceCategory === 'MEDIUM' ? '● Medium Confidence' : '● Needs Human Review'}
        </span>
      </div>

      {/* Side-by-Side Source vs Target Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Source Material A */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${srcBadge}`}>
              {sourceMaterial.cpse}
            </span>
            <span className="font-mono font-bold text-blue-600">{sourceMaterial.code}</span>
          </div>
          <h4 className="font-bold text-slate-900 leading-snug">{sourceMaterial.description}</h4>
          <p className="text-[11px] text-slate-500 font-mono mt-1 line-clamp-2">{sourceMaterial.specification}</p>
        </div>

        {/* Target Material B */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${tgtBadge}`}>
              {targetMaterial.cpse}
            </span>
            <span className="font-mono font-bold text-blue-600">{targetMaterial.code}</span>
          </div>
          <h4 className="font-bold text-slate-900 leading-snug">{targetMaterial.description}</h4>
          <p className="text-[11px] text-slate-500 font-mono mt-1 line-clamp-2">{targetMaterial.specification}</p>
        </div>

      </div>

      {/* MatchScore Visualization Component */}
      <MatchScore confidence={overallConfidence} metrics={matchMetrics} />

      {/* AI Decision Support Reasoning */}
      <div className="p-3 rounded-lg bg-indigo-50/60 border border-indigo-100 text-xs flex items-start gap-2.5">
        <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-indigo-900">AI Decision Support Reasoning: </span>
          <span className="text-indigo-800">{aiReasoning}</span>
        </div>
      </div>

      {/* Action Triggers */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
        <Button variant="ghost" size="sm" icon={GitCompare} onClick={() => onCompare(sourceMaterial.code, targetMaterial.code)}>
          Compare Side-by-Side
        </Button>
        <div className="flex items-center gap-2">
          <Button variant="danger" size="sm" icon={XCircle} onClick={() => onReject(recommendation.id)}>
            Reject Candidate
          </Button>
          <Button variant="success" size="sm" icon={CheckCircle2} onClick={() => onApprove(recommendation.id)}>
            Approve Mapping
          </Button>
        </div>
      </div>

    </div>
  );
};
