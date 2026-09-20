import { History, Activity } from "lucide-react";

export const RecentActivity = ({ activities = [] }) => {
  const itemsToDisplay = activities.map((act) => ({
    id: act.id,
    time: act.timestamp || "Recorded",
    text: (
      <span>
        {act.cpse && act.cpse !== "SYSTEM" && (
          <strong className="text-blue-600 mr-1">[{act.cpse}]</strong>
        )}
        {act.text}
      </span>
    ),
    dotColor:
      act.type === "IMPORT"
        ? "bg-blue-600"
        : act.type === "AI_MATCH"
          ? "bg-indigo-500"
          : act.type === "APPROVAL"
            ? "bg-emerald-500"
            : "bg-cyan-500",
  }));

  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-6 flex-1 shadow-2xs">
      <h3 className="text-base font-bold text-slate-900 mb-5 flex items-center gap-2">
        <History className="w-5 h-5 text-slate-500" />
        System Activity Audit
      </h3>

      {itemsToDisplay.length > 0 ? (
        <div className="relative border-l border-slate-200 ml-3 space-y-6">
          {itemsToDisplay.map((item) => (
            <div key={item.id} className="relative pl-6">
              <span
                className={`absolute -left-1.5 top-1 h-3 w-3 rounded-full ${item.dotColor} ring-4 ring-white`}
              ></span>
              <p className="text-[11px] font-semibold text-slate-400 font-mono">
                {item.time}
              </p>
              <p className="text-xs text-slate-800 mt-0.5 leading-snug">
                {item.text}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400">
          <Activity className="w-6 h-6 mx-auto mb-2 opacity-50" />
          <p className="text-xs font-semibold">
            No recent activity logs recorded.
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Events are recorded upon imports, matching, and approvals.
          </p>
        </div>
      )}
    </div>
  );
};
