"""
Tests for Feature Engineering
All tests use mocks for Neo4j and Postgres to run offline
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.ml.feature_engineering import FeatureEngineer


class MockPgConn:
    def __init__(self, rows=None, row=None):
        self._rows = rows or []
        self._row = row

    async def fetch(self, query, *args):
        return self._rows

    async def fetchrow(self, query, *args):
        return self._row


class MockAcquire:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class MockPostgresPool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return MockAcquire(self._conn)


@pytest.mark.asyncio
async def test_transaction_features_basic(monkeypatch):
    fe = FeatureEngineer()

    # Mock Postgres for transaction features
    row = {
        'tx_count': 10,
        'tx_count_24h': 4,
        'tx_count_7d': 7,
        'tx_count_30d': 10,
        'avg_tx_value': 2,
        'median_tx_value': 1.5,
        'max_tx_value': 10,
        'min_tx_value': 0.1,
        'std_tx_value': 0.5,
        'unique_receivers': 3,
        'unique_senders': 2,
    }
    pg_conn = MockPgConn(row=row)

    # Patch postgres_client on feature_engineering module directly
    import app.ml.feature_engineering as fe_mod
    fe_mod.postgres_client = MagicMock()
    fe_mod.postgres_client.pool = MockPostgresPool(pg_conn)

    tx_feats = await fe._extract_transaction_features("0xabc", "ethereum")

    assert tx_feats['tx_count_total'] == 10.0
    assert tx_feats['tx_velocity_24h'] == 4.0/24.0
    assert tx_feats['unique_counterparties'] == 5.0


@pytest.mark.asyncio
async def test_network_features_with_defaults(monkeypatch):
    fe = FeatureEngineer()

    # Mock Neo4j run_query to return empty
    import app.ml.feature_engineering as fe_mod
    fe_mod.neo4j_client = MagicMock()
    fe_mod.neo4j_client.run_query = AsyncMock(return_value=[])

    feats = await fe._extract_network_features("0xabc", "ethereum")
    assert 'pagerank' in feats
    assert feats['pagerank'] == 0.0


@pytest.mark.asyncio
async def test_temporal_features(monkeypatch):
    fe = FeatureEngineer()

    # Build synthetic rows of timestamps by hour and first/last
    now = datetime.utcnow()
    rows = []
    for i in range(10):
        ts = now - timedelta(hours=i)
        rows.append({
            'first_tx': now - timedelta(days=10),
            'last_tx': now,
            'tx_hour': ts.hour,
        })

    import app.ml.feature_engineering as fe_mod
    fe_mod.postgres_client = MagicMock()
    fe_mod.postgres_client.pool = MockPostgresPool(MockPgConn(rows=rows))

    feats = await fe._extract_temporal_features("0xabc", "ethereum")
    assert feats['account_age_days'] >= 9
    assert feats['days_since_last_tx'] <= 1
    assert 'activity_hour_entropy' in feats


@pytest.mark.asyncio
async def test_label_features(monkeypatch):
    fe = FeatureEngineer()

    # Mock labels_service
    import app.ml.feature_engineering as fe_mod
    fe_mod.labels_service = MagicMock()
    fe_mod.labels_service.get_labels = AsyncMock(return_value=["exchange", "defi"]) 

    feats = await fe._extract_label_features("0xabc", "ethereum")
    assert feats['is_exchange'] == 1.0
    assert feats['is_defi'] == 1.0


@pytest.mark.asyncio
async def test_risk_features(monkeypatch):
    fe = FeatureEngineer()

    # Mock neo4j queries
    import app.ml.feature_engineering as fe_mod
    fe_mod.neo4j_client = MagicMock()
    fe_mod.neo4j_client.run_query = AsyncMock(side_effect=[
        # _detect_cross_chain_activity
        [{"chains_count": 2}],
        # _count_bridge_transactions
        [{"bridge_count": 5}],
    ])

    # Mock postgres for amount/time anomalies
    vals_rows = [{"val": 1.0},{"val": 2.0},{"val": 3.0},{"val": 100.0},{"val": 2.0}]
    ts_now = datetime.utcnow()
    ts_rows = [
        {"ts": (ts_now - timedelta(minutes=i*10)).timestamp()} for i in range(6)
    ]

    fe_mod.postgres_client = MagicMock()
    fe_mod.postgres_client.pool = MockPostgresPool(MockPgConn(rows=vals_rows))

    # Patch fetch for time anomaly call next
    async def fetch_switch(query, *args):
        if "EXTRACT(EPOCH" in query:
            return ts_rows
        return vals_rows

    pg_conn = MockPgConn()
    pg_conn.fetch = fetch_switch
    fe_mod.postgres_client.pool = MockPostgresPool(pg_conn)

    feats = await fe._extract_risk_features("0xabc", "ethereum")
    assert 'transaction_amount_anomaly' in feats
    assert 'transaction_time_anomaly' in feats
    assert feats['cross_chain_activity'] >= 0.0
    assert feats['bridge_transaction_count'] >= 0.0
