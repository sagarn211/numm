import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/common/Button";
import { Loading } from "../components/common/Loading";

export const ProcurementOpportunities = () => {
  const { user } = useAuth();
  const [rows, setRows] = useState(null);
  const [nationals, setNationals] = useState([]);
  const [nationalId, setNationalId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([
      api.get("/api/procurement/opportunities"),
      api.get("/api/national-materials", { params: { limit: 500 } }),
    ])
      .then(([opportunities, materials]) => {
        if (active) {
          setRows(opportunities.data);
          setNationals(materials.data);
        }
      })
      .catch((err) => {
        if (active)
          setError(
            err?.response?.data?.detail ||
              err.message ||
              "Unable to load procurement intelligence.",
          );
      });
    return () => {
      active = false;
    };
  }, []);
  const selected = nationals.find((row) => String(row.id) === nationalId);
  const runPreview = async () => {
    setError("");
    setPreview(null);
    try {
      const response = await api.post("/api/procurement/reuse-preview", {
        national_material_id: Number(nationalId),
        requesting_cpse_id: Number(user.cpse_id),
        requested_quantity: Number(quantity),
        uom: selected.unit,
      });
      setPreview(response.data);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err.message ||
          "Unable to calculate reuse preview.",
      );
    }
  };
  if (rows === null && !error) return <Loading type="skeleton" rows={6} />;
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold">
          National Procurement Opportunity Engine
        </h2>
        <p className="text-xs text-slate-500">
          Rule-based prioritization using current demand, available stock, and
          real procurement history. It does not execute transfers or claim
          savings.
        </p>
      </div>
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          {typeof error === "string" ? error : JSON.stringify(error)}
        </div>
      )}
      {user?.cpse_id && (
        <section className="rounded-xl border bg-white p-4">
          <h3 className="text-sm font-bold">Reuse before buy preview</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            <select
              value={nationalId}
              onChange={(event) => {
                setNationalId(event.target.value);
                setPreview(null);
              }}
              className="min-w-72 rounded border px-3 py-2 text-xs"
            >
              <option value="">Select National Material</option>
              {nationals.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.national_code} · {row.description}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="0.0001"
              step="any"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              placeholder="Required quantity"
              className="rounded border px-3 py-2 text-xs"
            />
            <Button
              disabled={!selected || !(Number(quantity) > 0)}
              onClick={runPreview}
            >
              Check before procurement
            </Button>
          </div>
          {preview && (
            <div className="mt-4 grid gap-3 md:grid-cols-4 text-xs">
              <div className="rounded bg-slate-50 p-3">
                Own stock
                <br />
                <strong>
                  {preview.own_stock_applicable} {preview.uom}
                </strong>
              </div>
              <div className="rounded bg-blue-50 p-3">
                Cross-CPSE reuse
                <br />
                <strong>
                  {preview.cross_cpse_reuse_potential} {preview.uom}
                </strong>
              </div>
              <div className="rounded bg-amber-50 p-3">
                Fresh procurement
                <br />
                <strong>
                  {preview.remaining_fresh_procurement} {preview.uom}
                </strong>
              </div>
              <div className="rounded bg-violet-50 p-3">
                Consolidated review
                <br />
                <strong>
                  {preview.potential_consolidated_procurement} {preview.uom}
                </strong>
              </div>
              <p className="md:col-span-4 text-amber-800">{preview.warning}</p>
            </div>
          )}
        </section>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        {(rows || []).map((row) => (
          <article
            key={row.national_material_id}
            className="rounded-xl border bg-white p-5"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-mono text-xs font-bold text-blue-700">
                  {row.national_code}
                </p>
                <h3 className="font-bold">{row.description}</h3>
              </div>
              <div className="rounded-lg bg-blue-50 px-3 py-2 text-lg font-bold text-blue-800">
                {row.opportunity_score}
              </div>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                Demand
                <br />
                <strong>
                  {row.aggregate_demand} {row.uom}
                </strong>
              </div>
              <div>
                Reusable
                <br />
                <strong>
                  {row.cross_cpse_reuse_potential} {row.uom}
                </strong>
              </div>
              <div>
                Fresh need
                <br />
                <strong>
                  {row.net_fresh_procurement_demand} {row.uom}
                </strong>
              </div>
            </div>
            <p className="mt-4 text-xs">{row.recommendation}</p>
            <p className="mt-2 text-[10px] text-slate-500">
              Score formula: {row.score_formula}
            </p>
          </article>
        ))}
        {rows?.length === 0 && (
          <p className="text-sm text-slate-500">
            No evidence-backed opportunities for the current period.
          </p>
        )}
      </div>
    </div>
  );
};
