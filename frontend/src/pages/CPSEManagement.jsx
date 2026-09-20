import { useEffect, useState } from "react";
import { Building2, Check, Plus, ShieldCheck, Trash2, X } from "lucide-react";
import { cpseApi } from "../services/cpseApi";
import { userApi } from "../services/userApi";
import { Button } from "../components/common/Button";
import { roleLabel } from "../utils/permissions";

const ROLES = [
  "PENDING_USER",
  "SYSTEM_ADMIN",
  "CPSE_DATA_MANAGER",
  "REQUESTING_OFFICER",
  "PROCUREMENT_OFFICER",
  "AUDITOR",
  "CPSE_OFFICER",
];

const needsCpse = (role) =>
  [
    "CPSE_DATA_MANAGER",
    "REQUESTING_OFFICER",
    "PROCUREMENT_OFFICER",
    "CPSE_OFFICER",
  ].includes(role);

export const CPSEManagement = () => {
  const [rows, setRows] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({ name: "", code: "", sector: "Power" });

  const load = async () => {
    try {
      const [cpseResponse, userResponse] = await Promise.all([
        cpseApi.getAll(),
        userApi.getAll(),
      ]);
      setRows(cpseResponse.data || []);
      setUsers(
        (userResponse.data || []).map((user) => ({
          ...user,
          approval_role: user.requested_role || "REQUESTING_OFFICER",
          approval_cpse_id: user.requested_cpse_id || "",
        })),
      );
      setError("");
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async (event) => {
    event.preventDefault();
    try {
      await cpseApi.create(form);
      setForm({ name: "", code: "", sector: "Power" });
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  const changeUser = (id, field, value) => {
    setUsers((current) =>
      current.map((user) =>
        user.id === id ? { ...user, [field]: value } : user,
      ),
    );
  };

  const saveUser = async (user) => {
    try {
      if (needsCpse(user.role) && !user.cpse_id) {
        setSuccess("");
        setError(
          `${user.name} needs an assigned CPSE for the ${roleLabel(user.role)} role.`,
        );
        return;
      }
      const cpseId =
        needsCpse(user.role) && user.cpse_id ? Number(user.cpse_id) : null;
      if (cpseId !== null && !Number.isInteger(cpseId)) {
        setError("Select a valid CPSE assignment.");
        return;
      }
      await userApi.updateRole(user.id, user.role, cpseId);
      setError("");
      setSuccess(`${user.name}'s role was assigned successfully.`);
      window.setTimeout(() => setSuccess(""), 4000);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  const approveUser = async (user) => {
    try {
      if (needsCpse(user.approval_role) && !user.approval_cpse_id) {
        setError(`${user.name} needs a CPSE assignment before approval.`);
        return;
      }
      await userApi.approve(user.id, user.approval_role, user.approval_cpse_id);
      setError("");
      setSuccess(`${user.name}'s account was approved.`);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  const rejectUser = async (user) => {
    try {
      await userApi.reject(user.id);
      setError("");
      setSuccess(`${user.name}'s account request was rejected.`);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Delete ${user.name}'s account? They will immediately lose access.`)) {
      return;
    }
    try {
      await userApi.delete(user.id);
      setError("");
      setSuccess(`${user.name}'s account was deleted.`);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  const pendingUsers = users.filter(
    (user) => user.account_status === "PENDING",
  );
  const activeUsers = users.filter(
    (user) => user.account_status === "APPROVED",
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">CPSE & Access Management</h2>
        <p className="text-xs text-slate-500">
          Participating enterprises, user roles and CPSE assignments
        </p>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 text-rose-700 rounded-lg text-xs">
          {error}
        </div>
      )}
      {success && (
        <div
          className="fixed right-6 top-20 z-50 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800 shadow-lg"
          role="status"
        >
          <ShieldCheck className="h-5 w-5" />
          {success}
        </div>
      )}

      <form
        onSubmit={add}
        className="bg-white border rounded-xl p-4 grid md:grid-cols-4 gap-3"
      >
        <input
          required
          placeholder="CPSE name"
          value={form.name}
          onChange={(event) => setForm({ ...form, name: event.target.value })}
          className="border rounded-lg px-3 py-2 text-xs"
        />
        <input
          required
          placeholder="Code"
          value={form.code}
          onChange={(event) => setForm({ ...form, code: event.target.value })}
          className="border rounded-lg px-3 py-2 text-xs"
        />
        <select
          value={form.sector}
          onChange={(event) => setForm({ ...form, sector: event.target.value })}
          className="border rounded-lg px-3 py-2 text-xs"
        >
          <option>Power</option>
          <option>Oil & Gas</option>
          <option>Steel</option>
          <option>Mining</option>
          <option>Heavy Engineering</option>
        </select>
        <Button icon={Plus}>Add CPSE</Button>
      </form>

      <div className="grid md:grid-cols-3 gap-4">
        {rows.map((cpse) => (
          <div key={cpse.id} className="bg-white border rounded-xl p-5">
            <Building2 className="w-5 h-5 text-blue-600" />
            <div className="font-bold mt-3">{cpse.name}</div>
            <div className="font-mono text-blue-600 text-xs">{cpse.code}</div>
            <div className="text-xs text-slate-500 mt-2">{cpse.sector}</div>
          </div>
        ))}
      </div>

      <section className="overflow-hidden rounded-xl border border-amber-200 bg-amber-50/40">
        <div className="flex items-center justify-between border-b border-amber-200 px-4 py-3">
          <div>
            <h3 className="text-sm font-bold text-slate-800">
              Pending account requests
            </h3>
            <p className="text-xs text-slate-600">
              Approve access only after verifying the applicant and CPSE
              assignment.
            </p>
          </div>
          <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-800">
            {pendingUsers.length} pending
          </span>
        </div>
        {pendingUsers.length ? (
          <div className="divide-y divide-amber-100">
            {pendingUsers.map((user) => (
              <div
                key={user.id}
                className="grid gap-3 bg-white p-4 lg:grid-cols-[minmax(180px,1fr)_190px_170px_auto] lg:items-end"
              >
                <div>
                  <div className="font-bold text-sm">{user.name}</div>
                  <div className="text-xs text-slate-500">{user.email}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    Requested CPSE:{" "}
                    {rows.find((cpse) => cpse.id === user.requested_cpse_id)
                      ?.code || "Not provided"}
                  </div>
                </div>
                <label className="text-[11px] font-semibold text-slate-600">
                  Role
                  <select
                    value={user.approval_role}
                    onChange={(event) =>
                      changeUser(user.id, "approval_role", event.target.value)
                    }
                    className="mt-1 w-full rounded-lg border bg-white px-2 py-2 text-xs"
                  >
                    {ROLES.filter(
                      (role) =>
                        !["PENDING_USER", "SYSTEM_ADMIN"].includes(role),
                    ).map((role) => (
                      <option key={role} value={role}>
                        {roleLabel(role)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-[11px] font-semibold text-slate-600">
                  CPSE
                  <select
                    value={user.approval_cpse_id}
                    disabled={!needsCpse(user.approval_role)}
                    onChange={(event) =>
                      changeUser(
                        user.id,
                        "approval_cpse_id",
                        event.target.value,
                      )
                    }
                    className="mt-1 w-full rounded-lg border bg-white px-2 py-2 text-xs disabled:bg-slate-100"
                  >
                    <option value="">No CPSE</option>
                    {rows.map((cpse) => (
                      <option key={cpse.id} value={cpse.id}>
                        {cpse.code}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    icon={Check}
                    onClick={() => approveUser(user)}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    icon={X}
                    onClick={() => rejectUser(user)}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="p-5 text-center text-xs text-slate-500">
            No account requests are awaiting approval.
          </p>
        )}
      </section>

      <section className="bg-white border rounded-xl overflow-hidden">
        <div className="p-4 border-b flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="font-bold text-sm">Role-Based Access Control</h3>
            <p className="text-xs text-slate-500">
              Assign each user one role and, where required, one CPSE.
            </p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="p-3 text-left">User</th>
                <th className="p-3 text-left">Role</th>
                <th className="p-3 text-left">Assigned CPSE</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {activeUsers.map((user) => (
                <tr key={user.id}>
                  <td className="p-3">
                    <div className="font-bold">{user.name}</div>
                    <div className="text-slate-500">{user.email}</div>
                  </td>
                  <td className="p-3">
                    <select
                      value={user.role}
                      onChange={(event) =>
                        changeUser(user.id, "role", event.target.value)
                      }
                      className="border rounded-lg px-2 py-1.5"
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>
                          {roleLabel(role)}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="p-3">
                    <select
                      value={user.cpse_id || ""}
                      onChange={(event) =>
                        changeUser(user.id, "cpse_id", event.target.value)
                      }
                      disabled={!needsCpse(user.role)}
                      className="border rounded-lg px-2 py-1.5 disabled:bg-slate-100"
                    >
                      <option value="">No CPSE</option>
                      {rows.map((cpse) => (
                        <option key={cpse.id} value={cpse.id}>
                          {cpse.code}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" onClick={() => saveUser(user)}>
                        Save Access
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        icon={Trash2}
                        onClick={() => deleteUser(user)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
