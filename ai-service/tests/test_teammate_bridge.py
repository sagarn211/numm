import unittest

from src.teammate_bridge import engine_health, match_batch, match_pair, runtime_evidence


def material(material_id, description):
    return {
        "id": material_id,
        "description": description,
        "cleaned_description": description,
        "category": "FASTENER",
        "specifications": {},
    }


class TeammateBridgeTests(unittest.TestCase):
    def assert_real_result(self, result, label):
        self.assertIsNotNone(result)
        self.assertEqual(result["label"], label)
        self.assertEqual(result["model"], "all-MiniLM-L6-v2")
        self.assertTrue(all(0.0 <= result["components"][key] <= 1.0 for key in ("semantic", "attribute", "fuzzy")))
        self.assertTrue(0.0 <= result["match_score"] <= 1.0)

    def test_real_engine_health_and_pair_guardrails(self):
        self.assertEqual(engine_health()["engine"], "TEAMMATE_REAL")
        source = material(1001, "HEX BOLT M16X50 SS304")
        self.assert_real_result(
            match_pair(source, material(1002, "BOLT HEXAGONAL M16 X 50 STAINLESS STEEL 304")),
            "EXACT",
        )
        self.assert_real_result(match_pair(source, material(1003, "HEX NUT M16 SS304")), "NO_MATCH")
        self.assert_real_result(match_pair(source, material(1004, "HEX BOLT M20X75 SS304")), "NO_MATCH")
        self.assert_real_result(match_pair(source, material(1005, "HEX BOLT M16X50 MILD STEEL")), "FUNCTIONAL_EQUIVALENT")

    def test_batch_uses_faiss_and_returns_canonical_unique_pairs(self):
        results = match_batch([
            material(2001, "HEX BOLT M16X50 SS304"),
            material(2002, "BOLT HEXAGONAL M16 X 50 STAINLESS STEEL 304"),
            material(2003, "HEX BOLT M20X75 SS304"),
        ])
        self.assertTrue(results)
        pairs = [(result["material_a_id"], result["material_b_id"]) for result in results]
        self.assertEqual(pairs, list(dict.fromkeys(pairs)))
        self.assertTrue(all(left < right for left, right in pairs))
        evidence = runtime_evidence()
        self.assertEqual(evidence["embedding_dimension"], 384)
        self.assertEqual(evidence["faiss_vectors_indexed"], 3)
        self.assertTrue(evidence["last_faiss_top_k"])

    def test_focused_batch_queries_only_imported_materials(self):
        results = match_batch([
            material(3001, "HEX BOLT M16X50 SS304"),
            material(3002, "BOLT HEXAGONAL M16 X 50 STAINLESS STEEL 304"),
            material(3003, "HEX BOLT M16X50 MILD STEEL"),
        ], {3001})
        self.assertTrue(all(3001 in (row["material_a_id"], row["material_b_id"]) for row in results))
        self.assertEqual(len(runtime_evidence()["last_faiss_top_k"]), 1)


if __name__ == "__main__":
    unittest.main()
