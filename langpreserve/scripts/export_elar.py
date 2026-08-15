"""Demo: package a recording's transcription + IGT into an ELAR-style manual
deposit bundle (ELAN .eaf + IMDI metadata + media), written to
`./export_output/`.

Usage (with the API running and sample data seeded):
    python scripts/export_elar.py <recording_id>
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.database import AsyncSessionLocal  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.linguistics import InterlinearGloss, Transcription  # noqa: E402
from app.models.recording import Recording  # noqa: E402
from app.services.elar_integration import DepositBundle, ELARClient  # noqa: E402
from app.services.export_service import (  # noqa: E402
    ExportIGTLine,
    ExportRecordingBundle,
    ExportSegment,
    generate_elan_eaf,
    generate_imdi_metadata,
)
from app.services.storage_service import get_storage_service  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "export_output"


async def main(recording_id: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Recording)
            .options(selectinload(Recording.transcriptions).selectinload(Transcription.segments))
            .where(Recording.id == UUID(recording_id))
        )
        recording = result.scalar_one_or_none()
        if not recording:
            print(f"Recording {recording_id} not found. Run scripts/seed_db.py first?")
            return

        language = await session.get(Language, recording.language_id)
        transcription = next(iter(recording.transcriptions), None)

        segments = []
        igt_lines = []
        if transcription:
            segments = [
                ExportSegment(s.start_ms, s.end_ms, s.text) for s in transcription.segments
            ]
            igt_result = await session.execute(
                select(InterlinearGloss).where(
                    InterlinearGloss.transcription_id == transcription.id
                )
            )
            igt_lines = [
                ExportIGTLine(i.surface_form, i.morpheme_breakdown, i.gloss_line, i.free_translation)
                for i in igt_result.scalars().all()
            ]

        media_filename = f"{recording.id}.{recording.file_format or 'wav'}"
        eaf_xml = generate_elan_eaf(
            ExportRecordingBundle(
                recording_title=recording.title,
                language_name=language.name if language else "unknown",
                speaker_display_name=None,
                media_filename=media_filename,
                segments=segments,
                igt_lines=igt_lines,
            )
        )
        imdi_xml = generate_imdi_metadata(
            language_name=language.name if language else "unknown",
            glottocode=language.glottocode if language else None,
            session_title=recording.title,
            speaker_name=None,
            recorded_date=recording.recorded_at_field_date,
        )

        storage = get_storage_service()
        audio_bytes = storage.get_object(recording.storage_key)

        client = ELARClient()
        package = client.package_for_manual_deposit(
            DepositBundle(
                session_title=recording.title,
                language_name=language.name if language else "unknown",
                glottocode=language.glottocode if language else None,
                media_files={media_filename: audio_bytes},
                metadata_xml=imdi_xml,
                additional_documents={f"{recording.id}.eaf": eaf_xml},
            )
        )

        OUTPUT_DIR.mkdir(exist_ok=True)
        target = OUTPUT_DIR / str(recording.id)
        target.mkdir(exist_ok=True)
        for filename, content in package.items():
            file_path = target / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)

        print(f"Wrote manual-deposit bundle to {target}")
        print("Zip that folder and upload it through your archive's deposit portal")
        print("(e.g. ELAR, PARADISEC, or your institution's repository).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/export_elar.py <recording_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
