import React from 'react';
import { Factory, Flame, Zap, HardHat, Cog } from 'lucide-react';
import { formatNumber } from '../../utils/formatters';

export const SectorCard = ({ sector }) => {
  const getSectorIcon = (name) => {
    switch (name) {
      case 'Oil & Gas': return Flame;
      case 'Power': return Zap;
      case 'Steel': return Factory;
      case 'Mining': return HardHat;
      default: return Cog;
    }
  };

  const Icon = getSectorIcon(sector.name);
  const isHighProgress = sector.standardization >= 75;

  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-4 hover:border-slate-300 transition-all shadow-2xs hover:shadow-md flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-slate-100 text-slate-600">
              <Icon className="w-4 h-4 text-slate-700" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-900 leading-tight">{sector.name}</h4>
              <span className="text-[10px] font-medium text-slate-400">{sector.cpseList?.join(', ')}</span>
            </div>
          </div>
          <span className="bg-slate-100 px-2 py-0.5 rounded text-[11px] font-medium text-slate-600">
            {sector.cpseList ? `${sector.cpseList.length} CPSEs` : 'Vertical'}
          </span>
        </div>

        <div className="flex justify-between items-end mb-2">
          <span className="font-mono text-xs text-slate-500">{formatNumber(sector.materials)} Materials</span>
          <span className="text-xs text-slate-900 font-bold">{sector.standardization}% Standardized</span>
        </div>

        <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
          <div 
            className={`h-1.5 rounded-full transition-all duration-500 ${
              isHighProgress ? 'bg-blue-600' : 'bg-amber-500'
            }`}
            style={{ width: `${sector.standardization}%` }}
          />
        </div>
      </div>
    </div>
  );
};

