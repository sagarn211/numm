import React from 'react';
import { History } from 'lucide-react';

export const RecentActivity = ({ activities = [] }) => {
  // Mock timeline activities if empty or use passed array formatted nicely
  const defaultActivities = [
    { id: '1', time: '10 mins ago', text: <>Batch import from <strong>CIL</strong> completed.</>, dotColor: 'bg-blue-600' },
    { id: '2', time: '1 hour ago', text: <>AI Engine finalized standardization for <strong>Pump category</strong>.</>, dotColor: 'bg-indigo-500' },
    { id: '3', time: '3 hours ago', text: <>Manual approval by Admin for <strong>45 conflicting items</strong>.</>, dotColor: 'bg-slate-300 border border-slate-400' },
    { id: '4', time: 'Yesterday', text: <>New CPSE node connected: <strong>BHEL</strong>.</>, dotColor: 'bg-blue-600' }
  ];

  const itemsToDisplay = activities.length > 0 
    ? activities.map(act => ({
        id: act.id,
        time: act.timestamp || 'Just now',
        text: <><strong>{act.cpse}</strong> {act.text}</>,
        dotColor: act.type === 'IMPORT' ? 'bg-blue-600' : act.type === 'AI_MATCH' ? 'bg-indigo-500' : 'bg-emerald-500'
      }))
    : defaultActivities;

  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-6 flex-1 shadow-2xs">
      <h3 className="text-base font-bold text-slate-900 mb-5 flex items-center gap-2">
        <History className="w-5 h-5 text-slate-500" />
        System Activity
      </h3>

      <div className="relative border-l border-slate-200 ml-3 space-y-6">
        {itemsToDisplay.map((item) => (
          <div key={item.id} className="relative pl-6">
            <span className={`absolute -left-1.5 top-1 h-3 w-3 rounded-full ${item.dotColor} ring-4 ring-white`}></span>
            <p className="text-[11px] font-semibold text-slate-400">{item.time}</p>
            <p className="text-sm text-slate-800 mt-0.5 leading-snug">{item.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

