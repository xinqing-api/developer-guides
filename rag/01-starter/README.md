# Episode 01 starter

```bash
docker compose up -d
python -m venv .venv
python -m pip install -r requirements.txt
python healthcheck.py
```

Qdrant Dashboard: <http://localhost:6333/dashboard>

> This setup is for local development. Do not expose the default unauthenticated service to the public internet.
