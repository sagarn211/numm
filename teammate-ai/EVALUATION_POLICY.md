# ALADIN AI Evaluation Policy

Accuracy statements must include the dataset size and scope. The current result may be described as
"accuracy on the current 139-pair labelled evaluation set" and must not be presented as universal accuracy.

Every release evaluation records dataset hashes, UTC timestamp, per-class precision/recall/F1,
confusion matrix, and misclassified examples. The final benchmark should add held-out CPSE records,
hard negatives, missing attributes, unit conversions, OCR/spelling noise, and multilingual descriptions.
These cases are maintained in `data/challenge_pairs.csv` and are always assigned to
the held-out test partition. The project does not train MiniLM on this dataset;
threshold tuning and held-out test results are reported separately. CI publishes the
versioned JSON result as the `ai-evaluation-report` build artifact.

Run:

```bash
python tests/eval_against_ground_truth.py --output evaluation-report.json
```
