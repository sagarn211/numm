import React from 'react';

export const MatchScore = ({ confidence = 97.4, metrics = {} }) => {
  const score = typeof confidence === 'number' ? confidence : parseFloat(confidence || 0);

  const getScoreColor = (val) => {
    if (val >= 90) return { stroke: '#10B981', text: 'text-emerald-600', bg: 'bg-emerald-500' };
    if (val >= 75) return { stroke: '#F59E0B', text: 'text-amber-600', bg: 'bg-amber-500' };
    return { stroke: '#EF4444', text: 'text-rose-600', bg: 'bg-rose-500' };
  };

  const colors = getScoreColor(score);
  const strokeDashoffset = 251.2 - (251.2 * score) / 100;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-5 p-4 rounded-xl bg-slate-50 border border-slate-200/80">
      {/* SVG Circular Animated Match Gauge */}
      <div className="relative w-28 h-28 flex items-center justify-center shrink-0">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background Ring */}
          <circle
            cx="50"
            cy="50"
            r="40"
            stroke="#E2E8F0"
            strokeWidth="8"
            fill="transparent"
          />
          {/* Progress Ring */}
          <circle
            cx="50"
            cy="50"
            r="40"
            stroke={colors.stroke}
            strokeWidth="8"
            strokeDasharray="251.2"
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className={`text-xl font-black font-mono leading-none ${colors.text}`}>
            {score.toFixed(1)}%
          </span>
          <span className="text-[9px] font-bold text-slate-400 uppercase mt-0.5">MATCH SCORE</span>
        </div>
      </div>

      {/* Sub-parameter breakdown bars */}
      <div className="flex-1 w-full space-y-2 text-xs">
        <div>
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-0.5">
            <span>Description Similarity</span>
            <span className="font-mono font-bold text-slate-900">{metrics.descriptionSimilarity || 98.2}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div className="bg-blue-600 h-full rounded-full" style={{ width: `${metrics.descriptionSimilarity || 98.2}%` }}></div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-0.5">
            <span>Specification Similarity</span>
            <span className="font-mono font-bold text-slate-900">{metrics.specificationSimilarity || 96.5}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div className="bg-indigo-600 h-full rounded-full" style={{ width: `${metrics.specificationSimilarity || 96.5}%` }}></div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-0.5">
            <span>Category Similarity</span>
            <span className="font-mono font-bold text-slate-900">{metrics.categorySimilarity || 94.0}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div className="bg-cyan-600 h-full rounded-full" style={{ width: `${metrics.categorySimilarity || 94.0}%` }}></div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-0.5">
            <span>UOM Compatibility</span>
            <span className="font-mono font-bold text-emerald-600">{metrics.uomCompatibility || 100.0}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${metrics.uomCompatibility || 100.0}%` }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};
