"""Integration adapter for depositing packaged materials with ELAR
(Endangered Languages Archive) or compatible IMDI/CMDI-based archives.

ELAR does not currently offer a fully open public deposit API for
third-party tools, so this adapter is written against a generic
"archive deposit" contract (bundle upload + session metadata) that mirrors
how CMDI-based repositories (ELAR, PARADISEC, TLA) typically ingest
material. Point `ELAR_API_BASE_URL` at a real archive endpoint, or use the
`package_for_manual_deposit` path to produce a folder structure that can be
uploaded by hand through the archive's own web portal — this is, in
practice, still the most common deposit workflow for small projects.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class DepositBundle:
    session_title: str
    language_name: str
    glottocode: str | None
    media_files: dict[str, bytes]  # filename -> bytes
    metadata_xml: str
    additional_documents: dict[str, str] = field(default_factory=dict)  # filename -> text


class ELARIntegrationError(RuntimeError):
    pass


class ELARClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or settings.elar_api_base_url
        self.api_key = api_key or settings.elar_api_key

    def package_for_manual_deposit(self, bundle: DepositBundle) -> dict[str, bytes]:
        """Build an in-memory folder (filename -> bytes) suitable for zipping
        and uploading by hand through the archive's deposit portal.

        This is the recommended path for most small documentation teams,
        since it doesn't depend on any particular archive exposing a
        machine API.
        """
        manifest = {
            "session_title": bundle.session_title,
            "language_name": bundle.language_name,
            "glottocode": bundle.glottocode,
            "media_files": list(bundle.media_files.keys()),
            "generated_by": "Kaimira Language Documentation Platform",
        }
        package: dict[str, bytes] = {
            "manifest.json": json.dumps(manifest, indent=2).encode("utf-8"),
            "metadata.imdi.xml": bundle.metadata_xml.encode("utf-8"),
        }
        for filename, content in bundle.media_files.items():
            package[f"media/{filename}"] = content
        for filename, text in bundle.additional_documents.items():
            package[f"documents/{filename}"] = text.encode("utf-8")
        return package

    async def submit_deposit(self, bundle: DepositBundle) -> dict:
        """Submit directly to a configured archive API, if available.

        Raises ELARIntegrationError if no API key/endpoint is configured —
        callers should fall back to `package_for_manual_deposit` in that
        case (this is the default in `routers/export.py`).
        """
        if not self.api_key:
            raise ELARIntegrationError(
                "No ELAR_API_KEY configured; use package_for_manual_deposit() "
                "to produce a manual-upload bundle instead."
            )

        package = self.package_for_manual_deposit(bundle)
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.base_url}/deposits",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "collection_id": settings.elar_default_collection_id,
                    "manifest": json.loads(package["manifest.json"]),
                },
            )
            response.raise_for_status()
            return response.json()
