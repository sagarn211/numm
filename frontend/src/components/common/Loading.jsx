import React from 'react';
import { Loader2, Sparkles, Cpu } from 'lucide-react';

export const Loading = ({ type = 'spinner', text = 'Loading data...', rows = 4 }) => {
  if (type === 'ai') {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center bg-gradient-to-b from-indigo-50/50 to-cyan-50/50 rounded-xl border border-indigo-100">
        <div className="relative mb-4">
          <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center text-white shadow-lg animate-glow-cyan">
            <Cpu className="w-7 h-7 animate-pulse" />
          </div>
          <Sparkles className="w-5 h-5 text-amber-400 absolute -top-1 -right-1 animate-bounce" />
        </div>
        <h4 className="text-base font-semibold text-slate-800">{text || 'AI Engine analyzing material relationships...'}</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">Comparing technical specifications, standardizing UOMs, and identifying candidate clusters across CPSE records.</p>
      </div>
    );
  }

  if (type === 'skeleton') {
    return (
      <div className="w-full space-y-3 animate-pulse">
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="h-12 bg-slate-100 rounded-lg w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-8 text-slate-500 gap-3">
      <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
      <span className="text-sm font-medium">{text}</span>
    </div>
  );
};
