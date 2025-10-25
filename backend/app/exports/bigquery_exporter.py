"""
BigQuery Exporter (optional)
============================

Optionales Modul zum Exportieren großer Datensätze (Transactions, Graph) nach Google BigQuery.
Aktivierung über ENV: ENABLE_BIGQUERY_EXPORT=1 und Konfiguration über BIGQUERY_*

- Fallback: Wenn Abhängigkeiten fehlen oder ENV nicht gesetzt ist, laufen Aufrufe als No-Op.
- Sicherheit: Keine geheimen Keys im Code, Credentials via Service Account JSON (Pfad oder Inhalt).
"""
from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    # Lazy/optional imports
    from google.cloud import bigquery  # type: ignore
    from google.oauth2 import service_account  # type: ignore
    _BQ_AVAILABLE = True
except Exception:
    bigquery = None  # type: ignore
    service_account = None  # type: ignore
    _BQ_AVAILABLE = False


class BigQueryExporter:
    """Exporter für Google BigQuery (optional aktivierbar)."""

    def __init__(self) -> None:
        self.enabled_env = os.getenv("ENABLE_BIGQUERY_EXPORT", "0") == "1"
        self.project = os.getenv("BIGQUERY_PROJECT", "")
        self.dataset = os.getenv("BIGQUERY_DATASET", "forensics")
        self.location = os.getenv("BIGQUERY_LOCATION", "EU")
        self.table_prefix = os.getenv("BIGQUERY_TABLE_PREFIX", "bf_")
        self.credentials_json = os.getenv("BIGQUERY_CREDENTIALS_JSON", "")
        self.credentials_file = os.getenv("BIGQUERY_CREDENTIALS_FILE", "")
        self._client: Optional["bigquery.Client"] = None

    @property
    def enabled(self) -> bool:
        return self.enabled_env and _BQ_AVAILABLE and bool(self.project)

    def _get_client(self) -> "bigquery.Client":
        if self._client is not None:
            return self._client
        if not self.enabled:
            raise RuntimeError("BigQuery exporter not enabled or dependencies missing")

        creds = None
        try:
            if self.credentials_json:
                info = json.loads(self.credentials_json)
                creds = service_account.Credentials.from_service_account_info(info)
            elif self.credentials_file and os.path.exists(self.credentials_file):
                creds = service_account.Credentials.from_service_account_file(self.credentials_file)
        except Exception as e:
            logger.warning(f"Failed to load BigQuery credentials, falling back to default auth: {e}")

        if creds is not None:
            self._client = bigquery.Client(project=self.project, credentials=creds, location=self.location)
        else:
            # Falls Workload Identity / Default Credentials genutzt werden
            self._client = bigquery.Client(project=self.project, location=self.location)
        return self._client

    def _ensure_dataset(self) -> None:
        client = self._get_client()
        ds_id = f"{self.project}.{self.dataset}"
        try:
            client.get_dataset(ds_id)
        except Exception:
            logger.info(f"Creating BigQuery dataset: {ds_id}")
            dataset = bigquery.Dataset(ds_id)
            dataset.location = self.location
            client.create_dataset(dataset, exists_ok=True)

    def _ensure_table(self, table_name: str, schema: List["bigquery.SchemaField"]) -> None:
        client = self._get_client()
        self._ensure_dataset()
        table_id = f"{self.project}.{self.dataset}.{self.table_prefix}{table_name}"
        try:
            client.get_table(table_id)
        except Exception:
            logger.info(f"Creating BigQuery table: {table_id}")
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table, exists_ok=True)

    # -------------------------------
    # Public API
    # -------------------------------
    def export_transactions(self, rows: List[Dict[str, Any]], table_override: Optional[str] = None) -> Dict[str, Any]:
        """Exportiert Transaktionszeilen nach BigQuery.
        Erwartete Keys je Row: chain, tx_hash, block_number, timestamp, from_address, to_address, value, risk_score
        Zusätzliche Keys werden ignoriert.
        """
        if not self.enabled:
            logger.info("BigQuery export disabled - skipping export (noop)")
            return {"enabled": False, "inserted": 0}
        if not rows:
            return {"enabled": True, "inserted": 0}

        client = self._get_client()
        table_name = table_override or "transactions"
        schema = [
            bigquery.SchemaField("chain", "STRING"),
            bigquery.SchemaField("tx_hash", "STRING"),
            bigquery.SchemaField("block_number", "INTEGER"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("from_address", "STRING"),
            bigquery.SchemaField("to_address", "STRING"),
            bigquery.SchemaField("value", "FLOAT"),
            bigquery.SchemaField("risk_score", "FLOAT"),
        ]
        self._ensure_table(table_name, schema)
        table_id = f"{self.project}.{self.dataset}.{self.table_prefix}{table_name}"

        # Normalisieren
        def _norm(r: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "chain": str(r.get("chain", "")),
                "tx_hash": str(r.get("tx_hash", r.get("txid", ""))),
                "block_number": int(r.get("block_number") or 0),
                "timestamp": r.get("timestamp"),
                "from_address": str(r.get("from_address", r.get("from", "")) or ""),
                "to_address": str(r.get("to_address", r.get("to", "")) or ""),
                "value": float(r.get("value") or 0.0),
                "risk_score": float(r.get("risk_score") or 0.0),
            }

        json_rows = [_norm(r) for r in rows]
        errors = client.insert_rows_json(table_id, json_rows, row_ids=[None] * len(json_rows))
        if errors:
            # Versuche via load_table_from_json (Batch) als Fallback
            logger.warning(f"insert_rows_json returned errors, trying load_table_from_json: {errors}")
            job = client.load_table_from_json(json_rows, table_id)
            job.result()
            return {"enabled": True, "inserted": len(json_rows), "method": "load"}
        return {"enabled": True, "inserted": len(json_rows), "method": "insert"}

    def export_trace_graph(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exportiert Trace Graph (nodes/edges) nach BigQuery (zwei Tabellen)."""
        if not self.enabled:
            logger.info("BigQuery export disabled - skipping export (noop)")
            return {"enabled": False, "inserted_nodes": 0, "inserted_edges": 0}
        if not trace_data:
            return {"enabled": True, "inserted_nodes": 0, "inserted_edges": 0}

        client = self._get_client()
        # Nodes
        nodes_schema = [
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("labels", "STRING", mode="REPEATED"),
            bigquery.SchemaField("risk_score", "FLOAT"),
            bigquery.SchemaField("taint", "FLOAT"),
            bigquery.SchemaField("hop", "INTEGER"),
        ]
        edges_schema = [
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("target", "STRING"),
            bigquery.SchemaField("value", "FLOAT"),
            bigquery.SchemaField("tx_hash", "STRING"),
        ]
        self._ensure_table("graph_nodes", nodes_schema)
        self._ensure_table("graph_edges", edges_schema)

        nodes = trace_data.get("nodes") or trace_data.get("graph", {}).get("nodes") or []
        edges = trace_data.get("edges") or trace_data.get("graph", {}).get("edges") or []

        def _norm_node(n: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "id": str(n.get("id") or n.get("address") or n.get("node_id") or ""),
                "labels": list(n.get("labels") or []),
                "risk_score": float(n.get("risk_score") or n.get("risk", 0.0) or 0.0),
                "taint": float(n.get("taint") or n.get("taint_received") or 0.0),
                "hop": int(n.get("hop") or n.get("hop_distance") or 0),
            }

        def _norm_edge(e: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "source": str(e.get("source") or e.get("from") or e.get("from_address") or ""),
                "target": str(e.get("target") or e.get("to") or e.get("to_address") or ""),
                "value": float(e.get("value") or e.get("taint_value") or 0.0),
                "tx_hash": str(e.get("tx_hash") or e.get("txid") or ""),
            }

        node_rows = [_norm_node(n) for n in nodes]
        edge_rows = [_norm_edge(e) for e in edges]

        tbl_nodes = f"{self.project}.{self.dataset}.{self.table_prefix}graph_nodes"
        tbl_edges = f"{self.project}.{self.dataset}.{self.table_prefix}graph_edges"

        err_n = client.insert_rows_json(tbl_nodes, node_rows, row_ids=[None] * len(node_rows)) if node_rows else []
        err_e = client.insert_rows_json(tbl_edges, edge_rows, row_ids=[None] * len(edge_rows)) if edge_rows else []

        # Fallback auf Batch-Load wenn Fehler
        if err_n:
            job = client.load_table_from_json(node_rows, tbl_nodes)
            job.result()
        if err_e:
            job = client.load_table_from_json(edge_rows, tbl_edges)
            job.result()

        return {
            "enabled": True,
            "inserted_nodes": len(node_rows),
            "inserted_edges": len(edge_rows),
        }


# Singleton
bigquery_exporter = BigQueryExporter()
