import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { formatNumber } from '../../utils/formatters';

export const StatCard = ({
  title,
  value,
  change,
  period = 'this month',
  icon: Icon,
  accentColor = 'blue', // blue | emerald | amber | cyan | indigo | red
  isAiGlow = false,
  isRedAlert = false,
  isGreenBorder = false,
  statusBadge = null,
}) => {
  const isPositive = change && change.startsWith('+');

  const iconVariants = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    cyan: 'bg-cyan-50 text-cyan-600 border-cyan-100',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    red: 'bg-rose-50 text-rose-600 border-rose-100',
  };

  let containerClasses = "bg-white border rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-2xs hover:shadow-md ";

  if (isAiGlow) {
    containerClasses += "ai-border-gradient ai-glow ";
  } else if (isRedAlert) {
    containerClasses += "border-slate-200 border-r-4 border-r-rose-500 hover:border-slate-300 ";
  } else if (isGreenBorder) {
    containerClasses += "border-slate-200 border-l-4 border-l-emerald-500 hover:border-slate-300 ";
  } else {
    containerClasses += "border-slate-200/80 hover:border-slate-300 ";
  }

  return (
    <div className={containerClasses}>
      <div className="flex justify-between items-start">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-1.5 rounded-lg border ${iconVariants[accentColor] || iconVariants.blue} ${isAiGlow ? 'pulse-border' : ''}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-2xl font-black text-slate-900 tracking-tight">
          {typeof value === 'number' ? formatNumber(value) : value}
        </div>
        
        <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-medium">
          {statusBadge ? (
            <span className={`inline-flex items-center gap-1 font-semibold ${statusBadge.color}`}>
              {statusBadge.icon && <statusBadge.icon className="w-3.5 h-3.5" />}
              {statusBadge.text}
            </span>
          ) : change ? (
            <div className={`flex items-center gap-0.5 font-bold ${
              isPositive ? 'text-emerald-600' : 'text-rose-600'
            }`}>
              {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
              <span>{change}</span>
              <span className="text-slate-400 font-normal ml-0.5">{period}</span>
            </div>
          ) : (
            <span className="text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-400" />
              {period}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

