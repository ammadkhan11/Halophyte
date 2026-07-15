"""SQLite-backed, provenance-first graph store.

The tables intentionally mirror labelled nodes and edges so export to Neo4j is
straightforward, while keeping the final-year-project demo portable.
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .schema import ENTITY_TYPES, RELATION_TYPES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "halophyte_graph.sqlite"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


class GraphStore:
    def __init__(self, path: str | Path = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self.conn.close()

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY,
                external_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT,
                authors TEXT,
                year INTEGER,
                journal TEXT,
                doi TEXT,
                url TEXT,
                source_kind TEXT NOT NULL DEFAULT 'literature',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                node_type TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                external_id TEXT,
                attributes_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE(node_type, canonical_name)
            );
            CREATE TABLE IF NOT EXISTS aliases (
                alias_normalized TEXT NOT NULL,
                node_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                UNIQUE(alias_normalized, node_id)
            );
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY,
                source_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                target_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                relation_type TEXT NOT NULL,
                paper_id INTEGER REFERENCES papers(id) ON DELETE SET NULL,
                numeric_value REAL,
                unit TEXT,
                evidence_quote TEXT NOT NULL,
                confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                review_status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                UNIQUE(source_id, target_id, relation_type, paper_id, evidence_quote)
            );
            CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_edges_status ON edges(review_status);
            """
        )
        self.conn.commit()

    def upsert_paper(self, paper: dict[str, Any], source_kind: str = "literature") -> int:
        required = ["external_id", "title"]
        missing = [key for key in required if not paper.get(key)]
        if missing:
            raise ValueError(f"Paper missing required fields: {', '.join(missing)}")
        self.conn.execute(
            """INSERT INTO papers (external_id,title,abstract,authors,year,journal,doi,url,source_kind,created_at)
               VALUES (:external_id,:title,:abstract,:authors,:year,:journal,:doi,:url,:source_kind,:created_at)
               ON CONFLICT(external_id) DO UPDATE SET title=excluded.title, abstract=excluded.abstract,
               authors=excluded.authors, year=excluded.year, journal=excluded.journal, doi=excluded.doi, url=excluded.url""",
            {
                "external_id": paper["external_id"], "title": paper["title"],
                "abstract": paper.get("abstract", ""), "authors": paper.get("authors", ""),
                "year": paper.get("year"), "journal": paper.get("journal", ""),
                "doi": paper.get("doi"), "url": paper.get("url"), "source_kind": source_kind,
                "created_at": _now(),
            },
        )
        row = self.conn.execute("SELECT id FROM papers WHERE external_id=?", (paper["external_id"],)).fetchone()
        self.conn.commit()
        return int(row["id"])

    def upsert_node(self, node_type: str, name: str, aliases: Iterable[str] = (), attributes: dict[str, Any] | None = None) -> int:
        if node_type not in ENTITY_TYPES:
            raise ValueError(f"Unknown node type {node_type}")
        canonical = _normalise(name)
        self.conn.execute(
            """INSERT INTO nodes (node_type,canonical_name,display_name,attributes_json,created_at)
               VALUES (?,?,?,?,?) ON CONFLICT(node_type,canonical_name) DO UPDATE SET
               display_name=excluded.display_name, attributes_json=excluded.attributes_json""",
            (node_type, canonical, name.strip(), json.dumps(attributes or {}, sort_keys=True), _now()),
        )
        row = self.conn.execute("SELECT id FROM nodes WHERE node_type=? AND canonical_name=?", (node_type, canonical)).fetchone()
        node_id = int(row["id"])
        for alias in {name, *aliases}:
            if alias and alias.strip():
                self.conn.execute("INSERT OR IGNORE INTO aliases(alias_normalized,node_id) VALUES (?,?)", (_normalise(alias), node_id))
        self.conn.commit()
        return node_id

    def find_node(self, name: str, node_type: str | None = None) -> sqlite3.Row | None:
        sql = """SELECT n.* FROM nodes n LEFT JOIN aliases a ON a.node_id=n.id
                 WHERE (n.canonical_name=? OR a.alias_normalized=?)"""
        params: list[Any] = [_normalise(name), _normalise(name)]
        if node_type:
            sql += " AND n.node_type=?"
            params.append(node_type)
        return self.conn.execute(sql + " ORDER BY n.id LIMIT 1", params).fetchone()

    def add_edge(self, source_name: str, target_name: str, relation_type: str, paper_external_id: str | None,
                 evidence_quote: str, confidence: float, review_status: str = "pending", numeric_value: float | None = None,
                 unit: str | None = None) -> int:
        if relation_type not in RELATION_TYPES:
            raise ValueError(f"Unknown relation type {relation_type}")
        source = self.find_node(source_name)
        target = self.find_node(target_name)
        if not source or not target:
            raise ValueError(f"Both graph nodes must exist before linking: {source_name!r} → {target_name!r}")
        paper_id = None
        if paper_external_id:
            paper = self.conn.execute("SELECT id FROM papers WHERE external_id=?", (paper_external_id,)).fetchone()
            if not paper:
                raise ValueError(f"Unknown provenance record: {paper_external_id}")
            paper_id = int(paper["id"])
        self.conn.execute(
            """INSERT OR IGNORE INTO edges(source_id,target_id,relation_type,paper_id,numeric_value,unit,evidence_quote,confidence,review_status,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (source["id"], target["id"], relation_type, paper_id, numeric_value, unit, evidence_quote.strip(), confidence, review_status, _now()),
        )
        edge = self.conn.execute(
            "SELECT id FROM edges WHERE source_id=? AND target_id=? AND relation_type=? AND paper_id IS ? AND evidence_quote=?",
            (source["id"], target["id"], relation_type, paper_id, evidence_quote.strip()),
        ).fetchone()
        self.conn.commit()
        return int(edge["id"])

    def seed_demo(self, seed_path: str | Path | None = None) -> None:
        path = Path(seed_path or ROOT / "data" / "demo_seed.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        for paper in payload["papers"]:
            self.upsert_paper(paper, source_kind="demo_literature")
        for node in payload["nodes"]:
            self.upsert_node(node["type"], node["name"], node.get("aliases", []))
        for edge in payload["edges"]:
            self.add_edge(edge["source"], edge["target"], edge["type"], edge.get("paper"), edge["quote"],
                          float(edge["confidence"]), edge.get("status", "pending"))

    def import_phase1_csv(self, csv_path: str | Path) -> dict[str, int]:
        """Import the existing dictionary without assuming one exact export layout."""
        count = {"rows": 0, "species": 0, "mechanisms": 0, "thresholds": 0}
        dataset_id = "DATASET:PHASE1_GRASS_DICTIONARY"
        self.upsert_paper({"external_id": dataset_id, "title": "Phase 1 Grass Dictionary", "url": None,
                           "abstract": "Project dataset imported from the Halophyte Phase 1 dictionary."}, source_kind="project_dataset")
        with open(csv_path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                norm = {_normalise(k).replace("_", " "): (v or "").strip() for k, v in row.items() if k}
                species = next((norm.get(k) for k in ["scientific name", "species full name", "species", "grass species", "grass species common name", "common name"] if norm.get(k)), None)
                mechanism = norm.get("mechanism") or norm.get("salt tolerance mechanism")
                gr50 = next((norm.get(k) for k in ["gr50 avg ds m", "gr50 average", "gr50 avg", "gr50 mid", "gr50 (ds/m)", "gr50"] if norm.get(k)), None)
                if not species:
                    continue
                count["rows"] += 1
                self.upsert_node("Species", species)
                count["species"] += 1
                if mechanism:
                    self.upsert_node("Mechanism", mechanism)
                    self.add_edge(species, mechanism, "HAS_MECHANISM", dataset_id, "Imported from Phase 1 Grass Dictionary.", 1.0, "dataset_import")
                    count["mechanisms"] += 1
                if gr50:
                    match = re.search(r"\d+(?:\.\d+)?", gr50)
                    if match:
                        value = float(match.group())
                        label = f"GR50 {value:g} dS/m"
                        self.upsert_node("SalinityThreshold", label, attributes={"metric": "GR50", "value": value, "unit": "dS/m"})
                        self.add_edge(species, label, "TOLERATES_UP_TO", dataset_id, "Imported GR50 value from Phase 1 Grass Dictionary.", 1.0, "dataset_import", value, "dS/m")
                        count["thresholds"] += 1
        return count

    def papers_without_extraction(self, limit: int = 100) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT p.* FROM papers p WHERE p.source_kind='literature' AND NOT EXISTS
               (SELECT 1 FROM edges e WHERE e.paper_id=p.id) ORDER BY p.year DESC LIMIT ?""", (limit,)
        ).fetchall()

    def dashboard_counts(self) -> dict[str, int]:
        return {
            "papers": int(self.conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]),
            "nodes": int(self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]),
            "edges": int(self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]),
            "pending": int(self.conn.execute("SELECT COUNT(*) FROM edges WHERE review_status IN ('pending','needs_source_review')").fetchone()[0]),
        }

    def search(self, query: str = "", node_type: str | None = None) -> list[sqlite3.Row]:
        sql = "SELECT * FROM nodes WHERE 1=1"
        params: list[Any] = []
        if query:
            sql += " AND (display_name LIKE ? OR canonical_name LIKE ?)"
            params.extend([f"%{query}%", f"%{_normalise(query)}%"])
        if node_type and node_type != "All":
            sql += " AND node_type=?"
            params.append(node_type)
        return self.conn.execute(sql + " ORDER BY node_type, display_name", params).fetchall()

    def node_details(self, node_id: int) -> tuple[sqlite3.Row, list[sqlite3.Row]]:
        node = self.conn.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
        edges = self.conn.execute(
            """SELECT e.*, s.display_name AS source_name, t.display_name AS target_name,
                      p.title AS paper_title, p.url AS paper_url, p.external_id AS paper_external_id
               FROM edges e JOIN nodes s ON s.id=e.source_id JOIN nodes t ON t.id=e.target_id
               LEFT JOIN papers p ON p.id=e.paper_id WHERE e.source_id=? OR e.target_id=?
               ORDER BY e.review_status, e.confidence DESC""", (node_id, node_id),
        ).fetchall()
        return node, edges

    def graph_edges(self, status: str | None = None) -> list[sqlite3.Row]:
        sql = """SELECT e.*, s.display_name AS source_name, s.node_type AS source_type,
                        t.display_name AS target_name, t.node_type AS target_type, p.external_id AS paper_external_id
                 FROM edges e JOIN nodes s ON s.id=e.source_id JOIN nodes t ON t.id=e.target_id
                 LEFT JOIN papers p ON p.id=e.paper_id"""
        if status:
            sql += " WHERE e.review_status=?"
            return self.conn.execute(sql + " ORDER BY e.id", (status,)).fetchall()
        return self.conn.execute(sql + " ORDER BY e.id").fetchall()

    def set_review_status(self, edge_id: int, status: str) -> None:
        if status not in {"approved", "rejected", "pending", "demo_reviewed", "needs_source_review", "dataset_import"}:
            raise ValueError("Invalid review status")
        self.conn.execute("UPDATE edges SET review_status=? WHERE id=?", (status, edge_id))
        self.conn.commit()
