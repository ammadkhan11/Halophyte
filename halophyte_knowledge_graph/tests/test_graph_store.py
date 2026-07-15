import tempfile
import unittest
from pathlib import Path

from src.analysis import research_opportunities
from src.extraction import validate_and_ingest
from src.graph_store import GraphStore


class GraphStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = GraphStore(Path(self.temp.name) / "graph.sqlite")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_seed_has_provenance(self):
        self.store.seed_demo()
        counts = self.store.dashboard_counts()
        self.assertGreaterEqual(counts["papers"], 2)
        self.assertGreaterEqual(counts["edges"], 3)
        for edge in self.store.graph_edges():
            self.assertTrue(edge["evidence_quote"])

    def test_rejects_quote_absent_from_abstract(self):
        self.store.upsert_paper({"external_id": "PMID:TEST", "title": "Test", "abstract": "Only a literal grounded statement."})
        extraction = {"entities": [{"name": "Suaeda salsa", "canonical_name": "Suaeda salsa", "type": "Species"}, {"name": "NHX", "canonical_name": "NHX", "type": "Gene"}],
                      "relations": [{"source": "Suaeda salsa", "target": "NHX", "type": "EXPRESSES_GENE", "value": None, "unit": None, "evidence_quote": "invented relationship", "confidence": 0.95}]}
        result = validate_and_ingest(self.store, "PMID:TEST", extraction)
        self.assertEqual(result["accepted"], 0)
        self.assertEqual(result["rejected"], 1)

    def test_opportunities_are_transparent(self):
        self.store.seed_demo()
        results = research_opportunities(self.store)
        self.assertTrue(results)
        self.assertTrue(all("next_step" in item for item in results))


if __name__ == "__main__":
    unittest.main()
