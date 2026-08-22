import os
import sys

from qdrant_client import QdrantClient


def main() -> int:
    url = os.getenv("QDRANT_URL", "http://localhost:6333")

    try:
        client = QdrantClient(url=url, timeout=5)
        version = client.info().version
        collections = client.get_collections().collections
    except Exception as exc:
        print(f"Qdrant connection failed: {exc}", file=sys.stderr)
        return 1

    print("Qdrant connected")
    print(f"server version: {version}")
    print(f"collections: {len(collections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
