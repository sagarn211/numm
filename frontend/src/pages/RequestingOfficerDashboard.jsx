import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Boxes,
  ClipboardList,
  PackageSearch,
  Sparkles,
  Warehouse,
} from "lucide-react";
import { inventoryApi } from "../services/inventoryApi";
import { requestApi } from "../services/requestApi";
import { Button } from "../components/common/Button";
import { Loading } from "../components/common/Loading";
import { useAuth } from "../hooks/useAuth";

const number = (value) => Number(value || 0);

export const RequestingOfficerDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [requests, setRequests] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [requestResponse, inventoryResponse] = await Promise.all([
          requestApi.getAll(),
          inventoryApi.getAll(),
        ]);
        setRequests(requestResponse.data || []);
        setInventory(inventoryResponse.data || []);
      } catch (requestError) {
        setError(
          requestError?.response?.data?.detail ||
            requestError.message ||
            "Unable to load your operational dashboard.",
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const available = useMemo(
    () =>
      inventory.reduce(
        (total, row) =>
          total +
          Math.max(
            number(row.available_quantity) - number(row.reserved_quantity),
            0,
          ),
        0,
      ),
    [inventory],
  );
  const openRequests = requests.filter((request) =>
    [
      "DRAFT",
      "SUBMITTED",
      "PROCUREMENT_REQUIRED",
      "APPROVED",
      "APPROVED_PROCUREMENT",
    ].includes(request.status),
  );

  if (loading)
    return <Loading type="ai" text="Loading your CPSE operations..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">
            My CPSE Operations
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Requests, available stock, and material discovery for{" "}
            {user?.cpse_id ? "your assigned CPSE" : "your organization"}.
          </p>
        </div>
        <Button icon={Sparkles} onClick={() => navigate("/ai-recommendations")}>
          Find Materials with AI
        </Button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          icon={ClipboardList}
          label="Open requests"
          value={openRequests.length}
          note="Draft, submitted, or in progress"
        />
        <Metric
          icon={Warehouse}
          label="Available stock"
          value={available.toLocaleString()}
          note="Units not reserved"
          accent="text-emerald-700"
        />
        <Metric
          icon={Boxes}
          label="Stocked materials"
          value={inventory.length}
          note="Inventory records in your CPSE"
        />
        <Metric
          icon={PackageSearch}
          label="Completed requests"
          value={
            requests.filter((request) => request.status === "FULFILLED").length
          }
          note="Material requests fulfilled"
          accent="text-blue-700"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-2xl border bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900">My material requests</h3>
              <p className="text-xs text-slate-500">
                Track the latest requests for your CPSE.
              </p>
            </div>
            <button
              onClick={() => navigate("/requests")}
              className="text-xs font-semibold text-blue-700 hover:underline"
            >
              View all
            </button>
          </div>
          <div className="space-y-3">
            {requests.slice(0, 5).map((request) => (
              <div
                key={request.id}
                className="flex items-center justify-between gap-3 rounded-xl border p-3"
              >
                <div>
                  <div className="font-mono text-sm font-bold text-blue-700">
                    {request.request_number}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    Created {request.created_at?.slice(0, 10) || "—"}
                  </div>
                </div>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold text-slate-700">
                  {request.status}
                </span>
              </div>
            ))}
            {!requests.length && (
              <p className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-500">
                No material requests yet.
              </p>
            )}
          </div>
        </section>
        <section className="rounded-2xl border bg-slate-900 p-5 text-white">
          <h3 className="font-bold">What would you like to do?</h3>
          <p className="mt-1 text-xs text-slate-300">
            Discover an approved product, compare specifications, or start a
            reuse request.
          </p>
          <div className="mt-5 space-y-2">
            <Action
              label="Search national products"
              onClick={() => navigate("/ai-recommendations")}
            />
            <Action
              label="Search using an image"
              onClick={() => navigate("/visual-search")}
            />
            <Action
              label="Compare materials"
              onClick={() => navigate("/comparison")}
            />
            <Action
              label="Create material request"
              onClick={() => navigate("/requests")}
            />
          </div>
        </section>
      </div>
    </div>
  );
};

const Metric = ({
  icon: Icon,
  label,
  value,
  note,
  accent = "text-slate-900",
}) => (
  <section className="rounded-2xl border bg-white p-4">
    <Icon className="h-5 w-5 text-blue-600" />
    <p className="mt-3 text-[11px] font-bold uppercase tracking-wide text-slate-500">
      {label}
    </p>
    <p className={`mt-1 text-2xl font-bold ${accent}`}>{value}</p>
    <p className="mt-1 text-xs text-slate-500">{note}</p>
  </section>
);
const Action = ({ label, onClick }) => (
  <button
    onClick={onClick}
    className="flex w-full items-center justify-between rounded-lg border border-slate-700 px-3 py-3 text-left text-sm font-semibold hover:bg-slate-800"
  >
    <span>{label}</span>
    <ArrowRight className="h-4 w-4" />
  </button>
);
