import { useState } from 'react';
import { ExternalLink, Image, LoaderCircle, Upload, ZoomIn } from 'lucide-react';
import { visualSearchApi } from '../services/visualSearchApi';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';

const value = item => item || 'Not specified';

export const VisualMaterialSearch = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const choose = event => {
    const chosen = event.target.files?.[0];
    setFile(chosen || null);
    setPreview(chosen ? URL.createObjectURL(chosen) : '');
    setResults([]); setSelected(null); setError('');
  };

  const search = async () => {
    if (!file) return setError('Choose a JPEG, PNG, or WebP image first.');
    setLoading(true); setError('');
    try { const response = await visualSearchApi.search(file); setResults(response.data.candidates || []); }
    catch (e) { setError(e?.response?.data?.detail || 'Visual search could not be completed.'); }
    finally { setLoading(false); }
  };

  return <div className="space-y-6">
    <div><h2 className="text-xl font-bold">AI Visual Material Discovery</h2><p className="text-xs text-slate-500">Find likely material candidates from a photo. Technical validation is always required.</p></div>
    <section className="rounded-xl border bg-white p-5"><div className="grid gap-5 md:grid-cols-[260px_1fr]">
      <div className="grid h-56 place-items-center overflow-hidden rounded-xl border border-dashed bg-slate-50">{preview ? <img className="h-full w-full object-contain" src={preview} alt="Selected query" /> : <Image className="h-10 w-10 text-slate-300" />}</div>
      <div className="flex flex-col justify-center gap-3"><label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded-lg border px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"><Upload className="h-4 w-4" />Choose photo<input className="hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={choose} /></label><p className="text-xs text-slate-500">JPEG, PNG, or WebP. Use a clear photo of one item where possible.</p><button onClick={search} disabled={loading} className="inline-flex w-fit items-center gap-2 rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{loading && <LoaderCircle className="h-4 w-4 animate-spin" />}Search visual candidates</button></div>
    </div></section>
    {error && <p className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">Visual Similarity is for candidate discovery only. Compare specifications and complete technical validation before any engineering decision.</p>
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">{results.map(item => <article key={item.material_id} className="overflow-hidden rounded-xl border bg-white shadow-sm transition-shadow hover:shadow-md">
      <button type="button" onClick={() => setSelected(item)} className="group relative block h-64 w-full overflow-hidden bg-slate-100 text-left" aria-label={`View details for ${item.material_code}`}>
        {item.primary_image_url ? <img className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105" src={item.primary_image_url} alt={`${item.description} preview`} /> : <div className="grid h-full place-items-center text-xs text-slate-400">No verified image</div>}
        {item.primary_image_url && <span className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1 bg-slate-950/65 py-2 text-xs font-semibold text-white opacity-0 transition-opacity group-hover:opacity-100"><ZoomIn className="h-4 w-4" />Open full preview</span>}
      </button>
      <div className="p-4"><div className="flex justify-between gap-2"><span className="font-mono text-xs font-bold text-blue-700">{item.material_code}</span><span className="shrink-0 rounded-full bg-blue-50 px-2 py-1 text-[10px] font-bold text-blue-700">Visual Similarity {(item.visual_similarity * 100).toFixed(1)}%</span></div><p className="mt-2 text-sm font-semibold text-slate-800">{item.description}</p><p className="mt-1 text-xs text-slate-500">{item.category || 'Unclassified'} {item.national_code ? `• ${item.national_code}` : ''}</p><button type="button" onClick={() => setSelected(item)} className="mt-3 inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:underline">View full details <ZoomIn className="h-3.5 w-3.5" /></button></div>
    </article>)}</div>
    {!loading && !error && file && !results.length && <p className="text-sm text-slate-500">No candidates returned yet.</p>}
    <Modal open={!!selected} onClose={() => setSelected(null)} title={selected?.material_code || 'Material details'} subtitle={selected ? `Visual similarity ${(selected.visual_similarity * 100).toFixed(1)}% · ${selected.cpse_code || `CPSE #${selected.cpse_id}`}` : ''} maxWidth="max-w-5xl" actions={selected && <><Button size="sm" variant="ghost" onClick={() => setSelected(null)}>Close</Button><a href={`/comparison?material_id=${selected.material_id}`}><Button size="sm" icon={ExternalLink}>Compare specifications</Button></a></>}>
      {selected && <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]"><div className="grid min-h-80 place-items-center overflow-hidden rounded-xl border bg-slate-50">{selected.primary_image_url ? <img src={selected.primary_image_url} alt={`${selected.description} full preview`} className="max-h-[56vh] w-full object-contain" /> : <div className="text-sm text-slate-400">No verified image is available for this material.</div>}</div><div className="space-y-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Material description</p><p className="mt-1 text-base font-bold text-slate-900">{selected.description}</p></div><dl className="grid grid-cols-2 gap-x-4 gap-y-4 rounded-xl border bg-slate-50 p-4 text-xs"><div><dt className="text-slate-500">Material code</dt><dd className="mt-1 font-mono font-bold text-slate-800">{selected.material_code}</dd></div><div><dt className="text-slate-500">National material code</dt><dd className="mt-1 font-mono font-bold text-violet-700">{value(selected.national_code)}</dd></div><div><dt className="text-slate-500">CPSE</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.cpse_code)}</dd></div><div><dt className="text-slate-500">Mapping type</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.mapping_type)}</dd></div><div><dt className="text-slate-500">Category</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.category)}</dd></div><div><dt className="text-slate-500">Unit of measure</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.unit)}</dd></div><div><dt className="text-slate-500">Manufacturer</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.manufacturer)}</dd></div><div><dt className="text-slate-500">Model / part number</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.model)}</dd></div><div><dt className="text-slate-500">Record status</dt><dd className="mt-1 font-semibold text-slate-800">{value(selected.status)}</dd></div><div><dt className="text-slate-500">Visual similarity</dt><dd className="mt-1 font-semibold text-blue-700">{(selected.visual_similarity * 100).toFixed(1)}%</dd></div></dl>{selected.national_description && <div className="rounded-xl border border-violet-100 bg-violet-50 p-4 text-xs"><p className="font-semibold text-violet-900">National material description</p><p className="mt-1 text-violet-800">{selected.national_description}</p></div>}{Object.keys(selected.specifications || {}).length > 0 && <div className="rounded-xl border p-4 text-xs"><p className="font-semibold text-slate-800">Technical specifications</p><pre className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap font-sans text-slate-600">{JSON.stringify(selected.specifications, null, 2)}</pre></div>}</div></div>}
    </Modal>
  </div>;
};
