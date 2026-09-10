# Governance and National Material Code Policy

## National code format

New codes use `NMC-{category}-{subcategory}-{sequence}-{check-digit}`. Category and
subcategory segments come from the controlled taxonomy in
`classification_service.py`; the database sequence provides concurrency-safe identity;
the final digit detects common transcription errors. Issued codes are immutable.

Scheme version 2 calculates the check digit from the complete normalized body before
the final hyphen: `NMC-{CATEGORY}-{SUBCATEGORY}-{SEQUENCE}`. Letters are uppercase,
category and subcategory use their controlled three-letter codes, and the sequence
is a six-digit, zero-padded decimal identifier. The permitted body alphabet is ASCII
`A-Z`, `0-9`, and `-`. Convert every character, including each separator, to its
three-digit, zero-padded Unicode code point in base 10 (`-` becomes `045`), concatenate
those digits, and process them from left to right. Start with interim state 0; for each
input digit use the current state as the row and the digit as the column in this Damm
table. The final state is the check digit.

| State | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 3 | 1 | 7 | 5 | 9 | 8 | 6 | 4 | 2 |
| 1 | 7 | 0 | 9 | 2 | 1 | 5 | 4 | 8 | 6 | 3 |
| 2 | 4 | 2 | 0 | 6 | 8 | 7 | 1 | 3 | 5 | 9 |
| 3 | 1 | 7 | 5 | 0 | 9 | 8 | 3 | 4 | 2 | 6 |
| 4 | 6 | 1 | 2 | 3 | 0 | 4 | 5 | 9 | 7 | 8 |
| 5 | 3 | 6 | 7 | 4 | 2 | 0 | 9 | 5 | 8 | 1 |
| 6 | 5 | 8 | 6 | 9 | 7 | 2 | 0 | 1 | 3 | 4 |
| 7 | 8 | 9 | 4 | 5 | 3 | 6 | 2 | 0 | 1 | 7 |
| 8 | 9 | 4 | 3 | 8 | 6 | 1 | 7 | 2 | 0 | 5 |
| 9 | 2 | 5 | 8 | 1 | 4 | 3 | 6 | 7 | 9 | 0 |

Authoritative scheme-v2 vectors are `NMC-FST-BLT-000001-4`,
`NMC-VLV-GTV-000042-6`, and `NMC-GEN-GEN-999999-0`.

The code text deliberately remains stable. Validators must find the exact code in the
National Material registry and select the algorithm from `code_scheme_version`; an
unknown or unregistered code is invalid and has no fallback. Version 1 validation uses
the legacy rule: sum each body's Unicode code point multiplied by its one-based
position, modulo 10. Existing version-1 codes retain that digit and remain immutable;
all newly issued codes are recorded as version 2.

## Canonical conflict policy

Complete structured records are preferred when proposing canonical data. Differences
in grade, pressure/rating, voltage, size, diameter, or length are safety-critical and
must be explicitly resolved in the reviewer workspace. Original CPSE values remain in
NationalMaterial provenance and the approval audit event.

## Audit policy

Material, inventory, demand, import, integration, national registry, mapping, approval,
request, CPSE, and role mutations create append-only audit events. Update events capture
before/after values. Audit APIs expose filters but no mutation endpoints.

## ERP wording

The MOCK connector is a simulation. The ODATA connector is the production integration
path and requires an explicit endpoint and credential. Demonstrations must state which
connector was active.
