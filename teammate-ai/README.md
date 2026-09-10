# SIH — National Material Master: AI Matching Module

This is your slice of the SIH 2026 project: the AI layer that normalizes
material descriptions, extracts technical attributes, and scores whether
two CPSE material records are the same / near-duplicate / functionally
equivalent / different.

## 1. Open in VS Code
```bash
code .
```
(run this from inside the `sih-ai-matcher` folder)

## 2. Create + activate a virtual environment
In the VS Code terminal (Ctrl + `):
```bash
python -m venv venv
```
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

When VS Code prompts **"Select this environment for the workspace?"** click **Yes**.

## 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 4. Verify the environment
```bash
python test_setup.py
```
You should see semantic similarity scores above ~0.85 between the 4 sample
bolt descriptions, a FAISS top-k result, and RapidFuzz scores. If this
fails, fix the environment before moving on.

## 5. Generate the synthetic dataset
```bash
python data/make_dataset.py
```
This creates:
- `data/synthetic_materials.csv` — fake CPSE material records (bolts, nuts, washers)
- `data/ground_truth_pairs.csv` — labelled pairs (1=same, 2=functional equivalent, 0=different)

Use `ground_truth_pairs.csv` later to compute precision/recall/F1 for your matcher —
this is what turns "the AI works" into a number you can show judges.

## Folder structure
```
sih-ai-matcher/
├── venv/                          (created by you, gitignored)
├── requirements.txt
├── test_setup.py                  environment sanity check
├── data/
│   ├── make_dataset.py            synthetic dataset generator
│   ├── synthetic_materials.csv    (generated)
│   └── ground_truth_pairs.csv     (generated)
├── src/
│   ├── normalize.py               ⏳ next to build
│   ├── extract_attributes.py      ⏳ next to build
│   ├── fuzzy_score.py             ⏳ next to build
│   ├── embed_and_retrieve.py      ⏳ next to build
│   └── scorer.py                  ⏳ next to build
└── tests/
    └── eval_against_ground_truth.py   ⏳ next to build
```

## Build order (what to ask for next, one at a time)
1. `src/normalize.py` — clean text, expand abbreviations
2. `src/extract_attributes.py` — regex-based attribute extraction (diameter, length, material...)
3. `src/fuzzy_score.py` — RapidFuzz wrapper
4. `src/embed_and_retrieve.py` — embeddings + FAISS index/search, wrapped as functions
5. `src/scorer.py` — combines all signals into final score + label (Exact/Near-Dup/Functional-Equiv/No-Match)
6. `tests/eval_against_ground_truth.py` — runs the scorer over `ground_truth_pairs.csv`, prints precision/recall/F1

## Output contract for your teammates
Your matcher should expose one function that returns JSON like:
```json
{
  "match_score": 0.958,
  "label": "Exact",
  "components": {"semantic": 0.94, "attribute": 1.00, "fuzzy": 0.91},
  "extracted_attributes": {"type": "bolt", "head": "hexagonal", "diameter": "M16", "length": "50mm", "material": "SS304"},
  "explanation": "Matched on identical size (M16x50) and material (SS304); wording differs (hex vs hexagonal)."
}
```
Agree on this shape with your backend teammate before you're both deep into code.
