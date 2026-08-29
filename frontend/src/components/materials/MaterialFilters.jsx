import React from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';
import { Button } from '../common/Button';

export const MaterialFilters = ({
  search,
  onSearchChange,
  cpse,
  onCpseChange,
  sector,
  onSectorChange,
  status,
  onStatusChange,
  onReset
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-2xs space-y-3 mb-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Search */}
        <div className="relative sm:col-span-2">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search material code, description, specification..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"
          />
        </div>

        {/* CPSE Filter */}
        <div>
          <select
            value={cpse}
            onChange={(e) => onCpseChange(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All CPSEs</option>
            <option value="ONGC">ONGC (Oil & Gas)</option>
            <option value="NTPC">NTPC (Power)</option>
            <option value="SAIL">SAIL (Steel)</option>
            <option value="CIL">CIL (Mining)</option>
            <option value="BHEL">BHEL (Heavy Eng.)</option>
          </select>
        </div>

        {/* Sector Filter */}
        <div>
          <select
            value={sector}
            onChange={(e) => onSectorChange(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Sectors</option>
            <option value="Oil & Gas">Oil & Gas</option>
            <option value="Power">Power</option>
            <option value="Steel">Steel</option>
            <option value="Mining">Mining</option>
            <option value="Heavy Engineering">Heavy Engineering</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <select
            value={status}
            onChange={(e) => onStatusChange(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Match Statuses</option>
            <option value="Matched">Matched</option>
            <option value="Pending Review">Pending Review</option>
            <option value="Unmatched">Unmatched</option>
          </select>
        </div>
      </div>

      {/* Reset Bar */}
      <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
        <span className="text-slate-400 font-medium">Filter parameters active</span>
        <button
          onClick={onReset}
          className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 hover:underline cursor-pointer"
        >
          <RotateCcw className="w-3 h-3" /> Reset Filters
        </button>
      </div>
    </div>
  );
};
