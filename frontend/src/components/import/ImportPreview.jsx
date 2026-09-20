import {
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  ArrowRight,
} from "lucide-react";
import { Button } from "../common/Button";

export const ImportPreview = ({
  validationData,
  onConfirmImport,
  onCancel,
}) => {
  if (!validationData) return null;
  const inventory = validationData.importType === "INVENTORY";

  return (
    <div className="animate-fade-in space-y-5 rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs">
      <div className="flex flex-col justify-between gap-4 rounded-xl border border-slate-200/80 bg-slate-50 p-4 sm:flex-row sm:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
            <FileSpreadsheet className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase text-slate-400">
              FILE READY FOR PIPELINE
            </div>
            <h4 className="font-mono text-sm font-bold text-slate-900">
              {validationData.filename}
            </h4>
            <span className="text-[10px] font-bold text-blue-700">
              {inventory ? "INVENTORY STOCK" : "MATERIAL MASTER"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4 font-mono text-xs font-bold text-slate-700">
          <div className="rounded-lg border bg-white px-3 py-1.5">
            <span className="font-normal text-slate-400">Rows: </span>
            <span className="font-extrabold text-blue-600">
              {validationData.totalRows}
            </span>
          </div>
          <div className="rounded-lg border bg-white px-3 py-1.5">
            <span className="font-normal text-slate-400">Size: </span>
            {validationData.fileSize}
          </div>
        </div>
      </div>

      <div>
        <h4 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-slate-500">
          Pre-Import Schema & Validation Audit
        </h4>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {validationData.validations.map((item, index) => (
            <div
              key={index}
              className={`flex items-center gap-2.5 rounded-lg border p-3 text-xs font-semibold ${item.type === "success" ? "border-emerald-200 bg-emerald-50/60 text-emerald-800" : item.type === "error" ? "border-rose-200 bg-rose-50/60 text-rose-800" : "border-amber-200 bg-amber-50/60 text-amber-800"}`}
            >
              {item.type === "success" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
              ) : (
                <AlertTriangle className="h-4 w-4 shrink-0" />
              )}
              <span>{item.message}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 className="mb-2.5 text-xs font-bold uppercase tracking-wider text-slate-500">
          Sample Dataset Row Preview (First 5 Rows)
        </h4>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="border-b bg-slate-50 text-[10px] font-bold uppercase text-slate-500">
              {inventory ? (
                <tr>
                  <th className="px-3 py-2.5">Material Code</th>
                  <th className="px-3 py-2.5">Warehouse</th>
                  <th className="px-3 py-2.5">Available</th>
                  <th className="px-3 py-2.5">Reserved</th>
                  <th className="px-3 py-2.5">UOM</th>
                  <th className="px-3 py-2.5">Unit Cost</th>
                  <th className="px-3 py-2.5">Action</th>
                </tr>
              ) : (
                <tr>
                  <th className="px-3 py-2.5">Material Code</th>
                  <th className="px-3 py-2.5">Description</th>
                  <th className="px-3 py-2.5">Category</th>
                  <th className="px-3 py-2.5">Technical Specification</th>
                  <th className="px-3 py-2.5">UOM</th>
                </tr>
              )}
            </thead>
            <tbody className="divide-y font-mono">
              {validationData.previewRows.map((row, index) =>
                inventory ? (
                  <tr key={index} className="hover:bg-slate-50">
                    <td className="px-3 py-2.5 font-bold text-blue-600">
                      {row.code}
                    </td>
                    <td className="px-3 py-2.5 font-semibold">
                      {row.warehouse}
                    </td>
                    <td className="px-3 py-2.5">{row.available}</td>
                    <td className="px-3 py-2.5">{row.reserved}</td>
                    <td className="px-3 py-2.5 font-bold">{row.uom}</td>
                    <td className="px-3 py-2.5">
                      {row.unitCost === "" ? "—" : row.unitCost}
                    </td>
                    <td
                      className={`px-3 py-2.5 font-bold ${row.action === "UPDATE" ? "text-amber-700" : "text-emerald-700"}`}
                    >
                      {row.action}
                    </td>
                  </tr>
                ) : (
                  <tr key={index} className="hover:bg-slate-50">
                    <td className="px-3 py-2.5 font-bold text-blue-600">
                      {row.code}
                    </td>
                    <td className="px-3 py-2.5 font-sans font-semibold text-slate-900">
                      {row.description}
                    </td>
                    <td className="px-3 py-2.5 font-sans text-slate-600">
                      {row.category}
                    </td>
                    <td className="max-w-xs truncate px-3 py-2.5 text-[11px] text-slate-500">
                      {row.specification}
                    </td>
                    <td className="px-3 py-2.5 font-bold text-slate-700">
                      {row.uom}
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between border-t pt-3">
        <span className="text-xs text-slate-500">
          Valid rows are ready; blocking-error rows will be skipped.
        </span>
        <div className="flex gap-2">
          <Button variant="secondary" size="md" onClick={onCancel}>
            Choose another file
          </Button>
          <Button
            variant="success"
            size="md"
            icon={ArrowRight}
            onClick={onConfirmImport}
            disabled={validationData.validRows === 0}
          >
            {inventory ? "Import Stock" : "Validate & Import Pipeline"} →
          </Button>
        </div>
      </div>
    </div>
  );
};
