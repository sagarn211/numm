import { useEffect } from "react";
import { X } from "lucide-react";

export const Modal = ({
  open,
  onClose,
  title,
  subtitle,
  children,
  actions,
  maxWidth = "max-w-2xl",
}) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && open && onClose) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-6">
        <div
          className={`relative w-full ${maxWidth} transform overflow-hidden rounded-2xl bg-white text-left align-middle shadow-[0_20px_50px_-12px_rgba(0,0,0,0.15)] transition-all border border-slate-200/60`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-start justify-between border-b border-slate-100 bg-linear-to-b from-slate-50 to-white px-7 py-5">
            <div>
              <h3 className="text-[17px] font-bold text-slate-900 tracking-tight">
                {title}
              </h3>
              {subtitle && (
                <p className="mt-1 text-xs text-slate-500 font-medium">
                  {subtitle}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="px-7 py-6 max-h-[75vh] overflow-y-auto">
            {children}
          </div>

          {/* Footer Actions */}
          {actions && (
            <div className="flex items-center justify-end gap-3 border-t border-slate-100 bg-slate-50/50 px-7 py-4">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
