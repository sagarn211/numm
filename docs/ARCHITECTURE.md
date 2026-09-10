# NUMM Architecture

```text
React Frontend :5173
        |
        v
Main FastAPI Backend :8000
   |          |           |
   v          v           v
PostgreSQL   AI :8001   Mock SAP :8002
```

## Main backend responsibilities

- authentication
- CPSE master
- material master
- CSV/XLSX imports
- data cleaning and validation
- AI orchestration
- reviewer approval
- national material registry
- cross-CPSE inventory
- material requests and allocation
- audit
- demand aggregation
- ERP/SAP integration
- exports

## AI service responsibilities

- matching-specific normalization
- attribute extraction
- embeddings
- FAISS candidate retrieval
- fuzzy similarity
- hybrid score
- engineering rules
- explanation
- model/matcher version

## Human-in-the-loop rule

AI recommends. Human reviewer makes the final harmonization decision.

`FUNCTIONAL_EQUIVALENT` must never be automatically mapped without review.

Safety-critical canonical conflicts (grade, pressure, voltage and dimensions) block
approval until a reviewer selects the authoritative value. Imports are queued and
processed in bounded chunks with parallel normalization/classification, progress,
idempotency, exponential retry, and durable dead-letter records. Candidate retrieval
uses a fingerprinted persistent HNSW index. ERP integration uses a connector boundary:
MOCK for demonstrations and ODATA for configured SAP systems. OData supports OAuth,
optional mTLS, throttling, delta pagination, health checks, and reconciliation.
