import os
import asyncio
from typing import List, Dict, Optional, Set
from app.db.postgres import postgres_client
from app.kb.embeddings import openai_embedding, to_pgvector_literal

# Erweiterte Dateitypen für KB-Indexierung
TEXT_EXTS = {'.md', '.txt', '.mdx', '.py', '.js', '.ts', '.tsx', '.json'}
DOC_EXTS = {'.pdf', '.docx'}  # Für zukünftige Erweiterung

async def reindex_kb_multiple(root_paths: List[str]) -> Dict[str, int]:
    """
    Erweiterte KB-Reindexierung für mehrere Quellen.
    Unterstützt Docs, Blog, API, Support und andere Firmendaten.
    """
    if not getattr(postgres_client, "pool", None):
        return {"inserted": 0, "sources": {}}

    all_files: List[str] = []
    source_counts = {}

    for root_path in root_paths:
        if not os.path.exists(root_path):
            continue
        source_name = os.path.basename(root_path)
        source_counts[source_name] = 0
        for dirpath, _, filenames in os.walk(root_path):
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in TEXT_EXTS:
                    all_files.append((os.path.join(dirpath, fn), source_name))
                    source_counts[source_name] += 1

    inserted = 0
    async with postgres_client.acquire() as conn:
        # Vollständiges Rebuild
        await conn.execute("DELETE FROM kb_docs")
        try:
            await conn.execute("DELETE FROM kb_embeddings")
        except Exception:
            pass

        for fp, source in all_files:
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                title = os.path.basename(fp)
                rel = os.path.relpath(fp, root_paths[0])  # Relativer Pfad zur ersten Quelle

                # Erweitere Metadaten
                metadata = {
                    "source": source,
                    "file_type": os.path.splitext(fp)[1],
                    "size": len(content),
                    "last_modified": os.path.getmtime(fp)
                }

                # Insert mit Metadaten
                row = await conn.fetchrow(
                    """
                    INSERT INTO kb_docs (path, title, content, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)
                    RETURNING id
                    """,
                    rel, title, content, metadata
                )
                doc_id = row['id'] if row else None

                # Embedding für semantische Suche
                if doc_id:
                    vec = await openai_embedding((title + "\n" + content)[:6000])
                    if vec:
                        try:
                            vec_lit = to_pgvector_literal(vec)
                            await conn.execute(
                                """
                                INSERT INTO kb_embeddings (doc_id, embedding)
                                VALUES ($1, $2)
                                """,
                                doc_id, vec_lit
                            )
                        except Exception:
                            pass
                inserted += 1
            except Exception:
                continue

    return {"inserted": inserted, "sources": source_counts}


async def reindex_kb(root_path: str) -> Dict[str, int]:
    """Abwärtskompatible Variante: akzeptiert einen Root-Pfad.
    Ruft reindex_kb_multiple([root_path]) auf.
    """
    return await reindex_kb_multiple([root_path])


from app.services.cache_service import cache_kb_search, get_cached_kb_search
import hashlib

async def search_kb(query: str, limit: int = 5, sources: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Erweiterte Suche mit optionalen Source-Filtern und besserer Snippeting.
    """
    if not getattr(postgres_client, "pool", None):
        return []

    # Generate cache key
    sources_str = ",".join(sources or [])
    query_hash = hashlib.sha256(f"{query}:{limit}:{sources_str}".encode()).hexdigest()[:16]

    # Check cache first
    cached_results = await get_cached_kb_search(query_hash)
    if cached_results:
        return cached_results

    q = f"%{query[:256]}%"
    where_clause = "WHERE (title ILIKE $1 OR content ILIKE $1)"
    params = [q, limit]

    if sources:
        placeholders = ','.join(f'${len(params) + 1 + i}' for i in range(len(sources)))
        where_clause += f" AND metadata->>'source' IN ({placeholders})"
        params.extend(sources)

    async with postgres_client.acquire() as conn:
        sql = f"""
            SELECT path, title, metadata->>'source' as source,
                   substr(content, greatest(1, position(lower($1) in lower(content)) - 100), 500) AS snippet
            FROM kb_docs
            {where_clause}
            ORDER BY
                CASE WHEN title ILIKE $1 THEN 1 ELSE 2 END,
                length(snippet) DESC
            LIMIT ${len(params)}
        """
        rows = await conn.fetch(sql, *params)

    results = [
        {
            "path": r["path"],
            "title": r["title"],
            "snippet": r["snippet"] or "",
            "source": r["source"]
        } for r in rows
    ]

    # Cache the results
    await cache_kb_search(query_hash, results)
    return results


async def semantic_search_kb(query: str, limit: int = 5, sources: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Semantische Suche mit pgvector, erweitert um Source-Filter und Caching.
    """
    if not getattr(postgres_client, "pool", None):
        return []

    # Generate cache key
    sources_str = ",".join(sources or [])
    query_hash = hashlib.sha256(f"semantic:{query}:{limit}:{sources_str}".encode()).hexdigest()[:16]

    # Check cache first
    cached_results = await get_cached_kb_search(query_hash)
    if cached_results:
        return cached_results

    vec = await openai_embedding(query)
    if not vec:
        return await search_kb(query, limit, sources)

    vec_lit = to_pgvector_literal(vec)
    where_clause = ""
    params = [limit]

    if sources:
        placeholders = ','.join(f'${len(params) + 1 + i}' for i in range(len(sources)))
        where_clause = f" AND d.metadata->>'source' IN ({placeholders})"
        params.extend(sources)

    async with postgres_client.acquire() as conn:
        try:
            sql = f"""
                SELECT d.path, d.title, d.metadata->>'source' as source,
                       substr(d.content, 1, 400) AS snippet
                FROM kb_embeddings e
                JOIN kb_docs d ON d.id = e.doc_id
                {where_clause}
                ORDER BY e.embedding <=> $1
                LIMIT ${len(params)}
            """
            rows = await conn.fetch(sql, vec_lit, *params)
            results = [
                {
                    "path": r["path"],
                    "title": r["title"],
                    "snippet": r["snippet"] or "",
                    "source": r["source"]
                } for r in rows
            ]
        except Exception:
            results = await search_kb(query, limit, sources)

    # Cache the results
    await cache_kb_search(query_hash, results)
    return results
