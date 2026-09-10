import { useEffect, useState } from 'react';
import { Building2, Plus, ShieldCheck } from 'lucide-react';
import { cpseApi } from '../services/cpseApi';
import { userApi } from '../services/userApi';
import { Button } from '../components/common/Button';
import { roleLabel } from '../utils/permissions';

const ROLES = [
  'PENDING_USER',
  'SYSTEM_ADMIN',
  'CPSE_DATA_MANAGER',
  'REQUESTING_OFFICER',
  'PROCUREMENT_OFFICER',
  'AUDITOR',
  'CPSE_OFFICER',
];

const needsCpse = role => ['CPSE_DATA_MANAGER', 'REQUESTING_OFFICER', 'CPSE_OFFICER'].includes(role);

export const CPSEManagement = () => {
  const [rows, setRows] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({ name: '', code: '', sector: 'Power' });

  const load = async () => {
    try {
      const [cpseResponse, userResponse] = await Promise.all([cpseApi.getAll(), userApi.getAll()]);
      setRows(cpseResponse.data || []);
      setUsers(userResponse.data || []);
      setError('');
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async event => {
    event.preventDefault();
    try {
      await cpseApi.create(form);
      setForm({ name: '', code: '', sector: 'Power' });
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  const changeUser = (id, field, value) => {
    setUsers(current => current.map(user => user.id === id ? { ...user, [field]: value } : user));
  };

  const saveUser = async user => {
    try {
      if (needsCpse(user.role) && !user.cpse_id) {
        setSuccess('');
        setError(`${user.name} needs an assigned CPSE for the ${roleLabel(user.role)} role.`);
        return;
      }
      const cpseId = needsCpse(user.role) && user.cpse_id
        ? Number(user.cpse_id)
        : null;
      if (cpseId !== null && !Number.isInteger(cpseId)) {
        setError('Select a valid CPSE assignment.');
        return;
      }
      await userApi.updateRole(user.id, user.role, cpseId);
      setError('');
      setSuccess(`${user.name}'s role was assigned successfully.`);
      window.setTimeout(() => setSuccess(''), 4000);
      await load();
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">CPSE & Access Management</h2>
        <p className="text-xs text-slate-500">Participating enterprises, user roles and CPSE assignments</p>
      </div>

      {error && <div className="p-3 bg-rose-50 text-rose-700 rounded-lg text-xs">{error}</div>}
      {success && (
        <div className="fixed right-6 top-20 z-50 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800 shadow-lg" role="status">
          <ShieldCheck className="h-5 w-5" />
          {success}
        </div>
      )}

      <form onSubmit={add} className="bg-white border rounded-xl p-4 grid md:grid-cols-4 gap-3">
        <input required placeholder="CPSE name" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} className="border rounded-lg px-3 py-2 text-xs" />
        <input required placeholder="Code" value={form.code} onChange={event => setForm({ ...form, code: event.target.value })} className="border rounded-lg px-3 py-2 text-xs" />
        <select value={form.sector} onChange={event => setForm({ ...form, sector: event.target.value })} className="border rounded-lg px-3 py-2 text-xs">
          <option>Power</option><option>Oil & Gas</option><option>Steel</option><option>Mining</option><option>Heavy Engineering</option>
        </select>
        <Button icon={Plus}>Add CPSE</Button>
      </form>

      <div className="grid md:grid-cols-3 gap-4">
        {rows.map(cpse => (
          <div key={cpse.id} className="bg-white border rounded-xl p-5">
            <Building2 className="w-5 h-5 text-blue-600" />
            <div className="font-bold mt-3">{cpse.name}</div>
            <div className="font-mono text-blue-600 text-xs">{cpse.code}</div>
            <div className="text-xs text-slate-500 mt-2">{cpse.sector}</div>
          </div>
        ))}
      </div>

      <section className="bg-white border rounded-xl overflow-hidden">
        <div className="p-4 border-b flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="font-bold text-sm">Role-Based Access Control</h3>
            <p className="text-xs text-slate-500">Assign each user one role and, where required, one CPSE.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px]">
              <tr><th className="p-3 text-left">User</th><th className="p-3 text-left">Role</th><th className="p-3 text-left">Assigned CPSE</th><th className="p-3 text-right">Action</th></tr>
            </thead>
            <tbody className="divide-y">
              {users.map(user => (
                <tr key={user.id}>
                  <td className="p-3"><div className="font-bold">{user.name}</div><div className="text-slate-500">{user.email}</div></td>
                  <td className="p-3">
                    <select value={user.role} onChange={event => changeUser(user.id, 'role', event.target.value)} className="border rounded-lg px-2 py-1.5">
                      {ROLES.map(role => <option key={role} value={role}>{roleLabel(role)}</option>)}
                    </select>
                  </td>
                  <td className="p-3">
                    <select
                      value={user.cpse_id || ''}
                      onChange={event => changeUser(user.id, 'cpse_id', event.target.value)}
                      disabled={!needsCpse(user.role)}
                      className="border rounded-lg px-2 py-1.5 disabled:bg-slate-100"
                    >
                      <option value="">No CPSE</option>
                      {rows.map(cpse => <option key={cpse.id} value={cpse.id}>{cpse.code}</option>)}
                    </select>
                  </td>
                  <td className="p-3 text-right"><Button size="sm" onClick={() => saveUser(user)}>Save Access</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
