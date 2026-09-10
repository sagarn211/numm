import { TrendingUp, TrendingDown, Clock } from 'lucide-react';
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
    blue: 'bg-[#efe2d7] text-[#6c4738] border-[#e1cab0]',
    emerald: 'bg-[#eaf1e7] text-[#5f7158] border-[#cfdcc8]',
    amber: 'bg-[#f4e7d7] text-[#9e7247] border-[#e7ceb0]',
    cyan: 'bg-[#edf3f4] text-[#6f7d74] border-[#dfe7e3]',
    indigo: 'bg-[#efe8e5] text-[#6b5a50] border-[#dfd0c7]',
    red: 'bg-[#f7e5e1] text-[#9a5a4c] border-[#ebc8c1]',
  };

  let containerClasses = "bg-[#fffaf5] border rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-[0_1px_0_rgba(59,44,35,0.06)] hover:shadow-md ";

  if (isAiGlow) {
    containerClasses += "ai-border-gradient ai-glow ";
  } else if (isRedAlert) {
    containerClasses += "border-[#e6d8ce] border-r-4 border-r-[#b75d50] hover:border-[#d9c0b5] ";
  } else if (isGreenBorder) {
    containerClasses += "border-[#e7e0d8] border-l-4 border-l-[#6b8d63] hover:border-[#d9c8ba] ";
  } else {
    containerClasses += "border-[#eae0d6] hover:border-[#d9cab7] ";
  }

  return (
    <div className={containerClasses}>
      <div className="flex justify-between items-start">
        <span className="text-[11px] font-bold text-[#715f57] uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-1.5 rounded-lg border ${iconVariants[accentColor] || iconVariants.blue} ${isAiGlow ? 'pulse-border' : ''}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-2xl font-black text-[#2f261f] tracking-tight">
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
              isPositive ? 'text-[#5f7158]' : 'text-[#a65e51]'
            }`}>
              {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
              <span>{change}</span>
              <span className="text-[#7a6d63] font-normal ml-0.5">{period}</span>
            </div>
          ) : (
            <span className="text-[#7a6d63] flex items-center gap-1">
              <Clock className="w-3 h-3 text-[#7a6d63]" />
              {period}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
