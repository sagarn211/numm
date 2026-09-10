# SIH AI Matcher — Everything You Built, In Plain Words

A cheat sheet of every concept, tool, and function you used — for revising
before the demo, or explaining your work to judges/teammates.

---

## 1. The Big Idea (one sentence)

You built a program that reads two messy, differently-worded material
descriptions and decides: **are these the same thing, a close variant,
or genuinely different?** — and it explains *why* it decided that.

---

## 2. Key Concepts (in plain words)

### Normalization
Cleaning up messy text so different spellings of the same thing look
the same. Example: `"Hex Bolt"` and `"Hexagonal Bolt"` both become
`"HEXAGONAL BOLT"`. Think of it like spell-check, but for making
things *consistent*, not just correct.

### Embedding
A way of turning a sentence into a list of numbers (a "vector") that
captures its *meaning*. Two sentences that mean similar things end up
with similar numbers, even if the words are totally different.
Think of it like a GPS coordinate for meaning — sentences with close
"meaning coordinates" are talking about the same thing.

### Semantic Similarity
How close two pieces of text are in *meaning* (using embeddings).
Score from 0 (totally different) to 1 (identical meaning).

### Cosine Similarity
The math formula used to measure how "close" two embeddings are.
It looks at the *angle* between two number-vectors, not their size.
You don't need to know the math — just know it's what "semantic
similarity" is calculated with.

### Fuzzy Matching
Comparing two pieces of text *by spelling*, not meaning. Counts how
many letters would need to change to turn one string into the other.
Catches typos and small differences that meaning-based matching
might miss (like `M16` vs `M18` — one digit, but a real difference).

### Attribute Extraction
Pulling structured facts out of messy text. Turns
`"HEX BOLT M16 X 50 MM SS304"` into a clean table:
`type=bolt, diameter=M16, length=50mm, grade=SS304`.
This is what lets you compare "is the diameter *actually* the same?"
instead of just "does the text *look* similar?"

### Regex (Regular Expressions)
A mini-language for finding patterns in text, like "find a number
followed by the letters MM." Used to pull out diameters, lengths,
etc. Not AI — just precise pattern-matching rules you write yourself.

### Vector Search / FAISS
Finding the "closest matches" to something out of a huge pile of
options, fast — without comparing it against every single one.
Imagine looking up a word in a dictionary (jump straight to the
right page) instead of reading every page from the start.

### Hybrid Scoring
Combining multiple signals (semantic + attribute + fuzzy) into one
final confidence score, instead of trusting just one method. You
used: `40% semantic + 40% attribute... ` — later tuned to
`25% semantic + 55% attribute + 20% fuzzy` after testing showed
attribute-matching was more trustworthy for this domain.

### Ground Truth / Labelled Data
A dataset where you (the human) already know the correct answer —
used to check if your AI is actually right, not just "seems right."
Your `ground_truth_pairs.csv` says which material pairs are
genuinely the same/different/functionally equivalent.

### Precision, Recall, F1 (the accuracy report card)
- **Precision**: when your system SAYS "these match," how often is it
  actually right? (Are you crying wolf too much?)
- **Recall**: out of all the TRUE matches that exist, how many did
  your system actually catch? (Are you missing real matches?)
- **F1**: a single score that balances precision and recall together.
- You measured all three for every category (Exact, Functional-
  Equivalent, No-Match) using `eval_against_ground_truth.py`.

### Domain Rules (a.k.a. business rules / hard rules)
Explicit "if this, then that" logic layered on top of the AI score,
based on real-world knowledge. Example: *"if the material TYPE
differs (nut vs bolt), it's automatically a No-Match — no AI score
should override that."* You added 3 of these after testing revealed
the pure math-based score alone made mistakes.

### venv (Virtual Environment)
An isolated, self-contained folder holding a specific set of Python
libraries just for this project — so it doesn't clash with other
projects on your computer. Safe to delete anytime; just reinstall.

---

## The Actual AI Model You Used: `all-MiniLM-L6-v2`

This is the real model doing the "semantic similarity" work in
`embed_and_retrieve.py`.

**What it is**: A *sentence embedding model* — its only job is to read
a sentence and output 384 numbers representing what that sentence
*means*. Built on a smaller, faster version of a "transformer" (the
same underlying architecture behind models like ChatGPT, just much
smaller and specialized for one narrow task).

**Where it's from**: Made by the Sentence-Transformers research team,
hosted publicly on Hugging Face (think of it like a public library/
app-store for AI models, similar to how GitHub hosts code). Official
page: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

**Why this specific model (not something bigger/fancier)**:

| Reason | Why it mattered here |
|---|---|
| Small (~90MB) | Downloads fast, low disk usage |
| Fast, CPU-only | Runs fine on a normal laptop, no GPU needed |
| "MiniLM" | A compressed/distilled model — keeps most accuracy while being much smaller |
| "L6" | 6 transformer layers (bigger models have 12, 24+) — fewer layers = faster |
| Good enough accuracy | Works well for a well-scoped domain like fastener descriptions |
| Offline after first download | Downloads once, then runs with no internet — good for live demos |

**What "384 numbers" means**: Every sentence becomes a list (vector) of
384 numbers — its "embedding dimension." Similar-meaning sentences get
vectors pointing in a similar direction. You never touch these numbers
directly — `sentence-transformers` + cosine similarity handle the
comparison math.

**One honest limitation** (worth mentioning if judges ask): it's a
general-purpose model, not trained specifically on engineering/
industrial terminology. That's exactly why it was "too forgiving" of
real differences like `SS304` vs `MS` or `M16` vs `M20` (both just look
like similar short technical codes to it) — which is *why* you built
the attribute-extraction + domain-rules layer on top instead of
trusting the model alone. A deliberate design decision, not a flaw.

---

## 3. Libraries You Used (and what each one is for)

| Library | Plain-word explanation |
|---|---|
| **sentence-transformers** | Turns text into embeddings (meaning-vectors) |
| **faiss-cpu** | Fast search through many embeddings at once |
| **rapidfuzz** | Fuzzy (spelling-based) text comparison |
| **numpy** | Handles the number-arrays behind embeddings |
| **pandas** / **openpyxl** | Reading/writing spreadsheets and CSVs (installed, not directly used yet in your code) |
| **scikit-learn** | Installed for future ML evaluation tools |
| **re** (built into Python) | Pattern-matching in text (regex) |
| **csv** (built into Python) | Reading/writing CSV files |
| **fastapi** / **uvicorn** | (Installed, not built yet) Turns your Python function into a web API others can call |

---

## 4. The Files You Built, and What Each One Does

| File | In one sentence |
|---|---|
| `data/make_dataset.py` | Generates fake CPSE material records + the "answer key" (ground truth) for testing |
| `src/normalize.py` | Cleans and standardizes messy text |
| `src/extract_attributes.py` | Pulls structured fields (type, size, grade) out of text |
| `src/fuzzy_score.py` | Scores spelling-level similarity between two texts |
| `src/embed_and_retrieve.py` | Scores meaning-level similarity + finds top matches fast |
| `src/scorer.py` | Combines everything into one final score, label, and explanation |
| `tests/eval_against_ground_truth.py` | Measures how accurate your matcher actually is |

---

## 5. The Key Function You'll Demo

```python
match_materials(description_a, description_b)
```
This is the ONE function that does everything. Feed it two raw material
descriptions, it returns:
```json
{
  "match_score": 0.958,
  "label": "Exact",
  "components": {"semantic": 0.94, "attribute": 1.0, "fuzzy": 0.91},
  "attributes_a": {...},
  "attributes_b": {...},
  "explanation": "Matched on material type, diameter, length..."
}
```

---

## 6. Your Actual Results (know these numbers!)

**Final accuracy: 100%** (139/139 test pairs correctly labelled)

### The full iteration story — how you actually got there

This is the part worth explaining to judges in detail, since it shows
real debugging, not luck.

**Round 1 — First working version — ~54% accuracy**
- Used the blueprint's suggested weights: `40% semantic + 40% attribute + 20% fuzzy`
- Problem found: the `functional_equivalent` class had only **3.5%
  precision** — almost everything the AI called "functional
  equivalent" was actually wrong
- Root cause: a **nut** vs. a **bolt** scored 0.688 and got labelled
  "Functional-Equivalent" — but a nut and a bolt are completely
  different parts, not similar items with minor differences
- Why it happened: general-purpose semantic embeddings don't
  distinguish engineering categories well — "Hexagonal Nut M16" and
  "Hexagonal Bolt M20" *sound* similar in everyday English, even
  though they're not interchangeable at all

**Round 2 — Added Rule 1 + reweighted — 86.3% accuracy**
- **Change 1**: shifted weights toward attribute-matching, since it
  proved more reliable than raw semantic similarity:
  `25% semantic + 55% attribute + 20% fuzzy`
- **Change 2**: added a hard rule — *if the extracted `material_type`
  differs (nut vs bolt vs carriage_bolt), immediately label
  "No-Match," skip the weighted formula entirely.* A categorical
  difference like this should never be softened by a similarity score.
- Result: `different` class jumped to 100% precision / 93.5% recall
- Remaining problem: pairs like `SS304 bolt` vs `Mild Steel bolt`
  (same size, same type, only the material grade differs) were still
  scoring high enough to be called "same" instead of "functionally
  equivalent" — because near-identical wording pushed the score above
  the Near-Duplicate threshold

**Round 3 — Added Rule 2 — 95.7% accuracy**
- **Change**: added a second rule — *if type matches AND diameter
  matches AND length matches, but material grade differs, force the
  label to "Functional-Equivalent" directly* — instead of hoping a
  numeric threshold happened to land in the right place
- This directly encodes what "functional equivalent" was actually
  *defined* as in the synthetic dataset: same physical part,
  different material
- Remaining problem: pairs like `M16x50 SS304` vs `M20x75 SS304`
  (different diameter AND length, same type, same grade) were now
  incorrectly landing in "Functional-Equivalent" — a wrong-sized bolt
  isn't a valid substitute no matter the material

**Round 4 — Added Rule 3 — 100% accuracy**
- **Change**: added a third rule, checked *before* the grade rule —
  *if diameter or length genuinely differ (both present, same type),
  force "No-Match," regardless of material grade.* Physical size
  incompatibility is a harder disqualifier than a grade difference.
- Result: all 139/139 ground-truth pairs correctly classified

### Why this progression matters for your demo
You didn't guess at magic threshold numbers — every change was a
direct response to a specific, named failure the evaluation script
found (nut vs bolt, grade-only difference, size-only difference).
That's the actual engineering story: **build → measure → find the
specific failure → fix it with an explainable rule → re-measure.**
Telling judges "we started at 54%, found *this specific bug*, fixed
it, found the *next* bug, fixed that too, and ended at 100%" is far
more convincing than just stating the final number cold.

### The 3 domain rules, summarized

| Priority | Rule | Result |
|---|---|---|
| 1st (checked first) | Different material TYPE (nut vs bolt) | Forced **No-Match** |
| 2nd | Different physical SIZE (diameter/length), same type | Forced **No-Match** |
| 3rd | Same type + same size, different material GRADE | Forced **Functional-Equivalent** |
| (fallback) | None of the above apply | Use the weighted formula (25% semantic + 55% attribute + 20% fuzzy) → label by score thresholds |



---

## 7. The 4 Possible Labels Your System Outputs

| Label | Meaning |
|---|---|
| **Exact** | Same material, just worded differently |
| **Near-Duplicate** | Very likely the same, minor uncertainty |
| **Functional-Equivalent** | Interchangeable in fit, but not identical (e.g. different material grade) |
| **No-Match** | Genuinely different materials |

---

## 8. What's Left To Build

- Wrap `match_materials()` in a **FastAPI** endpoint so your teammate's
  frontend/backend can call it over the web
- (Optional) Add more material families beyond fasteners (valves, cables)
- Push updates to GitHub as you go