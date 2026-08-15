# Deployment guide

This is a reference implementation sized for a small documentation team
self-hosting their own instance (one Postgres database, one object storage
bucket, one backend, one web dashboard) — not a multi-tenant SaaS.

## Local development

```bash
cp .env.example .env
docker compose up -d
docker compose exec backend python scripts/seed_db.py
cd frontend && npm install && npm run dev
```

## Production deployment (single-server reference)

1. **Provision infrastructure**
   - A small VM or managed container host (2 vCPU / 4GB RAM is plenty for a
     single documentation team's traffic).
   - Managed PostgreSQL (or self-hosted with regular backups — recordings
     and their transcriptions are irreplaceable field data; back up early
     and often).
   - S3-compatible object storage for media — either a cloud provider bucket
     or self-hosted MinIO with backups.

2. **Configure environment**
   - Copy `.env.example` to `.env` and set real secrets: `SECRET_KEY`,
     database credentials, object storage credentials.
   - Set `ENVIRONMENT=production` — this tightens CORS to an explicit
     allow-list you should also configure in `backend/app/main.py`.
   - Point `ASR_PROVIDER` at `custom_endpoint` with your fine-tuned model's
     endpoint (see `docs/ARCHITECTURE.md#asr-pipeline`) rather than leaving
     the default `mock` provider running in production.

3. **Run migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```
   (For a brand-new database, `scripts/seed_db.py` will also create the
   schema via `Base.metadata.create_all` if you'd rather skip Alembic for a
   very small deployment — but a real production deployment should manage
   schema changes through migrations.)

4. **Build and run**
   ```bash
   docker compose -f docker-compose.yml up -d --build
   cd frontend && npm run build   # serve the static dist/ behind your web server / CDN
   ```

5. **TLS and reverse proxy** — put the backend behind a reverse proxy
   (nginx, Caddy, or your cloud provider's load balancer) terminating TLS.
   The FastAPI app itself does not handle TLS.

6. **Backups** — schedule regular backups of both the Postgres database and
   the object storage bucket. For a documentation project, the media files
   in object storage are often the only surviving recording of a speaker or
   speech variety — treat backup failures as high-severity incidents.

## Mobile app distribution

The field app (`mobile/`) is an Expo project. For field teams:
- **Expo Go** (scan a QR code) is fine for testing and small pilot teams.
- For a durable field deployment, build a standalone binary with EAS Build
  (`eas build --platform android`) and distribute via APK/TestFlight so the
  app works fully offline without an Expo Go dependency in areas with no
  connectivity at all, including for the initial app install.

## Scaling notes

This reference implementation is intentionally simple (a single FastAPI
process, no task queue) because the target user is a small team, not a
platform. If your documentation project grows to many simultaneous field
teams:
- Move `ArchiveExportJob` processing and ASR transcription to a background
  worker (Celery/RQ/arq) instead of running them inline in the request/response
  cycle, especially once you swap in a real (slower) ASR model.
- Add a CDN in front of object storage for served audio.
- Consider read replicas for PostgreSQL if the annotation queue grows large
  across many communities.
