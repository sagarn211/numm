import { Factory, Flame, Zap, HardHat, Cog } from "lucide-react";
import { formatNumber } from "../../utils/formatters";

const SECTOR_ICONS = {
  "Oil & Gas": Flame,
  Power: Zap,
  Steel: Factory,
  Mining: HardHat,
};

export const SectorCard = ({ sector }) => {
  const Icon = SECTOR_ICONS[sector.name] || Cog;
  const isHighProgress = sector.standardization >= 75;

  return (
    <div className="bg-[#fffaf5] border border-[#e9dfd2] rounded-xl p-4 hover:border-[#d9cab7] transition-all shadow-[0_1px_0_rgba(59,44,35,0.06)] hover:shadow-md flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-[#f3e7dc] text-[#6c4738]">
              <Icon className="w-4 h-4 text-[#6c4738]" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#2f261f] leading-tight">
                {sector.name}
              </h4>
              <span className="text-[10px] font-medium text-[#7a6d63]">
                {sector.cpseList?.join(", ")}
              </span>
            </div>
          </div>
          <span className="bg-[#f1e7dd] px-2 py-0.5 rounded text-[11px] font-medium text-[#5c4d45]">
            {sector.cpseList ? `${sector.cpseList.length} CPSEs` : "Vertical"}
          </span>
        </div>

        <div className="flex justify-between items-end mb-2">
          <span className="font-mono text-xs text-[#6d625c]">
            {formatNumber(sector.materials)} Materials
          </span>
          <span className="text-xs text-[#2f261f] font-bold">
            {sector.standardization}% Standardized
          </span>
        </div>

        <div className="w-full bg-[#efe3d7] rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-1.5 rounded-full transition-all duration-500 ${
              isHighProgress ? "bg-[#7d8f72]" : "bg-[#c58a4f]"
            }`}
            style={{ width: `${sector.standardization}%` }}
          />
        </div>
      </div>
    </div>
  );
};
