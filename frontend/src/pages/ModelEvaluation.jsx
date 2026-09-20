import { useEffect, useState } from "react";
import { FlaskConical } from "lucide-react";
import { matchingApi } from "../services/matchingApi";
import { Loading } from "../components/common/Loading";

const percent = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;

export const ModelEvaluation = () => {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    matchingApi
      .getEvaluation()
      .then((response) => {
        if (active) setReport(response.data);
      })
      .catch((err) => {
        if (active)
          setError(
            err?.response?.data?.detail ||
              err.message ||
              "No executed evaluation artifact is available.",
          );
      });
    return () => {
      active = false;
    };
  }, []);
  if (!report && !error)
    return (
      <Loading type="ai" text="Loading measured teammate-AI evaluation..." />
    );
  if (error)
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {error}
      </div>
    );
  const classes = Object.keys(report.per_class || {});
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2">
          <FlaskConical className="h-5 w-5 text-violet-700" />
          <h2 className="text-xl font-bold">AI Model Evaluation</h2>
        </div>
        <p className="text-xs text-slate-500">
          Measured controlled-dataset results; these are not industrial
          production-accuracy claims.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <div className="rounded-xl border bg-white p-4">
          <span className="text-xs text-slate-500">Accuracy</span>
          <p className="text-2xl font-bold">{percent(report.accuracy)}</p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <span className="text-xs text-slate-500">Evaluated pairs</span>
          <p className="text-2xl font-bold">
            {report.ground_truth_pairs + report.held_out_challenge_pairs}
          </p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <span className="text-xs text-slate-500">
            Identity false positives
          </span>
          <p className="text-2xl font-bold">
            {percent(report.identity_merge_error_rates?.false_positive_rate)}
          </p>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <span className="text-xs text-slate-500">
            Identity false negatives
          </span>
          <p className="text-2xl font-bold">
            {percent(report.identity_merge_error_rates?.false_negative_rate)}
          </p>
        </div>
      </div>
      <section className="rounded-xl border bg-white p-4">
        <h3 className="text-sm font-bold">Executed engine configuration</h3>
        <p className="mt-2 text-xs">
          Model: {report.model?.name} · Version: {report.model?.version} ·
          Matcher: {report.model?.matcher_version}
        </p>
        <p className="text-xs">
          Weights: semantic {report.weights.semantic}, attributes{" "}
          {report.weights.attribute}, fuzzy {report.weights.fuzzy}
        </p>
        <p className="mt-2 text-[11px] text-slate-500">{report.claim_scope}</p>
        <p className="text-[11px] text-slate-500">
          Executed {report.evaluation_timestamp}
        </p>
      </section>
      <section className="overflow-auto rounded-xl border bg-white p-4">
        <h3 className="mb-3 text-sm font-bold">Per-class metrics</h3>
        <table className="w-full text-left text-xs">
          <thead>
            <tr>
              <th>Class</th>
              <th>Precision</th>
              <th>Recall</th>
              <th>F1</th>
              <th>Support</th>
            </tr>
          </thead>
          <tbody>
            {classes.map((name) => (
              <tr key={name} className="border-t">
                <td className="py-2 font-semibold">{name}</td>
                <td>{percent(report.per_class[name].precision)}</td>
                <td>{percent(report.per_class[name].recall)}</td>
                <td>{percent(report.per_class[name].f1)}</td>
                <td>{report.per_class[name].support}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="overflow-auto rounded-xl border bg-white p-4">
        <h3 className="mb-3 text-sm font-bold">
          Confusion matrix (true rows → predicted columns)
        </h3>
        <table className="w-full text-center text-xs">
          <thead>
            <tr>
              <th></th>
              {classes.map((name) => (
                <th key={name}>{name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {classes.map((actual) => (
              <tr key={actual} className="border-t">
                <th className="py-2 text-left">{actual}</th>
                {classes.map((predicted) => (
                  <td key={predicted}>
                    {report.confusion_matrix[actual]?.[predicted] ?? 0}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900">
        <strong>Known limitation:</strong> The checked-in ground truth is
        synthetic and small. Results establish reproducibility on these labelled
        pairs only; CPSE engineering validation and a larger held-out real
        dataset remain required.
      </section>
    </div>
  );
};
