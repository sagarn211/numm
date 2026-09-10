# Framework implementation status — 10 September 2026

This is an engineering implementation record, not a claim of production certification.

## Implemented in this change

- Structured attributes contribute to retrieval and pair scoring. Explicit structured conflicts override text similarity; missing one-sided critical evidence prevents exact classification.
- Engineering unit normalization for common voltage, power, length, and pressure units; grade aliases and explicit description extraction on the backend.
- Functional-equivalent approval stores a separate substitution recommendation and conditions. It does not merge material identities or authorize automatic stock substitution.
- All mapping writes validate incoming evidence against the national record and existing members. Unresolved conflicts cannot be bypassed by an acknowledgement boolean.
- Automatic approval requires a supported category schema and complete technical attributes, including explicitly extracted description evidence.
- Canonical creation reuses identical normalized content and serializes equal-content creation on PostgreSQL. This is conservative content reuse, not proof of semantic identity.
- Lighting, switchgear, cable accessories, seals, and transmission category rules; persisted taxonomy migration.
- Versioned starting attribute schemas and a Data Quality list of missing evidence.
- SAP synchronization updates existing material records and audits before/after state. Incompatible mapped changes fail the transaction for review; manual classifications are retained.
- OData continuation requests are confined to the configured origin; mock array responses are supported.
- Procurement-history CSV preview/confirmation and analytics by identity/month/unit/currency, supplier participation, and lead times; dedicated UI and Import Data link.
- Bulk mapping migration preview/apply with expected-current checks; per-material mapping history and guarded latest-change restoration.
- Pending exact/near-duplicate risk excludes rejected, resolved and functional-equivalent recommendations.
- Current-month stock/demand balances are grouped by identity and unit. The dashboard does not present surplus valuation as verified savings.
- Completed stock imports are idempotent; row locks protect updates, reservations cannot be released through imports, and omitted costs are retained.
- Stock allocation rejects incompatible units. Demand entry validates CPSE ownership, base unit, period presence, and finite non-negative quantities.
- National registry retrieval loads beyond the old first 100 records.

## Validation

- Backend: isolated SQLite regression suite covering identity guards, substitution separation, canonical reuse, SAP updates, procurement validation, stock retries and period-specific balances.
- AI: local model tests plus structured-evidence guard tests.
- Frontend: ESLint and production build.
- No production material mappings or stock quantities were rewritten to test these changes.

## Still required — do not mark these complete

1. Category schemas and substitution rules need CPSE engineering sign-off. Existing schemas and extraction rules cover a bounded vocabulary, not all five sectors.
2. Learned classification, domain-specific reranking and confidence calibration need real labelled CPSE records and held-out benchmarks. They are not implemented by expanding the rule table.
3. Full incremental/persistent vector indexing and national-scale load tests remain outstanding. Existing batch retrieval still rebuilds an index.
4. Complete migration lifecycle (retirement/supersession, graph-wide merge/split, downstream ERP cutover and restore) remains broader than mapping migration/restore.
5. Audit events remain ordinary database records. Tamper-evident chaining/external retention and a comprehensive versioned master-record workflow are not yet implemented.
6. Live SAP adapters need each CPSE's API metadata, authentication arrangement, deletion semantics, reconciliation dataset and acceptance tests. The current generic OData contract is not universal SAP support.
7. Procurement imports currently support CSV and existing materials; purchase-history signals do not yet feed identity scoring. Procurement planning, forecasting, supplier selection and joint sourcing execution are not complete.
8. Existing functional-equivalent identity merges were not automatically split; historical mappings need a reviewed migration plan.
9. Existing reviewed matching decisions are preserved. A complete invalidation/re-review policy after source updates is still required.
10. The batch-level procurement audit is not a per-row versioned procurement ledger. Inventory currency metadata and operational stock-movement accounting remain to be designed.
11. CodeRabbit review requires authentication (`coderabbit auth login`); no external review was completed in this change.

## Use

- Import Data → Procurement history: upload UTF-8 CSV using the documented columns, preview and confirm; analytics are available at `/procurement-history`.
- National Materials → mapping details → Mapping history: view events and restore the latest compatible previous mapping with a reason.
- Data Quality: inspect the first 100 materials lacking technical evidence or a supported category schema.
- API docs expose `/api/mapping-history/migration` for bulk preview/apply; submit the expected current national ID for every row.

Required deployment: migration `20260910_04`, backend, import worker, frontend and AI service rebuilds.
