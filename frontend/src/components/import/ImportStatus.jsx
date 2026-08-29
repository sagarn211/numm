import React from 'react';
import { UploadCloud, CheckCircle2, Cpu, Database, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '../common/Button';

export const ImportStatus = ({ progressData, onComplete }) => {
  if (!progressData) return null;

  const stages = [
    { key: 'UPLOAD', label: 'UPLOAD', icon: UploadCloud },
    { key: 'VALIDATE', label: 'VALIDATE', icon: CheckCircle2 },
    { key: 'NORMALIZE', label: 'NORMALIZE', icon: Cpu },
    { key: 'STORE', label: 'STORE', icon: Database },
    { key: 'AI MATCH', label: 'AI MATCH', icon: Sparkles }
  ];

  const currentStageIndex = 2; // e.g. NORMALIZE is active at 82%

  return (
    <div className="bg-gradient-to-br from-[#0B1220] via-[#0F172A] to-[#1E1B4B] rounded-2xl p-6 border border-slate-800 text-white shadow-xl space-y-6 animate-fade-in">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <span className="text-[10px] font-extrabold font-mono uppercase text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-full border border-cyan-500/30">
            LIVE DATA PIPELINE
          </span>
          <h3 className="text-lg font-extrabold text-white tracking-tight mt-1.5">Processing CPSE Master Dataset</h3>
        </div>
        <div className="text-right">
          <span className="text-2xl font-black font-mono text-cyan-400">{progressData.progress}%</span>
          <p className="text-[11px] text-slate-400 font-mono">Row {progressData.processedRows} / {progressData.totalRows}</p>
        </div>
      </div>

      {/* Pipeline Stage Indicators */}
      <div className="grid grid-cols-5 gap-2 relative">
        {stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isDone = idx < currentStageIndex;
          const isActive = idx === currentStageIndex;

          return (
            <div key={stage.key} className="flex flex-col items-center text-center group">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold mb-2 transition-all ${
                isDone 
                  ? 'bg-emerald-500 text-slate-950 font-black shadow-md' 
                  : isActive 
                  ? 'bg-gradient-to-tr from-blue-600 to-cyan-400 text-white shadow-lg ring-4 ring-cyan-500/30 animate-pulse'
                  : 'bg-slate-900 border border-slate-800 text-slate-500'
              }`}>
                {isActive ? <Loader2 className="w-5 h-5 animate-spin" /> : <Icon className="w-5 h-5" />}
              </div>
              <span className={`text-[10px] font-extrabold tracking-wider uppercase font-mono ${
                isActive ? 'text-cyan-400' : isDone ? 'text-emerald-400' : 'text-slate-500'
              }`}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Animated Pipeline Progress Bar */}
      <div>
        <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden border border-slate-800 p-0.5">
          <div 
            className="gradient-pipeline h-full rounded-full transition-all duration-500"
            style={{ width: `${progressData.progress}%` }}
          />
        </div>
      </div>

      {/* Active Stage Detail Box */}
      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <Loader2 className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase font-mono">Current Activity</span>
            <p className="text-slate-200 font-semibold mt-0.5">{progressData.stageMessage}</p>
          </div>
        </div>
        <Button variant="primary" size="sm" onClick={onComplete}>
          Jump to Recommendations →
        </Button>
      </div>

    </div>
  );
};
