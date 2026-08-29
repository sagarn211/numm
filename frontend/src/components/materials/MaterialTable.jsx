import React from 'react';
import { Eye, GitCompare, Globe2, ArrowRight } from 'lucide-react';
import { getCPSEBadgeColor, getStatusBadgeColor, formatConfidence } from '../../utils/formatters';

export const MaterialTable = ({
  materials = [],
  onSelectMaterial,
  onCompareMaterial,
  onMapMaterial
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden shadow-2xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-extrabold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-4">Material Code</th>
              <th className="py-3 px-4">Description</th>
              <th className="py-3 px-4">CPSE</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Specification</th>
              <th className="py-3 px-4">UOM</th>
              <th className="py-3 px-4">Match Status</th>
              <th className="py-3 px-4">National Code</th>
              <th className="py-3 px-4 text-center">Confidence</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {materials.map((item) => {
              const cpseBadge = getCPSEBadgeColor(item.cpse);
              const statusBadge = getStatusBadgeColor(item.matchStatus);

              return (
                <tr 
                  key={item.id} 
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                  onClick={() => onSelectMaterial(item)}
                >
                  <td className="py-3.5 px-4 font-mono font-bold text-blue-600 group-hover:underline">
                    {item.code}
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-900 max-w-xs truncate">
                    {item.description}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${cpseBadge}`}>
                      {item.cpse}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-medium">
                    {item.category}
                  </td>
                  <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px] max-w-xs truncate">
                    {item.specification}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-700">
                    {item.uom}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${statusBadge}`}>
                      {item.matchStatus}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                    {item.nationalCode ? (
                      <span className="text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">
                        {item.nationalCode}
                      </span>
                    ) : (
                      <span className="text-slate-400 font-normal">—</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold">
                    {item.confidence > 0 ? (
                      <span className={item.confidence >= 90 ? 'text-emerald-600' : 'text-amber-600'}>
                        {formatConfidence(item.confidence)}
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => onSelectMaterial(item)}
                        className="p-1.5 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => onCompareMaterial(item)}
                        className="p-1.5 rounded-md text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                        title="Compare Material"
                      >
                        <GitCompare className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
