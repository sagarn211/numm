import { useState } from 'react';
import { api } from '../../services/api';
import { Button } from '../common/Button';

export const MappingHistory = ({ materialId, canRestore = false, onRestored }) => {
  const [events, setEvents] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState('');
  const load = async () => {
    setBusy(true); setError('');
    try { setEvents((await api.get(`/api/mapping-history/${materialId}`)).data); }
    catch { setError('Unable to read mapping history.'); }
    finally { setBusy(false); }
  };
  const restore = async event => {
    setBusy(true); setError('');
    try {
      await api.post(`/api/mapping-history/${event.id}/restore`, { reason });
      await load(); await onRestored?.();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : detail?.message || 'Unable to restore this mapping.');
    } finally { setBusy(false); }
  };
  return <div className="mt-2 text-xs">
    <Button size="sm" variant="secondary" loading={busy} onClick={load}>Mapping history</Button>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {events && <div className="mt-2 space-y-2">{!events.length && <p>No mapping history recorded.</p>}
      {canRestore && <input aria-label="Mapping restoration reason" className="w-full rounded border p-2" placeholder="Reason for restoring previous mapping" value={reason} onChange={e => setReason(e.target.value)} />}
      {events.map((event, index) => <div key={event.id} className="rounded border p-2"><p>{event.action} — {event.created_at}</p><p>National identity: {event.details?.before?.national_material_id ?? 'None'} → {event.details?.after?.national_material_id ?? 'None'}</p>{index === 0 && canRestore && event.details?.before?.national_material_id && <Button size="sm" disabled={reason.trim().length < 5 || busy} onClick={() => restore(event)}>Restore previous mapping</Button>}</div>)}
    </div>}
  </div>;
};
