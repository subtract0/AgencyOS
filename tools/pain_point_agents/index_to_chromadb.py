#!/usr/bin/env python3
"""
Pain Points ChromaDB Indexer
Indexiert alle angereicherten Pain Points für semantische Suche.

Beispiel-Queries nach Indexierung:
    - "Sinnlosigkeit im Job"
    - "Einsamkeit und keine Freunde"
    - "Burnout und Erschöpfung"

Mit Metadaten-Filtern:
    - topic="depression", suffering_score > 0.7
    - platform="reddit", date_range
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

# Konfiguration
DATA_FILE = Path("/Volumes/Satechi4TB/pain_points/ENRICHED_pain_points.json")
CHROMA_DIR = Path("/Volumes/Satechi4TB/pain_points/chromadb_index")
COLLECTION_NAME = "pain_points"
BATCH_SIZE = 100  # ChromaDB empfiehlt 100-500


def load_pain_points() -> list[dict[str, Any]]:
    """Lädt die angereicherten Pain Points."""
    print(f"📂 Lade Daten aus {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   → {len(data):,} Records geladen")
    return data


def extract_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Extrahiert durchsuchbare Metadaten aus einem Record."""
    metadata = {}

    # Basis-Felder
    metadata["source_platform"] = record.get("source_platform", "unknown")
    metadata["topic"] = record.get("topic", "unknown")
    metadata["source_url"] = record.get("source_url", "")[:500]  # ChromaDB limit

    # Scores
    metadata["authenticity_score"] = float(record.get("authenticity_score", 0) or 0)
    metadata["suffering_score"] = float(record.get("suffering_score", 0) or 0)

    # Suffering Indicators als String (ChromaDB mag keine Listen)
    indicators = record.get("suffering_indicators", [])
    if indicators:
        metadata["suffering_indicators"] = ", ".join(indicators[:10])  # Max 10
    else:
        metadata["suffering_indicators"] = ""

    # Zeitstempel
    created_at = record.get("created_at")
    if created_at:
        try:
            if isinstance(created_at, (int, float)):
                metadata["created_at"] = int(created_at)
                dt = datetime.fromtimestamp(created_at)
                metadata["year"] = dt.year
                metadata["month"] = dt.month
            else:
                metadata["created_at"] = 0
                metadata["year"] = 0
                metadata["month"] = 0
        except (ValueError, OSError):
            metadata["created_at"] = 0
            metadata["year"] = 0
            metadata["month"] = 0
    else:
        metadata["created_at"] = 0
        metadata["year"] = 0
        metadata["month"] = 0

    # Nested metadata
    nested = record.get("metadata", {})
    if isinstance(nested, dict):
        metadata["subreddit"] = nested.get("subreddit", "")
        metadata["upvotes"] = int(nested.get("upvotes", 0) or 0)
        metadata["num_comments"] = int(nested.get("num_comments", 0) or 0)

    return metadata


def create_document_text(record: dict[str, Any]) -> str:
    """Erstellt den zu indexierenden Text."""
    parts = []

    # Hauptinhalt
    content = record.get("content", "")
    if content:
        parts.append(content)

    # LLM-Analyse hinzufügen für bessere semantische Suche
    llm_analysis = record.get("llm_analysis")
    if llm_analysis:
        if isinstance(llm_analysis, dict):
            # Relevante Felder aus der Analyse
            for key in ["summary", "pain_point", "emotional_state", "core_issue"]:
                if key in llm_analysis and llm_analysis[key]:
                    parts.append(str(llm_analysis[key]))
        elif isinstance(llm_analysis, str):
            parts.append(llm_analysis)

    return "\n".join(parts)


def index_to_chromadb(records: list[dict[str, Any]]) -> None:
    """Indexiert alle Records in ChromaDB."""
    print(f"\n🗄️  Initialisiere ChromaDB in {CHROMA_DIR}...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # Persistenter Client
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Collection erstellen/holen (mit default embedding function)
    # ChromaDB verwendet automatisch all-MiniLM-L6-v2
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   → Alte Collection gelöscht")
    except Exception:
        pass  # Collection existierte nicht

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Pain Points für semantische Suche"}
    )
    print(f"   → Collection '{COLLECTION_NAME}' erstellt")

    # Batched Indexierung
    total = len(records)
    indexed = 0
    skipped = 0

    print(f"\n📊 Indexiere {total:,} Records (Batch-Größe: {BATCH_SIZE})...\n")

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = records[batch_start:batch_end]

        ids = []
        documents = []
        metadatas = []

        for i, record in enumerate(batch):
            record_id = f"pp_{batch_start + i}"

            # Dokument-Text erstellen
            doc_text = create_document_text(record)
            if not doc_text or len(doc_text.strip()) < 10:
                skipped += 1
                continue

            # Metadaten extrahieren
            try:
                meta = extract_metadata(record)
            except Exception as e:
                print(f"   ⚠️  Metadaten-Fehler bei {record_id}: {e}")
                skipped += 1
                continue

            ids.append(record_id)
            documents.append(doc_text[:10000])  # Max 10k chars pro Doc
            metadatas.append(meta)

        if ids:
            try:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                indexed += len(ids)
            except Exception as e:
                print(f"   ❌ Batch-Fehler: {e}")
                skipped += len(ids)

        # Progress
        pct = (batch_end / total) * 100
        print(f"   [{pct:5.1f}%] {indexed:,} indexiert, {skipped:,} übersprungen", end="\r")

    print(f"\n\n✅ Indexierung abgeschlossen!")
    print(f"   → Indexiert: {indexed:,}")
    print(f"   → Übersprungen: {skipped:,}")
    print(f"   → Index-Pfad: {CHROMA_DIR}")

    # Verifizierung
    count = collection.count()
    print(f"\n🔍 Verifizierung: {count:,} Dokumente in der Collection")


def test_queries(client: chromadb.PersistentClient) -> None:
    """Testet einige Beispiel-Queries."""
    print("\n" + "="*60)
    print("🧪 Test-Queries")
    print("="*60)

    collection = client.get_collection(COLLECTION_NAME)

    test_cases = [
        ("Sinnlosigkeit im Job, keine Motivation mehr", None),
        ("Einsamkeit, keine Freunde, soziale Isolation", None),
        ("Burnout, Erschöpfung, kann nicht mehr", None),
        ("Beziehungsprobleme, Partner versteht mich nicht", {"topic": "relationships"}),
    ]

    for query, where_filter in test_cases:
        print(f"\n📝 Query: \"{query}\"")
        if where_filter:
            print(f"   Filter: {where_filter}")

        results = collection.query(
            query_texts=[query],
            n_results=3,
            where=where_filter
        )

        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            print(f"\n   [{i+1}] Score: {1-dist:.3f}")
            print(f"       Topic: {meta.get('topic')}, Platform: {meta.get('source_platform')}")
            print(f"       Suffering: {meta.get('suffering_score'):.2f}")
            preview = doc[:150].replace("\n", " ")
            print(f"       Preview: {preview}...")


def main():
    """Hauptprogramm."""
    print("="*60)
    print("🎯 Pain Points ChromaDB Indexer")
    print("="*60)

    # Prüfen ob Datei existiert
    if not DATA_FILE.exists():
        print(f"❌ Datei nicht gefunden: {DATA_FILE}")
        sys.exit(1)

    # Daten laden
    records = load_pain_points()

    if not records:
        print("❌ Keine Records zum Indexieren")
        sys.exit(1)

    # Indexieren
    index_to_chromadb(records)

    # Test-Queries
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    test_queries(client)

    print("\n" + "="*60)
    print("✅ FERTIG - Index bereit für Queries!")
    print("="*60)
    print(f"\nNutzung:")
    print(f"  from chromadb import PersistentClient")
    print(f"  client = PersistentClient(path='{CHROMA_DIR}')")
    print(f"  collection = client.get_collection('{COLLECTION_NAME}')")
    print(f"  results = collection.query(query_texts=['Sinnlosigkeit im Job'], n_results=10)")


if __name__ == "__main__":
    main()
