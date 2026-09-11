import argparse
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.rag.engine import RAGEngine
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(
        description="Healthcare Agentic RAG Chatbot CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to execute")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest PDF documents")
    ingest_parser.add_argument(
        "--docs-dir",
        default="data/documents",
        help="Path to directory containing PDF files",
    )
    ingest_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector store before ingestion",
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the RAG engine")
    query_parser.add_argument("question", type=str, help="Healthcare question string")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    engine = RAGEngine()

    if args.command == "ingest":
        print("=" * 60)
        print(f"INGESTING DOCUMENTS FROM: {args.docs_dir} (clear={args.clear})")
        print("=" * 60)

        summary = engine.ingest_directory(args.docs_dir, clear_existing=args.clear)

        print("\n--- INGESTION SUMMARY ---")
        print(f"Documents Processed: {summary.documents_processed}")
        print(f"Pages Processed:     {summary.pages_processed}")
        print(f"Chunks Created:      {summary.chunks_created}")
        print(f"Chunks Stored:       {summary.chunks_stored}")

        if summary.errors:
            print("\nERRORS ENCOUNTERED:")
            for err in summary.errors:
                print(f"  - {err}")
        print("=" * 60)

    elif args.command == "query":
        print("=" * 60)
        print(f"QUESTION: {args.question}")
        print("=" * 60)

        response = engine.query(args.question)

        print("\n--- RETRIEVAL METRICS ---")
        print(f"Results Count: {response.retrieval_info.results_count}")
        print(f"Top Distance:  {response.retrieval_info.top_distance}")
        print(f"Threshold:     {response.retrieval_info.threshold}")

        print("\n--- STATUS ---")
        print(f"Grounded:  {response.grounded}")
        print(f"Abstained: {response.abstained}")

        print("\n--- RESPONSE ---")
        print(response.answer)

        if response.sources:
            print("\n--- CITATIONS ---")
            for idx, source in enumerate(response.sources, 1):
                print(
                    f"[{idx}] Document: {source.document} | Page: {source.page} | Distance: {source.distance:.4f}"
                )
        print("=" * 60)


if __name__ == "__main__":
    main()
