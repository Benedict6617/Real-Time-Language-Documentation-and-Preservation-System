This directory is managed by Alembic. The initial schema is created directly
by `scripts/seed_db.py` (via `Base.metadata.create_all`) for quick local
setup; for production deployments, generate and apply a proper migration
instead:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
