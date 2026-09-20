import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  CheckCircle2,
  ClipboardList,
  PackageCheck,
  Plus,
  Send,
  XCircle,
} from "lucide-react";
import { requestApi } from "../services/requestApi";
import { cpseApi } from "../services/cpseApi";
import { nationalMaterialApi } from "../services/nationalMaterialApi";
import { Button } from "../components/common/Button";
import { useAuth } from "../hooks/useAuth";
import { hasPermission } from "../utils/permissions";

export const MaterialRequests = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [requests, setRequests] = useState([]);
  const [cpses, setCpses] = useState([]);
  const [nationals, setNationals] = useState([]);
  const [cpse, setCpse] = useState(user?.cpse_id ? String(user.cpse_id) : "");
  const [manualCpse, setManualCpse] = useState("");
  const [draft, setDraft] = useState(null);
  const [nationalId, setNationalId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [draftItems, setDraftItems] = useState([]);
  const [draftAllocationPreview, setDraftAllocationPreview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [actingId, setActingId] = useState(null);
  const [openRequestId, setOpenRequestId] = useState(null);
  const [requestItems, setRequestItems] = useState({});
  const [requestAllocations, setRequestAllocations] = useState({});
  const [detailLoading, setDetailLoading] = useState(null);
  const [error, setError] = useState("");

  const canCreate = hasPermission(user, "request.create");
  const canApprove = hasPermission(user, "request.approve");
  const canFulfill = hasPermission(user, "request.fulfill");
  const canCreateManualRequest = hasPermission(user, "*");

  useEffect(() => {
    // Keep the controlled field aligned when authentication is restored.
    setCpse(user?.cpse_id ? String(user.cpse_id) : "");
  }, [user?.cpse_id]);

  const load = async () => {
    setLoading(true);
    try {
      const [requestResponse, cpseResponse, nationalResponse] =
        await Promise.all([
          requestApi.getAll(),
          cpseApi.getAll(),
          nationalMaterialApi.getNationalMaterials(),
        ]);
      setRequests(requestResponse.data || []);
      setCpses(cpseResponse.data || []);
      setNationals(nationalResponse.data || []);
      setError("");
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // Data loads when the authenticated user changes.
  }, [user?.id]);

  useEffect(() => {
    const requestId = location.state?.createdRequestId;
    if (!requestId) return;
    requestApi
      .getById(requestId)
      .then((response) => {
        setDraft(response.data.request);
        setDraftItems(response.data.items || []);
      })
      .catch((requestError) =>
        setError(requestError?.response?.data?.detail || requestError.message),
      );
  }, [location.state?.createdRequestId]);

  const create = async (requestingCpseId = cpse) => {
    if (!requestingCpseId) {
      setError("Choose the CPSE that will receive this material request.");
      return;
    }
    setSaving(true);
    try {
      const created = (await requestApi.create(Number(requestingCpseId))).data;
      setDraft(created);
      setDraftItems([]);
      setDraftAllocationPreview([]);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setSaving(false);
    }
  };

  const add = async () => {
    const requestedQuantity = Number(quantity);
    if (
      !draft ||
      !nationalId ||
      !Number.isFinite(requestedQuantity) ||
      requestedQuantity <= 0
    ) {
      setError(
        "Select a National Material and enter a quantity greater than zero.",
      );
      return;
    }
    setSaving(true);
    try {
      const item = await requestApi.addItem(draft.id, {
        national_material_id: Number(nationalId),
        requested_quantity: requestedQuantity,
        uom: nationals.find((x) => x.id === Number(nationalId))?.uom || "EA",
      });
      setDraftItems((current) => [...current, item.data]);
      setDraftAllocationPreview([]);
      setNationalId("");
      setQuantity(1);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setSaving(false);
    }
  };

  const previewDraftAllocation = async () => {
    if (!draft || !draftItems.length) return;
    setSaving(true);
    setError("");
    try {
      const response = await requestApi.previewAllocation(draft.id);
      setDraftAllocationPreview(response.data || []);
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setSaving(false);
    }
  };

  const submit = async () => {
    if (!draftItems.length) {
      setError("Add at least one material and quantity before submitting.");
      return;
    }
    setSaving(true);
    try {
      await requestApi.submit(draft.id);
      setDraft(null);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setSaving(false);
    }
  };

  const approve = async (id) => {
    setActingId(id);
    setError("");
    try {
      await requestApi.approve(id);
      setRequestItems((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      setRequestAllocations((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setActingId(null);
    }
  };

  const reject = async (id) => {
    setActingId(id);
    setError("");
    try {
      await requestApi.reject(id);
      setRequestItems((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      setRequestAllocations((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setActingId(null);
    }
  };

  const fulfill = async (id) => {
    setActingId(id);
    setError("");
    try {
      await requestApi.fulfill(id);
      setRequestItems((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      setRequestAllocations((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setActingId(null);
    }
  };

  const toggleRequestDetails = async (id) => {
    if (openRequestId === id) {
      setOpenRequestId(null);
      return;
    }
    setError("");
    setDetailLoading(id);
    try {
      if (!requestItems[id]) {
        const response = await requestApi.getById(id);
        setRequestItems((current) => ({
          ...current,
          [id]: response.data.items || [],
        }));
        setRequestAllocations((current) => ({
          ...current,
          [id]: response.data.allocations || [],
        }));
      }
      setOpenRequestId(id);
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    } finally {
      setDetailLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Material Requests</h2>
        <p className="text-xs text-slate-500">
          Cross-CPSE reuse and reservation workflow
        </p>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 text-rose-700 rounded-lg text-xs">
          {error}
        </div>
      )}

      {canCreate && !draft && (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-blue-200 bg-blue-50 p-4">
            <div className="text-sm font-semibold text-slate-900">
              Request for my CPSE
            </div>
            <p className="mt-1 text-xs text-slate-600">
              Create a request for your assigned CPSE. Supplier CPSEs are chosen
              automatically when you submit the material quantities.
            </p>
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="text-xs text-slate-700">
                Receiving CPSE:{" "}
                <strong>
                  {cpses.find((item) => item.id === Number(cpse))?.code ||
                    "Not assigned"}
                </strong>
              </span>
              <Button
                icon={Plus}
                onClick={() => create(cpse)}
                loading={saving}
                disabled={!cpse}
              >
                Create Draft
              </Button>
            </div>
          </section>
          {canCreateManualRequest && (
            <section className="rounded-xl border bg-white p-4">
              <div className="text-sm font-semibold text-slate-900">
                Manual CPSE request
              </div>
              <p className="mt-1 text-xs text-slate-600">
                For an authorized central user ordering on behalf of a different
                CPSE.
              </p>
              <div className="mt-3 flex gap-3">
                <select
                  value={manualCpse}
                  onChange={(event) => setManualCpse(event.target.value)}
                  className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-xs"
                >
                  <option value="">Receiving CPSE</option>
                  {cpses.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.code}
                    </option>
                  ))}
                </select>
                <Button
                  icon={Plus}
                  onClick={() => create(manualCpse)}
                  loading={saving}
                  disabled={!manualCpse}
                >
                  Create Draft
                </Button>
              </div>
            </section>
          )}
        </div>
      )}

      {draft && canCreate && (
        <div className="bg-slate-900 text-white rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="font-mono font-bold">{draft.request_number}</div>
              <div className="mt-1 text-xs text-slate-300">
                Draft request — add material quantities, then submit for
                allocation.
              </div>
            </div>
            <span className="rounded-full bg-amber-400/20 px-2 py-1 text-[10px] font-bold text-amber-200">
              DRAFT
            </span>
          </div>
          <div className="grid md:grid-cols-4 gap-3">
            <select
              value={nationalId}
              onChange={(event) => setNationalId(event.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs md:col-span-2"
            >
              <option value="">National Material</option>
              {nationals.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nationalCode} — {item.standardTitle}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="0.01"
              step="any"
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs"
            />
            <Button
              variant="secondary"
              onClick={add}
              loading={saving}
              disabled={!nationalId}
            >
              Add Item
            </Button>
          </div>
          {draftItems.length > 0 && (
            <div className="rounded-lg border border-slate-700 divide-y divide-slate-700">
              {draftItems.map((item) => {
                const national = nationals.find(
                  (x) => x.id === item.national_material_id,
                );
                return (
                  <div
                    key={item.id}
                    className="flex justify-between gap-3 p-2 text-xs"
                  >
                    <span>
                      {national?.nationalCode ||
                        `National Material #${item.national_material_id}`}
                    </span>
                    <strong>
                      {item.requested_quantity} {item.uom}
                    </strong>
                  </div>
                );
              })}
            </div>
          )}
          {draftItems.length > 0 && (
            <Button
              variant="secondary"
              onClick={previewDraftAllocation}
              loading={saving}
            >
              Preview automatic allocation
            </Button>
          )}
          {draftAllocationPreview.length > 0 && (
            <div className="rounded-lg border border-emerald-800 bg-emerald-950/30 p-3 text-xs">
              <div className="mb-2 font-semibold text-emerald-200">
                Automatic supplier allocation
              </div>
              {draftAllocationPreview.map((result) => {
                const item = draftItems.find(
                  (candidate) => candidate.id === result.request_item_id,
                );
                const national = nationals.find(
                  (material) => material.id === result.national_material_id,
                );
                return (
                  <div key={result.request_item_id} className="mb-2 last:mb-0">
                    <span className="font-medium">
                      {national?.nationalCode ||
                        `National Material #${result.national_material_id}`}
                      :
                    </span>
                    {result.allocations.map((allocation) => (
                      <span
                        key={allocation.inventory_id}
                        className="ml-2 inline-block rounded bg-emerald-900 px-2 py-1"
                      >
                        {cpses.find(
                          (company) => company.id === allocation.source_cpse_id,
                        )?.code || `CPSE #${allocation.source_cpse_id}`}{" "}
                        — {allocation.allocated_quantity} {item?.uom || "units"}
                      </span>
                    ))}
                    {result.unallocated_quantity > 0 && (
                      <span className="ml-2 text-amber-200">
                        {result.unallocated_quantity} {item?.uom || "units"}{" "}
                        requires procurement
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          <Button
            variant="success"
            icon={Send}
            onClick={submit}
            loading={saving}
            disabled={!draftItems.length}
          >
            Submit & Reserve
          </Button>
        </div>
      )}

      <div className="space-y-3">
        {requests.map((request) => (
          <article
            key={request.id}
            className="rounded-xl border bg-white p-4 shadow-sm"
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono font-bold text-blue-600">
                    {request.request_number}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-700">
                    {request.status}
                  </span>
                </div>
                <div className="mt-2 grid gap-1 text-xs text-slate-600 sm:grid-cols-2 sm:gap-x-8">
                  <span>
                    <strong className="text-slate-800">Requesting CPSE:</strong>{" "}
                    {cpses.find(
                      (item) => item.id === request.requesting_cpse_id,
                    )?.code || request.requesting_cpse_id}
                  </span>
                  <span>
                    <strong className="text-slate-800">Created:</strong>{" "}
                    {request.created_at?.slice(0, 10) || "—"}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 lg:justify-end">
                <Button
                  variant="secondary"
                  size="sm"
                  loading={detailLoading === request.id}
                  onClick={() => toggleRequestDetails(request.id)}
                >
                  {openRequestId === request.id
                    ? "Hide materials"
                    : "View materials"}
                </Button>
                {(request.status === "SUBMITTED" ||
                  request.status === "PROCUREMENT_REQUIRED") &&
                  canApprove &&
                  request.requested_by !== user?.id && (
                    <>
                      <Button
                        variant="success"
                        size="sm"
                        icon={CheckCircle2}
                        loading={actingId === request.id}
                        onClick={() => approve(request.id)}
                      >
                        {request.status === "PROCUREMENT_REQUIRED"
                          ? "Approve procurement"
                          : "Approve"}
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        icon={XCircle}
                        loading={actingId === request.id}
                        onClick={() => reject(request.id)}
                      >
                        Reject
                      </Button>
                    </>
                  )}
                {(request.status === "SUBMITTED" ||
                  request.status === "PROCUREMENT_REQUIRED") &&
                  request.requested_by === user?.id && (
                    <span className="text-slate-500">
                      Waiting for another approver
                    </span>
                  )}
                {request.status === "APPROVED" && canFulfill && (
                  <Button
                    variant="primary"
                    size="sm"
                    icon={PackageCheck}
                    loading={actingId === request.id}
                    onClick={() => fulfill(request.id)}
                  >
                    Fulfill
                  </Button>
                )}
                {request.status === "DRAFT" && (
                  <span className="text-slate-500">
                    Complete draft and submit
                  </span>
                )}
                {request.status === "REJECTED" && (
                  <span className="font-medium text-rose-600">Rejected</span>
                )}
                {request.status === "FULFILLED" && (
                  <span className="font-medium text-emerald-700">
                    Fulfilled
                  </span>
                )}
                {request.status === "PROCUREMENT_REQUIRED" && (
                  <span className="font-medium text-amber-700">
                    Partial stock reserved; procurement required
                  </span>
                )}
                {request.status === "APPROVED_PROCUREMENT" && (
                  <span className="font-medium text-amber-700">
                    Approved for procurement
                  </span>
                )}
              </div>
            </div>
            {openRequestId === request.id && (
              <div className="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-xs">
                <div className="mb-2 font-semibold text-slate-700">
                  Requested materials
                </div>
                <div className="space-y-2">
                  {(requestItems[request.id] || []).map((item) => {
                    const national = nationals.find(
                      (material) => material.id === item.national_material_id,
                    );
                    const supplierAllocations = (
                      requestAllocations[request.id] || []
                    ).filter(
                      (allocation) =>
                        allocation.request_item_id === item.id &&
                        allocation.status !== "RELEASED",
                    );
                    const allocated = supplierAllocations.reduce(
                      (sum, allocation) =>
                        sum + Number(allocation.allocated_quantity || 0),
                      0,
                    );
                    const shortage = Math.max(
                      Number(item.requested_quantity || 0) - allocated,
                      0,
                    );
                    return (
                      <div
                        key={item.id}
                        className="flex items-start justify-between gap-4 rounded-md border bg-white p-3"
                      >
                        <div>
                          <div className="font-mono font-semibold text-blue-600">
                            {national?.nationalCode ||
                              `National Material #${item.national_material_id}`}
                          </div>
                          <div className="mt-1 text-slate-700">
                            {national?.standardTitle ||
                              "Material description unavailable"}
                          </div>
                          {shortage > 0 && (
                            <div className="mt-2 font-medium text-amber-700">
                              {allocated} {item.uom} reserved from inventory ·{" "}
                              {shortage} {item.uom} requires procurement
                            </div>
                          )}
                        </div>
                        <strong className="whitespace-nowrap text-slate-800">
                          {item.requested_quantity} {item.uom}
                        </strong>
                      </div>
                    );
                  })}
                  {!requestItems[request.id]?.length && (
                    <div className="text-slate-500">
                      No material items were added to this request.
                    </div>
                  )}
                </div>
              </div>
            )}
          </article>
        ))}
        {loading && (
          <div className="p-8 text-center text-slate-400">
            Loading requests…
          </div>
        )}
        {!loading && !requests.length && (
          <div className="p-8 text-center text-slate-400">
            <ClipboardList className="w-8 h-8 mx-auto" />
            No requests yet
          </div>
        )}
      </div>
    </div>
  );
};
