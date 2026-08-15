"""Seed the database with realistic sample data for local development/demo.

Usage:
    docker compose exec backend python scripts/seed_db.py
    # or locally, with DATABASE_URL pointed at a running Postgres instance:
    python scripts/seed_db.py

This script is intentionally written against the same SQLAlchemy models the
application uses (rather than raw SQL), so seeded data always matches the
current schema. It is idempotent-ish: re-running against an already-seeded
database will raise on the unique language/user constraints rather than
silently duplicating data — drop the volume (`docker compose down -v`) for a
clean re-seed.
"""
import asyncio
import io
import json
import struct
import sys
import wave
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import AsyncSessionLocal, Base, engine  # noqa: E402
from app.models.language import Language, Orthography, PhonemeInventoryEntry  # noqa: E402
from app.models.linguistics import (  # noqa: E402
    Annotation,
    InterlinearGloss,
    Transcription,
    TranscriptionSegment,
)
from app.models.recording import Recording, Speaker  # noqa: E402
from app.models.user import Community, User, UserRole  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402
from app.services.storage_service import get_storage_service  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_data"


def _make_placeholder_wav(duration_seconds: float, sample_rate: int = 16000) -> bytes:
    """Generate a short silent WAV so upload/export flows have real bytes to work with."""
    capped_duration = min(duration_seconds, 3.0)  # keep seed data small
    n_frames = int(sample_rate * capped_duration)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack("<%dh" % n_frames, *([0] * n_frames)))
    return buffer.getvalue()


async def seed() -> None:
    print("Creating schema (if not present)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    languages_payload = json.loads((DATA_DIR / "sample_languages.json").read_text())
    speakers_payload = json.loads((DATA_DIR / "sample_speakers.json").read_text())
    recordings_payload = json.loads((DATA_DIR / "sample_recordings.json").read_text())
    transcriptions_payload = json.loads((DATA_DIR / "sample_transcriptions.json").read_text())
    igt_payload = json.loads((DATA_DIR / "sample_igt.json").read_text())
    phonemes_payload = json.loads((DATA_DIR / "sample_phonemes.json").read_text())
    annotations_payload = json.loads((DATA_DIR / "sample_annotations.json").read_text())

    storage = get_storage_service()

    async with AsyncSessionLocal() as session:
        print("Seeding demo user...")
        demo_user = User(
            email="linguist@example.org",
            full_name="Demo Field Linguist",
            hashed_password=hash_password("ChangeMe123!"),
            role=UserRole.LINGUIST,
            is_active=True,
        )
        session.add(demo_user)
        await session.flush()

        print("Seeding communities...")
        for community in languages_payload["communities"]:
            session.add(Community(
                id=UUID(community["id"]),
                name=community["name"],
                region=community["region"],
                country=community["country"],
                contact_notes=community["contact_notes"],
                data_sovereignty_agreement=community["data_sovereignty_agreement"],
            ))
        await session.flush()

        print("Seeding languages...")
        for lang in languages_payload["languages"]:
            session.add(Language(
                id=UUID(lang["id"]),
                name=lang["name"],
                glottocode=lang["glottocode"],
                iso_639_3=lang["iso_639_3"],
                endangerment_status=lang["endangerment_status"],
                estimated_speakers=lang["estimated_speakers"],
                region=lang["region"],
                notes=lang["notes"],
                community_id=UUID(lang["community_id"]),
            ))
        await session.flush()

        print("Seeding orthographies...")
        for orth in languages_payload["orthographies"]:
            session.add(Orthography(
                language_id=UUID(orth["language_id"]),
                name=orth["name"],
                kind=orth["kind"],
                is_default=orth["is_default"],
                description=orth["description"],
            ))

        print("Seeding speakers...")
        for sp in speakers_payload:
            session.add(Speaker(
                id=UUID(sp["id"]),
                display_name=sp["display_name"],
                community_id=UUID(sp["community_id"]),
                birth_decade=sp["birth_decade"],
                dialect_notes=sp["dialect_notes"],
                consent_status=sp["consent_status"],
            ))
        await session.flush()

        print("Seeding recordings (with placeholder audio upload)...")
        for rec in recordings_payload:
            audio_bytes = _make_placeholder_wav(rec["duration_seconds"])
            key = storage.build_key(
                language_id=rec["language_id"], kind="recordings", extension="wav"
            )
            storage.put_object(key, audio_bytes, content_type="audio/wav")

            session.add(Recording(
                id=UUID(rec["id"]),
                language_id=UUID(rec["language_id"]),
                speaker_id=UUID(rec["speaker_id"]),
                recorded_by_user_id=demo_user.id,
                title=rec["title"],
                genre=rec["genre"],
                location_description=rec["location_description"],
                recorded_at_field_date=rec["recorded_at_field_date"],
                duration_seconds=rec["duration_seconds"],
                storage_key=key,
                sample_rate_hz=rec["sample_rate_hz"],
                file_format=rec["file_format"],
                field_notes=rec["field_notes"],
                captured_offline=rec["captured_offline"],
                consent_status=rec["consent_status"],
                status="draft_ready",
            ))
        await session.flush()

        print("Seeding transcriptions and segments...")
        transcription_id_by_recording: dict[str, UUID] = {}
        for tr in transcriptions_payload:
            transcription = Transcription(
                recording_id=UUID(tr["recording_id"]),
                text=tr["text"],
                source=tr["source"],
                asr_model_version=tr["asr_model_version"],
                confidence=tr["confidence"],
                is_final=tr["is_final"],
            )
            session.add(transcription)
            await session.flush()
            transcription_id_by_recording[tr["recording_id"]] = transcription.id

            for seg in tr["segments"]:
                session.add(TranscriptionSegment(
                    transcription_id=transcription.id,
                    start_ms=seg["start_ms"],
                    end_ms=seg["end_ms"],
                    text=seg["text"],
                    confidence=seg["confidence"],
                ))

        print("Seeding interlinear glosses...")
        for igt in igt_payload:
            transcription_id = transcription_id_by_recording.get(igt["recording_id"])
            if not transcription_id:
                continue
            session.add(InterlinearGloss(
                transcription_id=transcription_id,
                line_number=igt["line_number"],
                surface_form=igt["surface_form"],
                morpheme_breakdown=igt["morpheme_breakdown"],
                gloss_line=igt["gloss_line"],
                free_translation=igt["free_translation"],
                pos_tags=igt["pos_tags"],
                generated_automatically=igt["generated_automatically"],
            ))

        print("Seeding phoneme inventory...")
        for ph in phonemes_payload:
            session.add(PhonemeInventoryEntry(
                language_id=UUID(ph["language_id"]),
                ipa_symbol=ph["ipa_symbol"],
                phoneme_type=ph["phoneme_type"],
                manner=ph["manner"],
                place=ph["place"],
                voicing=ph["voicing"],
                example_word=ph["example_word"],
                community_spelling=ph["community_spelling"],
                frequency_rank=ph["frequency_rank"],
                detected_automatically=ph["detected_automatically"],
            ))

        print("Seeding community annotations...")
        for ann in annotations_payload:
            transcription_id = transcription_id_by_recording.get(ann["recording_id"])
            if not transcription_id:
                continue
            session.add(Annotation(
                transcription_id=transcription_id,
                author_user_id=demo_user.id,
                annotation_type=ann["annotation_type"],
                body=ann["body"],
                upvotes=ann["upvotes"],
                resolved=ann["resolved"],
            ))

        await session.commit()

    print("\nSeed complete.")
    print("Demo login -> email: linguist@example.org  password: ChangeMe123!")
    print("(Change or remove this account before any real deployment.)")


if __name__ == "__main__":
    asyncio.run(seed())
